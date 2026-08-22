# Hosted path

Create a **new** Supabase project (do not reuse Lensora). Then:

```bash
supabase link --project-ref YOUR_REF
supabase db push
supabase db seed
supabase functions deploy ingest --no-verify-jwt
```

Set `INGEST_URL=https://YOUR_REF.supabase.co/functions/v1/ingest` in the repo `.env` so the simulator also POSTs ticks.

Realtime: `asset_state`, `alerts`, `missions`.

The summit demo does **not** require this. The local plant on `:8787` is the live path.
