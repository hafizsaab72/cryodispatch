# System patterns — architectural rules and invariants

Full narrative is in `docs/architecture.md`. This file is the short list of rules that must hold.

## Rules

- **Rules live in the plant, never in a client.** Web and staff render state and post intents
  (`accept`, `scan`, `anomaly`, `reset`, `ack`). No fault class, destination or disposition is
  decided client-side.
- **One JSON payload on HTTP and MQTT.** The HTTP body carries `topic`; an ESP32 is a drop-in
  replacement for the simulator.
- **HTTP + SSE is the live path;** MQTT is a device contract. A broker must never be able to take
  the demo down. Supabase Realtime is opt-in (`VITE_SUPABASE_*` / `EXPO_PUBLIC_SUPABASE_*`);
  unset means today’s LAN path.
- **Upsert latest state, append history sparsely** (every ~15 s or on anomaly), never at 1 Hz.
  Cloud sync writes **full** lists, not `snapshot()`. Network I/O never runs inside `Plant._lock`.
  Reset on the cloud path is delete-then-insert.
- **Greedy dispatch, not a solver.** `cost = 3·distance + 2·staff_eta + (1 − free_frac) +
  2·kwh_move + 4·cascade_risk`. O(vaults) and explainable on stage.
- **Demo τ is compressed to 2 min** for every cabinet (`DEMO_TAU_MIN`); real cabinets are ~12 min,
  walk-ins ~18. Physics unchanged, clock compressed — say so out loud.
- Single site, single in-memory process. Optional PostgREST fan-out to project
  `cefhoczywrycsbniywus` (ap-south-1). Anon SELECT-only; no hospital-grade RLS. Do not reuse
  Lensora (`eqexoblnsbewvfunqxky`).

## Invariants

1. `PROBE_DEAD` opens an instrumentation ticket and moves nothing. Only `BOTH` (offline *and* last
   reading out of band) dispatches.
2. The predictive alert fires from `T_eq` crossing the threshold, not the measured air. The gauge
   must keep showing an explicit in-band chip beside the countdown.
3. Capacity is **derived** on every change — `used_l` from inventory, `reserved_l` from open
   missions (`_recompute_capacity`). Never incremented in place.
4. Destinations are reserved at proposal time, which is what forces the real cascade.
5. Courier certification is a hard requirement; no cross-cert fallback. If no certified courier
   is free, do not create a mission — ticket and escalate instead.
6. Mission `units` are a snapshot at dispatch, not a live inventory reference.
7. MKT is computed for `insulin_ilr` only and never gates a release.
8. Reset is total: stock to `home_asset_id`, staff freed, reservations released, missions
   cancelled, alerts and tickets cleared. The demo must be replayable without restarting.
9. Alert dedup is keyed per `(asset_id, fault_class)`, so a probe death after a thermal alert
   still raises its own ticket. A second fault on the same stocked vault does **not** open a
   second mission — it audits an escalation on the existing one.
10. QR custody order is unit → source vault → destination vault; any wrong code is a logged
    rejection, and rejections appear in the custody log. Custody events never invent an actor
    (`staff_name` or `"unassigned"`).
11. Malformed telemetry is a data-quality fault: `422`, never a 500. That includes a missing
    `asset_id`, non-finite temperature, and `compressor_health` outside `[0, 1]`.
12. Incomplete missions still return a custody document (`draft: true`, disposition starts
    `DRAFT — `). Only `status == complete` asserts RELEASED / QUARANTINE.
13. `Plant` is guarded by one `threading.RLock` on `step`, `ingest`, `anomaly`, `reset_all`,
    `accept_mission`, `scan_mission`, `ack_alert`, and `snapshot`.
14. `DOOR_OPEN` is a warn-only event while the air is in band and `t* ≥ 5` min; it escalates to
    `THERMAL_EXCURSION` (and a MOVE) once the air leaves the band or the countdown drops below 5.
    At demo `τ = 2` a door anomaly escalates immediately — use `τ ≈ 30` to show the event itself.

## Scripted demo facts that code must keep true

`ILR_VAX_02` probe kill → ticket, no MOVE. `FREEZER_BLOOD_04` compressor → `T_eq` 7.8 °C, `t*`
≈ 1.4 min, 4 bags (1.4 L) → `FREEZER_BLOOD_03`, Nurse Rao, hold 0.468 kWh vs move 0.220 kWh.
`FREEZER_BLOOD_05` (0.7 L) → forced cascade to `FREEZER_BLOOD_06`, because vault 3 has 19.6 L
capacity with 17.8 L baseline stock. These IDs and numbers also appear in `docs/demo-script.md`,
`docs/qr-stickers.html` and `docs/pitch/build-deck.cjs` — change all of them together.
