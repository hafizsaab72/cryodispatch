# Tech context — exact stack and versions

Monorepo: pnpm workspaces (`pnpm@10.15.0`, `pnpm-workspace.yaml` covers `apps/*` and `packages/*`).
Root scripts: `dev:web`, `dev:staff`, `build:web`, `typecheck`, `sim`.

## apps/sim — the plant

Python `>= 3.12` (checked-out `.venv` is 3.14.7). Package `cryodispatch-sim`, src layout, entry
point `cryosim` / `python -m sim`.

- Runtime: `fastapi>=0.115`, `uvicorn[standard]>=0.32`, `pydantic>=2`, `httpx>=0.27`, `rich>=13`,
  `python-dotenv>=1.0`.
- Extras: `mqtt` → `paho-mqtt>=2`; `dev` → `pytest>=8` (58 tests in `apps/sim/tests`).
- Serves on `PLANT_HOST:PLANT_PORT` (default `0.0.0.0:8787`), CORS open, SSE at `/api/events`.
- Env: `SITE_ID` (`elcia-emc`), `DEMO_TAU_MIN` (2.0), `TICK_SEC` (1.0), optional `INGEST_URL` /
  `INGEST_KEY` for Supabase mirroring, optional `MQTT_HOST` / `MQTT_PORT` / `MQTT_USERNAME` /
  `MQTT_PASSWORD`. Loads the repo-root `.env` then a local one.

## apps/web — command centre

Vite `^7.1.3`, React `^19.1.1`, TypeScript `^5.9.2`, Tailwind v4 (`@tailwindcss/vite ^4.1.12`),
`@phosphor-icons/react ^2.1.10`, `recharts ^3.1.2`, `jspdf ^3.0.1` + `jspdf-autotable ^5.0.2`.
Dev server on 5173 with `host: true`, proxying `/api` and `/ingest` to `127.0.0.1:8787`.
`VITE_PLANT_URL` overrides the base (default empty → use the proxy). The custody PDF is generated
in the browser; its footer carries the "inspired by 21 CFR 11.10 / CDSCO GDP" disclaimer.

## apps/staff — Expo

Expo SDK `~56.0.12`, `expo-router ~56.2.11` (root `src/app`, typed routes), React Native `0.85.3`,
React `19.2.3`, `expo-camera ~56.0.8`, `expo-haptics ~56.0.3`, `react-native-screens 4.26.2`
(pinned by `expo install --fix`), `react-native-safe-area-context ~5.7.0`, TypeScript `^6.0.3`.
Runs in Expo Go; polls `/api/state` every 2 s (no SSE on the phone). `EXPO_PUBLIC_PLANT_URL`
defaults to `http://127.0.0.1:8787`. In-app haptics only — no FCM/APNs, no native map.

`expo-constants` and `expo-linking` are **required non-optional peer dependencies of expo-router**
and `react-native-gesture-handler` is required by `react-native-drawer-layout` underneath it, so
all three stay in `package.json` even though no app file imports them directly.

## Root `.npmrc`

`shamefully-hoist=true` gives Metro a flat `node_modules`, which Expo needs under pnpm. Keep it.
The "Unknown project config" warning only appears when npm is used instead of pnpm.

## packages/shared

TypeScript-only, no build step (`main`/`types` point straight at `src/index.ts`); the web app
resolves it through a Vite alias.

## supabase — hosted path (not used by the demo)

Postgres migrations (`asset_state`, `telemetry`, `alerts`, `missions`, `audit_events`,
`inventory`, `staff`, all RLS-enabled) plus `functions/ingest` (Deno, `@supabase/supabase-js@2`).
Needs a fresh Supabase project. Known to diverge from the Python plant — see `active-context.md`.

## docs/pitch

`CryoDispatch.pptx` is a build artefact of `build-deck.cjs`. `pptxgenjs` is deliberately **not** a
repo dependency; rebuilding needs a throwaway install (see `docs/pitch/README.md`).
