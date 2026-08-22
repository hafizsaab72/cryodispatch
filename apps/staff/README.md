# Staff app (Expo 56)

Three screens: inbox → accept MOVE → scan QR (unit → source → dest). Wrong vault is a hard reject.

```bash
# From repo root. Phone must reach the laptop plant.
EXPO_PUBLIC_PLANT_URL=http://192.168.x.x:8787 pnpm dev:staff
```

On iOS simulator, camera can be skipped: type `UNIT:BAG-ONEG-01` then vault codes from `docs/qr-stickers.html`.
