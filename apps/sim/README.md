# apps/sim — the plant

The brain of CryoDispatch and the live demo path: a 24-asset telemetry simulator, the lumped
thermal model, the fault taxonomy, the greedy dispatcher, the custody and audit log, and a FastAPI
server with Server-Sent Events on `:8787`. Real hardware can replace the simulator half by POSTing
the same JSON to `/ingest` — see `docs/firmware/cryodispatch_esp32.ino`.

## Setup and run

```bash
python3 -m venv .venv                 # Python >= 3.12 (this venv is 3.14)
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m sim               # plant + API on 0.0.0.0:8787
.venv/bin/pytest -q                   # 58 tests
```

Flags: `--host`, `--port`, `--tick` (seconds per step), `--tau` (demo time constant, minutes),
`--no-server` (terminal table only), `--anomaly ASSET KIND` where kind is
`compressor | door | lwt | reset` (`ALL reset` resets the whole plant).

```bash
.venv/bin/python -m sim --anomaly FREEZER_BLOOD_04 compressor
.venv/bin/python -m sim --anomaly ILR_VAX_02 lwt
```

With a plant already running, `--anomaly` POSTs to its `/api/anomaly` so the live demo reacts;
otherwise it applies the anomaly in-process and prints the result.

## Optional outputs

- `INGEST_URL` (+ `INGEST_KEY`) — also POST every tick to a hosted Supabase ingest function.
- `MQTT_HOST` — also publish the `telemetry` topic with `paho-mqtt` (install the `mqtt` extra).
  Nothing subscribes to it; see `docs/mqtt-schema.md`.

Neither is required, and neither is on the demo path.

## Layout

`thermal.py` physics · `hospital.py` asset/staff/inventory registry · `dispatch.py` routing cost
and cascade risk · `plant.py` state machine, alerts, missions, custody · `server.py` HTTP + SSE ·
`models.py` pydantic wire models. Endpoints and invariants are documented in
`docs/architecture.md`.
