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
.venv/bin/pytest -q                   # 67 tests
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

- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` — after each tick, publish full lists to the
  dedicated CryoDispatch project and drain `plant_intents`. The plant remains the decision
  engine. Do not set `INGEST_URL` at the old Deno ingest (it returns 410).
- `MQTT_HOST` — also publish the `telemetry` topic with `paho-mqtt` (install the `mqtt` extra).
  Nothing subscribes to it; see `docs/mqtt-schema.md`.

Neither is required for the summit LAN demo.

## Layout

`thermal.py` physics · `hospital.py` asset/staff/inventory registry · `dispatch.py` routing cost
and cascade risk · `plant.py` state machine, alerts, missions, custody · `cloud.py` optional
PostgREST publisher · `server.py` HTTP + SSE · `models.py` pydantic wire models. Endpoints and
invariants are documented in `docs/architecture.md`.
