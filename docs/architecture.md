# CryoDispatch architecture (one-pager)

```
[ ESP32 or Python sim ] --HTTP POST /ingest (MQTT JSON)--> [ Plant brain ]
                                                               |
                         lumped thermal + greedy dispatch + LWT taxonomy
                                                               |
                                                               v
                                              asset_state / alerts / missions
                                              /                         \
                                   SSE / Realtime                    SSE / Realtime
                                          v                                  v
                               Command Center (Vite)              Staff (Expo, 3 screens)
                               floor map · T_eq · PDF             Accept · QR · reject
```

Live demo path is local `:8787` so venue Wi-Fi cannot kill a broker. Hosted path is a **new** Supabase project + `functions/ingest`. Same payload. Dashboard never subscribes to MQTT.

Hardware drop-in: `docs/firmware/cryodispatch_esp32.ino`.
