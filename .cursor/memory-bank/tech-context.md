# Tech context

- **Sim:** Python 3.12, pydantic v2, httpx, rich, python-dotenv, FastAPI + uvicorn (local plant). Optional `paho-mqtt`.
- **Web:** Vite, React, TypeScript, Tailwind v4, Phosphor, Recharts, jsPDF, Zustand. Talks to `VITE_PLANT_URL` (default `http://localhost:8787`). Supabase JS is available for a hosted swap.
- **Staff:** Expo SDK 56, Expo Router (`src/app`), Expo Go. `EXPO_PUBLIC_PLANT_URL`. In-app haptic, no FCM/APNs. No native map.
- **DB (hosted path):** New Supabase project — do **not** reuse Lensora. Tables: `asset_state`, `telemetry`, `alerts`, `missions`, `audit_events`, plus `inventory` and `staff` seed.
- **Ingest:** `supabase/functions/ingest` (Deno) mirrors `apps/sim` thermal + dispatch.
- **PDF:** jsPDF in the browser (9 custody fields). Footer: inspired by 21 CFR 11.10 / CDSCO GDP — not certified.
- **Firmware:** Arduino ESP32 + DHT22 sketch publishes the same payload.
