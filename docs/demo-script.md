# 90-second live demo

Hospital: **ELCIA Medical Centre**. Plant: `cd apps/sim && .venv/bin/python -m sim`. Command centre: `pnpm dev:web`. Staff: Expo Go.

Print [qr-stickers.html](qr-stickers.html) **before** you travel. Hand the phone to a judge.

| t | Say / do |
| --- | --- |
| 0–10s | Floor map, 24 assets, all in band. "This is a plant, not a dashboard. Newton cooling for the cabinet, Arrhenius for the drug." |
| 10–25s | **Kill probe** (`ILR_VAX_02`). Node turns violet. A maintenance ticket opens and **no MOVE appears**. "A dead probe means we don't know the temperature — it doesn't mean the blood is hot, so we ticket the instrument and leave the stock where it is." |
| 25–40s | **Compressor fail** (`FREEZER_BLOOD_04`). `T_eq` jumps to 7.8°C, the countdown starts at ~1.4 min, and the chip still reads **AIR STILL IN BAND**. "We are not reacting to a breach. We are predicting one." MOVE card: 4 bags (1.4 L) → `FREEZER_BLOOD_03`, Nurse Rao, hold 0.468 kWh vs move 0.220 kWh. |
| 40–65s | Staff phone: **Accept**, scan `UNIT:BAG-ONEG-01` → `VAULT:FREEZER_BLOOD_04` → deliberately scan the **wrong** vault card (red REJECTED) → then `VAULT:FREEZER_BLOOD_03`. Custody closes live on the wall. |
| 65–80s | **Second vault** (`FREEZER_BLOOD_05`, 2 bags / 0.7 L). Vault 3 has only 0.4 L left, so the router cascades to `FREEZER_BLOOD_06` (ICU satellite 2). "The backup had room for one vault, not two — the router knew that before it committed." |
| 80–90s | **Custody PDF**. Nine GDP fields, disposition RELEASED because we moved *before* any excursion, payload hash at the top. "Detect, predict, dispatch, verify, prove." |

## Between judges

Press **Reset plant** in the command centre header. Stock returns to its home vault, staff are freed, reserved litres are released, and alerts clear — the full script can be run again without restarting the process.

CLI equivalents:

Run these from `apps/sim`, against the already-running plant (they POST to `/api/anomaly` on
`127.0.0.1:8787`; if no plant answers they fall back to an in-process one-shot):

```bash
.venv/bin/python -m sim --anomaly ILR_VAX_02 lwt
.venv/bin/python -m sim --anomaly FREEZER_BLOOD_04 compressor
.venv/bin/python -m sim --anomaly FREEZER_BLOOD_05 compressor
.venv/bin/python -m sim --anomaly ALL reset
```

## If something goes wrong

- **Phone cannot reach the plant** — the inbox prints the URL it is using. Re-launch with `EXPO_PUBLIC_PLANT_URL=http://<laptop-LAN-IP>:8787`. Tether the phone to the laptop hotspot rather than venue Wi-Fi.
- **Wrong sticker rejected unexpectedly** — the scan screen always shows the live source and destination. Read it off the phone; do not trust the printed label.
- **Everything is dirty** — **Reset plant** in the header. Do not restart the plant process mid-judge: alert dedup lives in memory and a restart can re-raise the same tickets. Cloud tables (if enabled) are a copy of this process, not a second brain.
- Venue Wi-Fi is never required. Leave `VITE_SUPABASE_*` and `EXPO_PUBLIC_SUPABASE_*` unset so the wall and phone stay on the laptop LAN.
- If you did opt into Realtime, pause after **Compressor fail** before handing the phone — Accept waits on the next plant tick.

## If a judge pushes

- *"Can you show the freeze case?"* — No. `T_eq` never falls below setpoint in this model, so the
  freeze countdown is unreachable; the band is enforced and alarmed, but the stimulus is not built.
  Say that rather than improvising.
- *"Is this certified?"* — No. Controls are inspired by 21 CFR Part 11.10 and CDSCO GDP §15.7.
  Not FDA/Part 11 certified, not WHO PQS prequalified, not NABH/NABL accredited, not an eVIN
  replacement. MKT is a thermal-stress index and never releases blood or vaccines.
- *"Is that real MQTT?"* — Only `telemetry` is published, and only when `MQTT_HOST` is set. The
  rest of `docs/mqtt-schema.md` is a hardware contract. The live path is HTTP on the LAN, on
  purpose.
- *"Is this on the cloud?"* — Optional. The summit path is the laptop LAN. Supabase stores what
  the plant already decided; it does not classify faults or pick `FREEZER_BLOOD_06`.
