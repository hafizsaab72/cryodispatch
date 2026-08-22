# Product context

Hospitals lose blood, insulin, and vaccines to silent compressor failure and door-open heat. National systems (eVIN, e-BloodBank) already monitor immunization stock and blood inventory. CryoDispatch sits **beside** them on the hospital floor: classify the fault, predict minutes-to-breach while air is still legal, move the right units to the right door, prove custody, ticket the compressor.

Judges from industrial/electronics companies will reject a Grafana clone. They reward a closed loop: sense → decide → act → verify.

Fault taxonomy:
- `PROBE_DEAD` — last-will / sensor death. Ticket only. Do not move stock.
- `THERMAL_EXCURSION` — spoilage clock + dispatch.
- `BOTH` — worst case.

Door-open is an event. Product leaving the labelled band is an excursion → quarantine, never auto-discard. Freeze (≤0°C on alum vaccines) is as critical as heat.
