# System patterns

- **Rules live in ingest**, never in the browser. Web and staff are subscribers + actors.
- **Upsert latest state** (`asset_state`). Append `telemetry` every 15s or on anomaly — never 1 Hz history inserts.
- **Same JSON on HTTP and MQTT.** HTTP body includes `topic`.
- **Lumped thermal plant** (Newton / RC) for minutes-to-breach. Compressor health derates cooling. Slope of last 8 samples is display-only.
- **MKT / Arrhenius** is illustrative on insulin/pharma-fridge assets only. Never used to release blood or vaccines.
- **Greedy dispatch** (not CP-SAT): sort units by urgency, reserve litres, cascade to the next vault, assign nearest certified staff, always emit a ticket.
- **QR custody:** unit → source vault → dest vault. Wrong vault is a hard reject.
- **Demo τ** is compressed (~2 min) so judges see prediction move in ~60s. State that physics is unchanged.
- One demo org, one plant process. No multi-tenant RLS theatre.
