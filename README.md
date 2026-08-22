# CryoDispatch

**Predict. Dispatch. Prove.** Hospital cold-chain plant for ELCIA Tech Summit 2026.

This is a closed loop, not a chart dashboard: sense → classify fault → predict time-to-breach → move the right bag → verify custody with QR → open a compressor ticket. Dead probes do **not** trigger evacuations.

Not an eVIN replacement. Not FDA/NABH/WHO PQS certified.

## Apps

| Path | What |
| --- | --- |
| `apps/sim` | Python telemetry simulator + local plant API (port 8787) |
| `apps/web` | Command center (Vite + React) |
| `apps/staff` | Staff action app (Expo, 3 screens) |
| `supabase/` | Postgres migrations + `ingest` Edge Function |
| `packages/shared` | Shared TypeScript types |

## Quick start (venue-proof local demo)

```bash
cd apps/sim
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m sim
```

In another terminal:

```bash
pnpm install
pnpm dev:web
```

Open http://localhost:5173. Trigger **Kill probe**, then **Compressor fail**, then accept the MOVE on the staff app.

```bash
# Staff (Expo Go). Use your machine LAN IP if the phone is not localhost.
EXPO_PUBLIC_PLANT_URL=http://<LAN-IP>:8787 pnpm dev:staff
```

Anomaly from the CLI while the plant is running:

```bash
python -m sim --anomaly FREEZER_BLOOD_04 compressor
python -m sim --anomaly ILR_VAX_02 lwt
```

## Demo beat (90 seconds)

See [docs/demo-script.md](docs/demo-script.md). Pitch deck: [docs/pitch/CryoDispatch.pptx](docs/pitch/CryoDispatch.pptx). Printable QR cards: [docs/qr-stickers.html](docs/qr-stickers.html). Hardware drop-in: [docs/firmware/cryodispatch_esp32.ino](docs/firmware/cryodispatch_esp32.ino).

MQTT topic contract: [docs/mqtt-schema.md](docs/mqtt-schema.md). The live path is HTTP → plant (or Supabase). The dashboard never subscribes to a broker.
