# Pitch deck

`CryoDispatch.pptx` — 8 slides for ELCIA Tech Summit 2026, generated from `build-deck.cjs`.

The `.pptx` is a **build artefact**. It is only correct as long as it matches the script, so any
content change means editing `build-deck.cjs` and regenerating. `pptxgenjs` is deliberately not a
repo dependency; rebuild with a throwaway install:

```bash
mkdir -p /tmp/pptxgen && cd /tmp/pptxgen
npm install pptxgenjs@3 --no-fund --no-audit --ignore-scripts
NODE_PATH=/tmp/pptxgen/node_modules node <repo>/docs/pitch/build-deck.cjs
```

## Facts the deck asserts (keep in sync with the code)

Slide 6 quotes hold **0.468 kWh** vs move **0.220 kWh**, and names **`FREEZER_BLOOD_06`
(ICU satellite 2)** as the cascade target. Slide 5 states τ is compressed to ~2 min for the demo.
If `dispatch.py`, `hospital.py` or `docs/demo-script.md` change these, the deck must be rebuilt.

## Claims the deck must never make

No FDA / Part 11 certification or compliance, no WHO PQS prequalification, no NABH/NABL
accreditation, no eVIN replacement, and MKT never proves potency — in slide text *or* speaker
notes. Slide 7 states these as refusals, which is the only place they may appear.
