# Overview

CryoDispatch is a hospital cold-chain **plant** at `/Users/hafizsaab/Documents/Personal/cryodispatch`.

**Tagline:** Predict. Dispatch. Prove.

**Event:** ELCIA Tech Summit 2026 (10 Sep, The Oterra). Theme: Humans, Machines & Meaning 3.0.

**What it is:** Simulated IoT telemetry + predictive thermal model + greedy emergency reroute + QR chain-of-custody + compressor ticket. Three apps: Python sim, Vite command center, Expo staff.

**What it is not:** eVIN replacement, FDA/NABH/WHO PQS certified product, ARIMA/ML demo, MQTT-only bus.

**Live path:** HTTP POST → plant ingest (local FastAPI on :8787, or Supabase Edge Function) → Realtime/SSE → web + staff. MQTT is a hardware-ready contract, optional second publisher.
