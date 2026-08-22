# Telemetry simulator

Replaces physical IoT hardware. 24 assets, MQTT-shaped JSON, anomaly CLI, local plant API on :8787.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m sim
python -m sim --anomaly FREEZER_BLOOD_04 compressor
python -m sim --anomaly ILR_VAX_02 lwt
pytest
```

The plant server is the venue-proof live path. Optionally set `INGEST_URL` to also POST to Supabase, or `MQTT_HOST` to publish with paho.
