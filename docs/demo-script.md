# 90-second live demo

Hospital: **ELCIA Medical Centre**. Plant: `python -m sim`. Command center: `pnpm dev:web`. Staff: Expo Go.

Print [qr-stickers.html](qr-stickers.html) first. Hand the phone to a judge.

| t | Say / do |
| --- | --- |
| 0–10s | Floor map, 24 assets. “This is a **plant**, not a dashboard. Newton cooling for the box.” |
| 10–25s | Click **Kill probe** (`ILR_VAX_02`). Purple node. Ticket only. **No MOVE.** “Dead probe ≠ spoiled blood.” |
| 25–40s | Click **Compressor V3** (`FREEZER_BLOOD_04`). `T_eq` jumps above 6°C while air is still ~4°C. Time-to-breach counts down. MOVE card: O-neg → `FREEZER_BLOOD_03`. kWh hold vs move. |
| 40–65s | Staff: **Accept**. Scan `UNIT:BAG-ONEG-01` → `VAULT:FREEZER_BLOOD_04` → once, scan the **wrong** dest sticker. Red reject. Then scan the real dest. |
| 65–80s | Click **Second vault** (`FREEZER_BLOOD_05`). Cascade: `WALKIN_COLD_02` because V7 litres are reserved. |
| 80–90s | **Custody PDF**. Nine GDP fields. Footer: inspired by 21 CFR 11.10 — not certified. “Closed loop.” |

CLI backup if the UI is busy:

```bash
python -m sim --anomaly ILR_VAX_02 lwt
python -m sim --anomaly FREEZER_BLOOD_04 compressor
python -m sim --anomaly FREEZER_BLOOD_05 compressor
```

Offline fallback: the plant on `:8787` is already local. If venue Wi-Fi dies, tether the phone to the laptop hotspot.
