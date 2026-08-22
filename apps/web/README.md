# apps/web — command centre

Vite + React wall display: floor map of 24 assets, the time-to-breach gauge with an explicit
in-band chip, the alert/dispatch rail, the demo trigger buttons, and the Chain of Cold Custody PDF
(generated in the browser with jsPDF).

```bash
pnpm install                    # from the repo root
cd apps/sim && .venv/bin/python -m sim   # start the plant first, in another terminal
pnpm dev:web                    # http://localhost:5173
```

The dev server proxies `/api` and `/ingest` to `127.0.0.1:8787`, so no environment variable is
needed locally. Set `VITE_PLANT_URL` only when the plant runs on another host. State arrives over
SSE (`/api/events`); the app retries every 3 s if the plant is not up yet, so opening the browser
first is harmless.

```bash
pnpm --filter @cryodispatch/web typecheck
pnpm --filter @cryodispatch/web build
```

The header buttons (**Kill probe**, **Compressor fail**, **Second vault**, **Reset plant**) are the
demo controls; the plant does the deciding. Nothing here classifies a fault or picks a destination.
