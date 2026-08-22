# supabase — hosted path (not the demo path)

Migrations for `asset_state`, `telemetry`, `alerts`, `missions`, `audit_events`, `inventory` and
`staff`, plus a Deno `ingest` Edge Function that accepts the same telemetry JSON as the Python
plant. This exists to show the deployment story: Supabase Realtime would replace SSE and Postgres
would replace in-memory state.

> **It is not at parity with `apps/sim` and it is unproven.**
> `functions/ingest/index.ts` differs from the Python plant on the risk formula (no efficacy
> term), MKT (single-sample rather than windowed), destination selection (a hardcoded `backupFor()`
> map that sends `FREEZER_BLOOD_05` to `WALKIN_COLD_02`, where the Python router computes
> `FREEZER_BLOOD_06` from real capacity), history write frequency, and it inserts missions with an
> empty `units` array. Do not demo from here and do not quote its behaviour as the system's.

## Deploy (into a fresh Supabase project, not an existing one)

```bash
supabase link --project-ref YOUR_REF
supabase db push
supabase db seed
supabase functions deploy ingest --no-verify-jwt
```

Then set `INGEST_URL=https://YOUR_REF.supabase.co/functions/v1/ingest` (and `INGEST_KEY`) in the
repo-root `.env` so the simulator mirrors every tick here as well as to the local plant.

The summit demo does not require any of this. The local plant on `:8787` is the live path.
