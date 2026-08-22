# Active context

**Repo:** `github.com/hafizsaab72/cryodispatch` (public, `main`).
GitHub Pages serves `docs/` at https://hafizsaab72.github.io/cryodispatch/
(`docs/index.html` redirects to `how-to-run.html`).

## This session (23 Aug, Supabase client cutover)

Dedicated project **cryodispatch**, ref `cefhoczywrycsbniywus`, region `ap-south-1`,
org `cdbjfqgflhgdjarlrieo`. Dashboard:
https://supabase.com/dashboard/project/cefhoczywrycsbniywus

Do **not** link or migrate into Lensora (`eqexoblnsbewvfunqxky`) or onthetab.

Rule that did not move: all decisions stay in `apps/sim`. Supabase stores and fans out
what the plant already decided. Summit default remains LAN (`VITE_SUPABASE_*` /
`EXPO_PUBLIC_SUPABASE_*` unset). `functions/ingest` is 410; ESP32 stays on plant `/ingest`.

## Prior (23 Aug, GitHub Pages)

Repo is public. Pages source is `main` / `docs`. Site root redirects to the run guide.

## Prior (23 Aug, run guide)

Added an illustrated first-run walkthrough — `docs/how-to-run.md`, offline twin
`docs/how-to-run.html`, SVGs in `docs/images/`, and a pointer from the README **Run it**
section. No app behaviour changed.

## Verified state (23 Aug, cutover)

- 67 Python tests (`cd apps/sim && .venv/bin/pytest -q`).
- Web / shared / staff typecheck clean.
- Seeded remote DB: 24 `asset_state`, 4 staff including `nurse-dsouza`, 10 inventory units.
- Intent + ingest Edge Functions deployed on `cefhoczywrycsbniywus`.
- Public docs (`README`, how-to-run, architecture, demo-script, supabase README) describe dual-mode:
  LAN is the summit default; Supabase is a plant fan-out, not a second brain.

## Still open — document honestly, do not paper over

- **Freeze rail is unreachable in the live demo.** `t_eq` is monotonically at or above setpoint,
  so `minutes_to_freeze` stays at the sentinel unless a test injects `teq < 0`. The field and
  gauge label exist; there is still no overcool / stuck-thermostat stimulus. Pitch line
  "freeze kills alum vaccines" cannot be shown on stage. Not demo-blocking for the 7 beats
  (those are heat). **Blocking for the freeze claim.**
- **`DOOR_OPEN` at demo τ=2 escalates immediately** to `THERMAL_EXCURSION`. The event itself
  needs `τ ≈ 30`. Not demo-blocking (door is not one of the 7 beats).
- **Only `telemetry` is published over MQTT,** and only when `MQTT_HOST` is set.
- **Plant memory is still the source of truth.** Cloud is a fan-out. Do not restart the plant
  mid-judge (`_active_alerts` is not persisted). RLS is demo-open SELECT, not hospital-grade.
- **Not started:** backup screen recording, print-ready architecture poster, two dress
  rehearsals, and a real ESP32 with a live MQTT last-will.

`docs/pitch/CryoDispatch.pptx` is a build artefact; regenerate it only if `build-deck.cjs`
changes.
