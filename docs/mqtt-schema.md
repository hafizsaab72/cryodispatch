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

HTTP POST to `/ingest` (alias `/api/ingest`) is that payload with `topic` in the body. An unknown
`asset_id` returns `404`; a non-numeric `temperature` or `compressor_health` returns `422`, because
a malformed sensor frame is a data-quality fault and not a server crash.

**Implementation status, stated plainly:** the simulator publishes `telemetry` at QoS 0 when
`MQTT_HOST` is set, using `paho-mqtt` from the optional `mqtt` extra. `status`, `lwt`,
`cmd/…/reroute`, and `alerts/…` are a specified contract for the firmware and the cloud bridge,
not something the demo currently emits — and neither does the bundled ESP32 sketch, which posts
over HTTP. The live demo path is HTTP, and the dashboard subscribes to the plant, not a broker.
`GET /api/protocol` returns this topic list, which is what the command centre's Protocol panel
renders.

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

If the last reading before the probe died was already outside the labelled band, the classification
becomes `BOTH` — blind *and* out of band — and that case does evacuate, because the product is
already at risk and the instrument can no longer prove otherwise.

## Hardware drop-in

An ESP32 publishing this JSON to `POST /ingest` or to the telemetry topic is a legal replacement for `apps/sim`. See `docs/firmware/cryodispatch_esp32.ino`.
