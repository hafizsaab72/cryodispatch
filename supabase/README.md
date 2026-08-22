# supabase — optional fan-out (not the summit default)

Dedicated project **cryodispatch**, ref `cefhoczywrycsbniywus`, region `ap-south-1`.
Do **not** link or migrate into Lensora (`eqexoblnsbewvfunqxky`) or onthetab.

The Python plant in `apps/sim` is the only decision engine. This project stores and fans
out what the plant already decided. Clients use Realtime **only** when `VITE_SUPABASE_*` /
`EXPO_PUBLIC_SUPABASE_*` are set. If those are unset, today’s SSE / LAN path is unchanged.

`functions/ingest` is a **410 Gone** stub. It must not classify faults or pick backups
(the old Deno `backupFor` map sent `FREEZER_BLOOD_05` to `WALKIN_COLD_02`; the plant
picks `FREEZER_BLOOD_06`). ESP32 firmware posts to the plant `POST /ingest` on `:8787`.

`functions/intent` inserts `plant_intents` rows (service role, server-side). The plant
drains them each tick **before** `step()`, then publishes full in-memory lists (not the
truncated UI snapshot). Reset is delete-then-insert so ghost missions do not linger.

Anon is **SELECT only**. Writes go through the service role (plant + intent function).
Never put `SUPABASE_SERVICE_ROLE_KEY` in web/staff env.

## Deploy (this project)

```bash
# .supabase/ is gitignored — link after adding it to .gitignore
supabase link --project-ref cefhoczywrycsbniywus
supabase db push
supabase db query --linked -f supabase/seed.sql
supabase functions deploy ingest --no-verify-jwt
supabase functions deploy intent --no-verify-jwt
```

Seed is generated from `hospital.py` (24 assets, 4 staff including `nurse-dsouza`, 10 units):

```bash
PYTHONPATH=apps/sim/src python supabase/scripts/gen_seed.py
```

Plant `.env` (local, gitignored): `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`.
Leave `VITE_SUPABASE_*` and `EXPO_PUBLIC_SUPABASE_*` commented for the summit LAN demo.

The plant must be running and publishing for cloud clients to move. Venue Wi-Fi must not
be required for the live demo.
