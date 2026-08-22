# Product context — problem, users, differentiators

## Problem

Hospitals lose blood, insulin and vaccines to silent compressor failure and door-open heat. The
gap is not monitoring — it is what happens in the twenty minutes after a vault starts to fail:
who decides, who carries, where it goes, and what proves it was safe.

## Where it sits

eVIN already monitors vaccine ILRs nationally; e-BloodBank already handles blood inventory.
CryoDispatch is **not** a replacement for either. It sits beside them and runs the hospital-floor
closed loop they do not: classify the fault, predict minutes-to-breach while the air is still
legal, move the right units to the right door with a certified nurse, prove custody, ticket the
compressor.

## Users

- **Command centre operator** — wall display; sees the floor map, the countdown, the alert rail,
  and prints the custody certificate.
- **Ward / blood-bank nurse** — phone; receives a locked MOVE, accepts it, scans unit → source →
  destination. A wrong vault is a hard reject.
- **Biomedical engineer** — receives the maintenance ticket with duty-cycle evidence, parts, an
  SLA, and the hold-versus-move energy comparison.
- **Judge / auditor** — reads the nine-field PDF and asks whether the claims are honest.

## Differentiators (the three arguments)

1. **Predict, don't react.** First-order lumped thermal model; the countdown starts when `T_eq`
   crosses the band, not when the air does. Not ARIMA, not `if (temp > 8)`.
2. **A dead probe is not a hot vault.** `PROBE_DEAD` → ticket only, stock stays put.
   `THERMAL_EXCURSION` → spoilage clock + dispatch. `BOTH` (blind *and* out of band) → evacuate
   and re-instrument. Generic IoT treats "no data" as "hot".
3. **Prove it.** Greedy router (distance, free capacity, cascade risk, kWh), reserved litres so a
   second failure cascades elsewhere, and a Chain of Cold Custody PDF for every move.

## Compliance line (load-bearing — must never regress)

Bands are hardcoded from CDSCO / NBTC / WHO sources. Alarm on any out-of-range reading; **never**
auto-discard. Door-open is an event; product leaving the labelled band is an excursion →
quarantine → QA review. Freeze (≤ 0 °C) is as dangerous as heat for alum-adjuvanted vaccines. MKT
is an illustrative thermal-stress index on insulin/pharma-fridge assets only and is **never** used
to release blood or vaccines (USP ⟨1079.2⟩).

Every document says controls are *inspired by* 21 CFR Part 11.10 and CDSCO GDP §15.7, and must
never claim: FDA/Part 11 certified or compliant, WHO PQS prequalified, NABH/NABL accredited, an
eVIN replacement, or that MKT proves potency.
