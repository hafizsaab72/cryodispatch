# apps/staff — staff app (Expo SDK 56)

Three screens: inbox of open MOVEs → the locked plan with **ACCEPT MOVE** → QR custody scan
(unit → source vault → destination vault). A wrong vault is a hard reject, logged into the custody
record. Runs in Expo Go; it polls `/api/state` every 2 seconds and buzzes once per new MOVE.

```bash
# From the repo root. The phone must be able to reach the laptop.
EXPO_PUBLIC_PLANT_URL=http://192.168.x.x:8787 pnpm dev:staff
```

The inbox prints the plant URL it is using, so a wrong LAN IP is visible rather than silent.
Default is `http://127.0.0.1:8787`.

Without a camera (simulator, or a phone that will not grant permission), type the codes instead:
`UNIT:BAG-ONEG-01`, then `VAULT:FREEZER_BLOOD_04`, then `VAULT:FREEZER_BLOOD_03`. The printable
cards are in `docs/qr-stickers.html`.

`expo-constants`, `expo-linking` and `react-native-gesture-handler` are declared but not imported
by any screen: they are peer dependencies of `expo-router` and of the drawer layout underneath it.
Do not remove them.
