# Overview — what and where

CryoDispatch is a hospital cold-chain **plant** (not a dashboard) at
`/Users/hafizsaab/Documents/Personal/cryodispatch`. Tagline: **Predict. Dispatch. Prove.**
Built for ELCIA Tech Summit 2026 (10 Sep, The Oterra, Electronics City, Bangalore; theme
"Humans, Machines & Meaning 3.0"). Judges are industrial/electronics engineers.

It simulates 24 cold-storage assets over three floors and runs one loop end to end:
sense → classify fault → predict time-to-breach → dispatch stock with a certified nurse →
verify custody by QR → open a compressor ticket.

## Layout

| Path | Role |
| --- | --- |
| `apps/sim` | Python plant — simulator, thermal model, dispatcher, FastAPI + SSE on `:8787`. Live demo path. |
| `apps/web` | Command centre (Vite + React), port 5173, proxies `/api` and `/ingest` to the plant. |
| `apps/staff` | Expo staff app, three screens (`src/app/index`, `mission/[id]`, `scan`). |
| `packages/shared` | TypeScript wire types. |
| `supabase/` | Dedicated project `cefhoczywrycsbniywus` (ap-south-1). Fan-out of plant state; ingest is 410. |
| `docs/` | `how-to-run.md` + `how-to-run.html` (illustrated first-run), `architecture.md`, `demo-script.md`, `mqtt-schema.md`, `qr-stickers.html`, `firmware/`, `pitch/`. |

## Run

Illustrated walkthrough: `docs/how-to-run.md` / `docs/how-to-run.html`
(live: https://hafizsaab72.github.io/cryodispatch/).

```bash
cd apps/sim && .venv/bin/python -m sim          # plant first
pnpm dev:web                                    # http://localhost:5173
EXPO_PUBLIC_PLANT_URL=http://<LAN-IP>:8787 pnpm dev:staff
cd apps/sim && .venv/bin/pytest -q              # 67 tests
```

## Where the rest of this memory bank lives

`product-context.md` — problem, users, differentiators, compliance line.
`system-patterns.md` — architectural rules and invariants.
`tech-context.md` — exact stack and versions.
`active-context.md` — current state, recent work, what is still open.

Canonical public documents: `README.md`, `docs/how-to-run.md`, and `docs/architecture.md`.
Keep them and this bank consistent; do not duplicate their detail here.
