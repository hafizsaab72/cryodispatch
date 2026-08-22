# Architecture

The README says what CryoDispatch is and how to run it. This document says how it is wired, which
rules are load-bearing, and why the boring choices were made.

## Data flow

```
  ESP32 / DHT22            apps/sim (Python)
  docs/firmware/  ──HTTP POST /ingest──▶  ┌──────────────────────────────┐
                                          │  Plant  (single process)     │
  optional MQTT publish ◀─── telemetry ───│  • lumped thermal model      │
  cryo/{site}/…/telemetry                 │  • fault taxonomy            │
                                          │  • greedy dispatcher         │
                                          │  • custody + audit log       │
                                          └──────────────┬───────────────┘
                                             GET /api/events (SSE)
                                    ┌────────────────────┴────────────────────┐
                                    ▼                                         ▼
                        apps/web  (Vite + React)                 apps/staff (Expo, polling)
                        floor map · gauge · alert rail            inbox → accept → QR scan
                        custody PDF (jsPDF, in browser)           POST /accept, POST /scan
```

Every box above is one process on one laptop plus one phone on the same LAN. There is no broker
and no cloud dependency on the **summit default** path. Supabase is an optional internet fan-out
that stores what the plant already decided; it is not a second brain.

## Where the rules live

**All decision logic is in the plant.** The browser and the phone are subscribers and actors; they
render state and post intents (`accept`, `scan`, `anomaly`, `reset`, `ack`). Nothing decides a
fault class, a destination or a disposition client-side. That is what makes the same brain
substitutable behind an ESP32, and it is how real SCADA is wired.

| Concern | File |
| --- | --- |
| Physics: `T_eq`, `t*`, MKT, efficacy, risk | `apps/sim/src/sim/thermal.py` |
| Asset registry: IDs, bands, capacities, staff, inventory | `apps/sim/src/sim/hospital.py` |
| Routing: distance, band compatibility, certification, kWh, cascade risk | `apps/sim/src/sim/dispatch.py` |
| State machine: stepping, alerts, missions, custody, audit, reset | `apps/sim/src/sim/plant.py` |
| HTTP surface and SSE fan-out | `apps/sim/src/sim/server.py` |
| Optional PostgREST publisher + intent drain | `apps/sim/src/sim/cloud.py` |
| Wire types shared with the web app | `packages/shared/src/index.ts` |

## HTTP surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | liveness + site id |
| `GET` | `/api/state` | full snapshot (assets, alerts, missions, tickets, inventory, staff, audit) |
| `GET` | `/api/events` | Server-Sent Events; first frame is a `hello` carrying the snapshot |
| `GET` | `/api/protocol` | the MQTT topic contract, rendered in the UI |
| `GET` | `/api/custody/{mission_id}` | the nine-field custody record the PDF is built from |
| `POST` | `/ingest`, `/api/ingest` | external telemetry (ESP32 or MQTT bridge). 404 unknown asset; 422 for missing `asset_id`, non-finite temperature, or `compressor_health` outside [0, 1] |
| `POST` | `/api/anomaly` | `{asset_id, kind}` where kind is `compressor` \| `door` \| `lwt` \| `reset` |
| `POST` | `/api/reset` | return the whole plant to its opening state |
| `POST` | `/api/missions/{id}/accept` | staff accepts a proposed MOVE |
| `POST` | `/api/missions/{id}/scan` | `{code}` — `UNIT:…` then `VAULT:…` (source) then `VAULT:…` (destination) |
| `POST` | `/api/alerts/{id}/ack` | acknowledge |

## Invariants

These are the properties the demo depends on. Breaking one is a stage failure, not a bug.

1. **A dead probe never moves stock.** `PROBE_DEAD` opens an instrumentation ticket and nothing
   else. Only `BOTH` — probe offline *and* the last reading already outside the band — dispatches.
2. **Prediction fires before the breach.** The alert on a degrading compressor is raised from
   `T_eq` crossing the threshold, not from the measured air crossing it. The gauge shows the
   countdown next to an explicit "AIR STILL IN BAND" chip.
3. **Capacity is derived, never accumulated.** `_recompute_capacity()` rebuilds `used_l` from the
   inventory and `reserved_l` from open missions on every change, so no drift is possible across
   repeated demo runs.
4. **A destination is reserved at proposal time,** which is what forces the second failure to
   cascade instead of double-booking the same backup.
5. **Certification is a hard requirement.** No certified courier free means no MOVE is created
   (ticket + escalation alert instead). There is no cross-certification fallback.
6. **The custody product list is a snapshot at dispatch,** not a live reference to inventory, so a
   certificate describes what was moved rather than where it ended up.
