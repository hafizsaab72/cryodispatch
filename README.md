# CryoDispatch

**Predict. Dispatch. Prove.** A hospital cold-chain *plant* for ELCIA Tech Summit 2026.

CryoDispatch simulates 24 cold-storage assets across a three-floor hospital — blood refrigerators
(2–6 °C), vaccine and insulin ILRs (2–8 °C), a platelet agitator (22 ± 2 °C), plasma freezers
(≤ −30 °C) and four location-only crash carts — and runs a **closed loop** over them:

> sense telemetry → classify the fault → predict time-to-breach → dispatch the right stock to the
> right backup vault with the right certified nurse → verify chain of custody by QR scan → open a
> compressor maintenance ticket.

## Why this is not a temperature dashboard

**1. It predicts instead of reacting.** A first-order lumped thermal model,
`τ·dT/dt + T = T_eq` with `T_eq = T_set + α_door·door + α_h·(1 − compressor_health)`, yields the
time to threshold `t* = −τ·ln((T_th − T_eq)/(T − T_eq))`. When a compressor degrades, the
*equilibrium* temperature jumps above the band and a countdown starts **while the measured air is
still legal**. Deliberately not ARIMA, deliberately not `if (temp > 8)`.

**2. A dead probe is not a hot vault.** The fault taxonomy separates the instrument from the
process: `PROBE_DEAD` (sensor death — maintenance ticket only, stock stays put),
`THERMAL_EXCURSION` (spoilage clock and dispatch), `BOTH` (blind *and* out of band — evacuate and
re-instrument). Generic IoT treats "no data" as "hot"; this treats it as instrumentation.

**3. It produces evidence.** A greedy router picks the backup by distance, free capacity and
cascade risk, reserves litres so a second failure cascades elsewhere, and weighs the energy of
holding a degraded compressor for 30 minutes (0.468 kWh) against moving the stock (0.220 kWh).
Every completed move produces a nine-field "Chain of Cold Custody" PDF.

## Repository map

