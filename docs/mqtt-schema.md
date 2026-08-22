# CryoDispatch MQTT contract

Devices speak MQTT. The cloud bridge upserts the **same JSON** the HTTP ingest accepts. Ops UIs subscribe to the database / plant API, **not** the broker. That is how real SCADA is wired.

Site token: `{site}` = `elcia-emc` in the demo.

## Topics

| Topic | QoS | Retain | Purpose |
| --- | --- | --- | --- |
| `cryo/{site}/assets/{id}/telemetry` | 0 | no | 1 Hz sensor payload |
| `cryo/{site}/assets/{id}/status` | 1 | **yes** | derived plant state (mode, t_eq, minutes_to_breach) |
| `cryo/{site}/assets/{id}/lwt` | 1 | yes | Last Will `offline` → fault class `PROBE_DEAD` |
| `cryo/{site}/cmd/{id}/reroute` | 1 | no | locked MOVE instruction |
| `cryo/{site}/alerts/{alertId}` | 1 | no | alert + ticket |

HTTP POST to `/ingest` is that payload with `topic` in the body.

## Telemetry payload

```json
{
  "topic": "cryo/elcia-emc/assets/FREEZER_BLOOD_04/telemetry",
  "asset_id": "FREEZER_BLOOD_04",
  "asset_class": "blood_rbc",
  "location": "Floor 1 — Blood Bank B",
  "floor": 1,
  "zone": "blood-b",
  "temperature": 4.2,
  "door_status": "CLOSED",
  "compressor_health": 0.88,
  "battery_pct": 97,
  "probe_online": true,
  "map_x": 62,
  "map_y": 48,
  "timestamp": 1724500000
}
```

Crash carts omit thermal fields (`temperature` may be null) and report `map_x` / `map_y` only.

## Last Will

Broker LWT payload: `{"asset_id":"ILR_VAX_02","probe_online":false,"reason":"offline"}`.

Ingest maps this to `model_mode=probe_dead` and `fault_class=PROBE_DEAD`. **Do not evacuate stock.** Open a maintenance ticket only.

## Hardware drop-in

An ESP32 publishing this JSON to `POST /ingest` or to the telemetry topic is a legal replacement for `apps/sim`. See `docs/firmware/cryodispatch_esp32.ino`.
