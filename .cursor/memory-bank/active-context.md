# Active context

Building the 48-hour core. Simulator, ingest, command center, staff app, MQTT schema, demo kit, and pitch deck are in-repo.

Demo hospital: ELCIA Medical Centre (`elcia-emc`), 24 assets.

Plant: `http://localhost:8787` via `cd apps/sim && .venv/bin/python -m sim`
Web: `pnpm dev:web`
Staff: `EXPO_PUBLIC_PLANT_URL=http://<LAN-IP>:8787 pnpm dev:staff`

Do not commit unless asked.