| Path | What it is |
| --- | --- |
| `apps/sim` | Python plant: 24-asset simulator, thermal model, dispatcher, FastAPI + SSE on `:8787`. **This is the live demo path.** |
| `apps/web` | Command centre (Vite + React): floor map, gauge, alert rail, custody PDF. |
| `apps/staff` | Staff app (Expo SDK 56, three screens): inbox → accept MOVE → QR scan. |
| `packages/shared` | TypeScript types shared by web and the plant's JSON contract. |
| `supabase/` | Dedicated project (`cefhoczywrycsbniywus`, `ap-south-1`): Postgres fan-out of plant state plus an `intent` Edge Function. Clients stay on LAN unless `VITE_SUPABASE_*` / `EXPO_PUBLIC_SUPABASE_*` are set. `functions/ingest` is 410 — see [Honest limitations](#honest-limitations). |
| `docs/` | [How to run](docs/how-to-run.md) ([browser](docs/how-to-run.html)), [architecture](docs/architecture.md), [demo script](docs/demo-script.md), [MQTT contract](docs/mqtt-schema.md), [ESP32 sketch](docs/firmware/cryodispatch_esp32.ino), [printable QR cards](docs/qr-stickers.html), [pitch deck](docs/pitch/). |

## Run it

Illustrated walkthrough: [docs/how-to-run.md](docs/how-to-run.md) · [open in a browser](docs/how-to-run.html) · [live on GitHub Pages](https://hafizsaab72.github.io/cryodispatch/).

Requires Python ≥ 3.12 (the checked-out venv is 3.14), Node 20+, and pnpm 10.

### 1. The plant (start this first)

```bash
cd apps/sim
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m sim          # plant + dashboard API on http://0.0.0.0:8787
```

`.venv/bin/python -m sim --no-server` runs the terminal table only. `--tau` and `--tick` override
`DEMO_TAU_MIN` and `TICK_SEC`.

### 2. The command centre

```bash
pnpm install                      # from the repo root
pnpm dev:web                      # http://localhost:5173
```

Vite proxies `/api` and `/ingest` to `127.0.0.1:8787`, so no environment variable is needed
locally. Set `VITE_PLANT_URL` only when the plant is on another host.

### 3. The staff app (Expo Go)

```bash
EXPO_PUBLIC_PLANT_URL=http://<laptop-LAN-IP>:8787 pnpm dev:staff
```

The phone must reach the laptop. The inbox screen prints the URL it is using, so a wrong IP is
visible rather than silent. Without the camera you can type codes: `UNIT:BAG-ONEG-01`,
`VAULT:FREEZER_BLOOD_04`, `VAULT:FREEZER_BLOOD_03`.

### 4. Drive the demo

Use the command-centre header buttons (**Kill probe**, **Compressor fail**, **Second vault**,
**Reset plant**) or the CLI against a running plant:

```bash
cd apps/sim
.venv/bin/python -m sim --anomaly ILR_VAX_02 lwt            # probe death → ticket only
.venv/bin/python -m sim --anomaly FREEZER_BLOOD_04 compressor  # predicted breach → MOVE
.venv/bin/python -m sim --anomaly FREEZER_BLOOD_05 compressor  # forced cascade
.venv/bin/python -m sim --anomaly ALL reset                 # replay for the next judge
```

The full 90-second beat is in [docs/demo-script.md](docs/demo-script.md). Print
[docs/qr-stickers.html](docs/qr-stickers.html) before travelling.

### Tests and checks

```bash
cd apps/sim && .venv/bin/pytest -q      # 67 tests
pnpm typecheck                          # web + shared
pnpm build:web
```

## Honest limitations

Stated up front, because a discovered limit is worse than a declared one.

- **The freeze rail cannot be demonstrated.** `T_eq` is monotonically at or above setpoint in the
  current model, so `minutes_to_freeze` always returns the stable sentinel. "Freeze ≤ 0 °C kills
  alum-adjuvanted vaccines" is a real hazard and is in the pitch, but the plant has no overcool or
  stuck-thermostat stimulus to trigger it.
- **Supabase is a fan-out, not a second brain.** Project `cefhoczywrycsbniywus` stores what the
  Python plant already decided. `functions/ingest` returns 410 so it cannot pick the wrong backup
  (`WALKIN_COLD_02` vs `FREEZER_BLOOD_06`). Anon is SELECT-only; writes are service-role. RLS is
  demo-open **read**, not hospital-grade auth. Summit clients stay on LAN unless you opt in.
- **Only the `telemetry` MQTT topic is published,** and only when `MQTT_HOST` is set. `status`,
  `lwt`, `cmd/…/reroute` and `alerts/…` are a specified hardware contract, not emitted traffic.
- **The plant is still in-memory.** Cloud tables are a copy of the running process. Do not restart
  the plant during a judge run (`_active_alerts` is not persisted and can re-fire). GitHub Pages
  hosts the run guide only — it does not host the command centre.
- **No auth, no multi-tenancy, no push notifications.** One site, one process, in-app haptics only.
- **Not built:** a real ESP32 on the bench with a live MQTT last-will, and a backup screen
  recording of the demo.

## Deliberately out of scope

ARIMA or any learned forecaster (the physics is explainable and the data is synthetic); a
constraint solver for routing (a greedy O(vaults) rule is defensible on stage); FCM/APNs; a native
map; multi-tenant RLS; and MQTT as the live bus — venue Wi-Fi must not be able to kill the demo.

## Compliance posture

Temperature bands are hardcoded from CDSCO, NBTC and WHO published sources. The system alarms on
any out-of-range reading and **never auto-discards**: a door-open is an event, product leaving the
labelled band is an excursion that leads to quarantine and QA review. Freeze is treated as
seriously as heat. Mean kinetic temperature is computed as an illustrative thermal-stress index on
insulin/pharma-fridge assets only, and is **never** used to release blood or vaccines
(USP ⟨1079.2⟩).

Audit-trail controls are **inspired by** 21 CFR Part 11.10 and CDSCO GDP §15.7. CryoDispatch is
**not** FDA or Part 11 certified, **not** WHO PQS prequalified, **not** NABH or NABL accredited,
**not** a replacement for eVIN or e-BloodBank, and MKT here does **not** prove potency. eVIN
already monitors vaccine ILRs nationally and e-BloodBank already handles blood inventory;
CryoDispatch sits beside them and runs the hospital-floor closed loop they do not.
