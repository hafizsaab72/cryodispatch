# Active context

**Repo:** `github.com/hafizsaab72/cryodispatch` (public, `main`).
GitHub Pages serves `docs/` at https://hafizsaab72.github.io/cryodispatch/
(`docs/index.html` redirects to `how-to-run.html`).

## This session (23 Aug, GitHub Pages)

Repo is public. Pages source is `main` / `docs`. Site root redirects to the run guide.

## Prior (23 Aug, run guide)

Added an illustrated first-run walkthrough — `docs/how-to-run.md`, offline twin
`docs/how-to-run.html`, SVGs in `docs/images/`, and a pointer from the README **Run it**
section. No app behaviour changed.

## Prior in this session (23 Aug, wakeup resume)

Parent chat `613fb571` failed to synthesize two background fix agents after a usage-limit
switch to grok-4.6. Both agents died mid-edit:

- Plant agent `97127c03` landed thermal/models scaffolding (`minutes_to_breach` → float,
  least-squares `slope_c_per_min`, `breach_direction` on `Processed`, RLock + `_num` helpers
  on `Plant`) then stopped. `_process` still unpacked the old tuple and would have crashed.
- Frontend agent `017eac3a` landed App retry-poll, Gauge null-temp/freeze label, AlertRail
  tally, web plant-URL fallback, and shared types, then died with `pdf.ts` referencing an
  undefined `Custody` type.

This resume finished the in-scope defects. Do not treat the two agent transcripts as complete.

## Verified state (23 Aug, after resume)

- 58 Python tests pass (`cd apps/sim && .venv/bin/pytest -q`).
- `pnpm --filter @cryodispatch/web typecheck` and `pnpm --filter @cryodispatch/shared typecheck` clean.
- `pnpm --filter @cryodispatch/staff exec tsc --noEmit` clean.

## What this audit/fix round actually changed

Plant (`apps/sim`):

- One non-terminal mission per source vault; THERMAL then PROBE_DEAD/BOTH audits escalate.
- No MOVE without a certified courier (ticket + escalation alert instead).
- `threading.RLock` on mutating/reading entry points.
- Custody `mission_status` + `draft`; incomplete docs start `DRAFT — `.
- Custody events use `staff_name` or `"unassigned"`, never a fallback nurse name.
- Least-squares dT/dt over the last ~30 custody-window samples (`None` if < 5).
- `breach_direction` `heat|freeze|none`; `breach_threshold_c` is the rail actually approached.
- Ingest 422 for missing `asset_id`, non-finite temperature, `compressor_health` ∉ [0, 1].
- `DOOR_OPEN` reachable at realistic τ; escalates at `t* < 5` or out-of-band.
- `battery_pct` restored on reset; tick + audit kept (commented); complete-mission scans emit;
  unknown anomaly kinds name the valid set.

Frontend / shared:

- `App.tsx` stops the retry poll after the first good frame / first SSE frame.
- `Gauge.tsx` null-temperature chip + freeze-rail label.
- `AlertRail.tsx` derives in-band count (no hardcoded "24 assets in band").
- Production web base URL falls back to `hostname:8787`; staff names `EXPO_PUBLIC_PLANT_URL`.
- `scan.tsx` in-flight ref debounce; `mission/[id].tsx` loading vs not-found.
- Shared `BreachDirection`, `CustodyDocument.draft` / `mission_status`.
- `pdf.ts` uses `CustodyDocument`, draft banner, status on disposition.
- Unused `@` alias removed from web vite/tsconfig.

## Still open — document honestly, do not paper over

- **Freeze rail is unreachable in the live demo.** `t_eq` is monotonically at or above setpoint,
  so `minutes_to_freeze` stays at the sentinel unless a test injects `teq < 0`. The field and
  gauge label exist; there is still no overcool / stuck-thermostat stimulus. Pitch line
  "freeze kills alum vaccines" cannot be shown on stage. Not demo-blocking for the 7 beats
  (those are heat). **Blocking for the freeze claim.**
- **Supabase Deno ingest diverges** from the Python plant (risk formula, MKT scope, hardcoded
  `backupFor()` sending `FREEZER_BLOOD_05` to `WALKIN_COLD_02`, per-tick history writes, empty
  `units`). Unproven; either bring it to parity or keep labelling it the deployment story.
  Not demo-blocking.
- **`DOOR_OPEN` at demo τ=2 escalates immediately** to `THERMAL_EXCURSION`. The event itself
  needs `τ ≈ 30`. Not demo-blocking (door is not one of the 7 beats).
- **Only `telemetry` is published over MQTT,** and only when `MQTT_HOST` is set.
- **Not started:** backup screen recording, print-ready architecture poster, two dress
  rehearsals, and a real ESP32 with a live MQTT last-will.

`docs/pitch/CryoDispatch.pptx` is a build artefact; regenerate it only if `build-deck.cjs`
changes.