7. **MKT never gates a release** and is only computed for `insulin_ilr`.
8. **Reset is total.** Stock returns to `home_asset_id`, staff are freed, reservations released,
   open missions cancelled, alerts and tickets cleared.

## Physics, honestly

`t_eq(T_set, door, health) = T_set + 6.5·door + 4.0·(1 − health) + 0.04·(T_amb − T_set)`, and the
cabinet relaxes toward it as `T ← T_eq + (T − T_eq)·e^(−Δt/τ)`.

τ in the demo is **2 minutes for every cabinet**, set by `DEMO_TAU_MIN`. A loaded blood
refrigerator is nearer 12 minutes and a walk-in room nearer 18, so the demo is time-compressed by
roughly 6×. The model is unchanged — only the clock is. Say this out loud on stage; the gauge
prints "τ compressed to 2 min for the demo" for the same reason.

Worked example (`FREEZER_BLOOD_04`, band 2–6 °C, setpoint 4 °C). A compressor derate to
`health = 0.25` gives `T_eq = 4 + 4.0·0.75 + 0.04·20 = 7.8 °C`. With the air at 4.2 °C,
`t* = −2·ln((6 − 7.8)/(4.2 − 7.8)) ≈ 1.4 min` — a countdown while the reading is still legal.

## Routing, honestly

`pick_backup` is a greedy scan over candidate vaults with a linear cost:

```
cost = 3·distance_m + 2·staff_eta + (1 − free_fraction) + 2·kwh_move + 4·cascade_risk
```

Candidates must be thermal, band-compatible (blood may overflow into a 2–8 °C walk-in; the 2–6 °C
product band still governs) and have `free_l ≥ need_l`. `cascade_risk` compares the headroom left
after this move against the largest single peer vault sharing the pool: `1.0` if the destination
could no longer absorb that peer, `0.5` if it barely could, `0.1` otherwise. There is no per-asset
tuning constant — the cascade in the demo is a real capacity outcome.

In the scripted run, `FREEZER_BLOOD_03` holds 17.8 L of baseline stock in a 19.6 L cabinet. It
absorbs the first move (4 bags, 1.4 L) and is then left with 0.4 L free, which is less than the
0.7 L the second failure needs — so the router is *forced* to `FREEZER_BLOOD_06` (ICU satellite 2).

## Why HTTP is the live path

MQTT is the honest transport for devices and it is fully specified in
[mqtt-schema.md](mqtt-schema.md), but a broker is a single point of failure standing between the
demo and a conference Wi-Fi network. The plant therefore ingests over HTTP and fans out over SSE
on the LAN, and the simulator publishes MQTT `telemetry` only as an optional side effect when
`MQTT_HOST` is set. Dashboards subscribe to the plant, never to the broker — which is also how a
real deployment separates the device bus from the operations plane.

## How the Supabase path relates

Dedicated project `cefhoczywrycsbniywus` (`ap-south-1`). Do not link this repo to Lensora
(`eqexoblnsbewvfunqxky`) or onthetab.

```
  plant  --service role, after lock drops-->  Postgres (full lists + custody_documents)
  web/staff --anon SELECT + Realtime-->  same tables
  web/staff --anon-->  Edge Function intent --> plant_intents
  plant tick: drain pending intents → step() → publish
```

Rules:

- All decisions stay in `apps/sim`. The intent function only inserts rows.
- `functions/ingest` returns **410**. ESP32 stays on plant `POST /ingest`.
- Cloud sync writes **full** in-memory lists, not the truncated `snapshot()` (40/20/20/40).
- Reset is **delete-then-insert** for alerts/missions/tickets/custody so the next judge does not
  see ghost MOVEs. `tick` is not zeroed.
- Network I/O never runs inside `Plant._lock`. Telemetry appends sparsely (~15 s or on anomaly).
- Anon is SELECT only. Service role writes. Never put the service role in `VITE_*` / `EXPO_PUBLIC_*`.
- Clients use this path only when `VITE_SUPABASE_*` / `EXPO_PUBLIC_SUPABASE_*` are set. Unset →
  today’s SSE / `EXPO_PUBLIC_PLANT_URL` LAN path (the summit default).
- Do not restart the plant mid-judge: `_active_alerts` is process memory and a restart can
  re-raise the same alerts.

Venue Wi-Fi must not be able to kill the demo. Rehearse Accept/scan lag: LAN already waits up to
one tick; Supabase adds intent-poll lag — pause after Compressor fail before handing the phone.

## Hardware drop-in

`docs/firmware/cryodispatch_esp32.ino` posts the same JSON to the plant `/ingest` on `:8787`.
Do not point it at `functions/v1/ingest` (410). On a failed DHT22 read it sends
`temperature: null` and `probe_online: false` rather than inventing a plausible number —
which is precisely the input that must produce a ticket instead of an evacuation.
