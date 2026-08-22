-- Generated from apps/sim/src/sim/hospital.py — do not hand-edit.
insert into public.plant_meta (site_id, hospital, tick) values ('elcia-emc', 'ELCIA Medical Centre', 0)
on conflict (site_id) do update set hospital = excluded.hospital;

insert into public.staff (id, name, cert, floor, busy) values
  ('nurse-rao', 'Nurse Rao', 'blood', 1, false),
  ('nurse-dsouza', 'Nurse D''Souza', 'blood', 2, false),
  ('tech-mehta', 'Tech Mehta', 'vaccine', 2, false),
  ('engr-iyer', 'Engr Iyer', 'maintenance', 1, false)
on conflict (id) do nothing;

insert into public.inventory (unit_id, asset_id, home_asset_id, product_name, blood_type, lot, expiry, volume_l, temp_band) values
  ('BAG-ONEG-01', 'FREEZER_BLOOD_04', 'FREEZER_BLOOD_04', 'Packed RBC', 'O-neg', 'B24-4411', '2026-09-04', 0.35, '2-6'),
  ('BAG-ONEG-02', 'FREEZER_BLOOD_04', 'FREEZER_BLOOD_04', 'Packed RBC', 'O-neg', 'B24-4412', '2026-09-05', 0.35, '2-6'),
  ('BAG-APOS-01', 'FREEZER_BLOOD_04', 'FREEZER_BLOOD_04', 'Packed RBC', 'A-pos', 'B24-4501', '2026-09-08', 0.35, '2-6'),
  ('BAG-APOS-02', 'FREEZER_BLOOD_04', 'FREEZER_BLOOD_04', 'Packed RBC', 'A-pos', 'B24-4502', '2026-09-08', 0.35, '2-6'),
  ('BAG-BPOS-01', 'FREEZER_BLOOD_05', 'FREEZER_BLOOD_05', 'Packed RBC', 'B-pos', 'B24-4601', '2026-09-03', 0.35, '2-6'),
  ('BAG-OPOS-01', 'FREEZER_BLOOD_05', 'FREEZER_BLOOD_05', 'Packed RBC', 'O-pos', 'B24-4701', '2026-09-06', 0.35, '2-6'),
  ('BAG-ONEG-03', 'FREEZER_BLOOD_01', 'FREEZER_BLOOD_01', 'Packed RBC', 'O-neg', 'B24-4101', '2026-09-10', 0.35, '2-6'),
  ('VAX-PENTA-01', 'ILR_VAX_02', 'ILR_VAX_02', 'Pentavalent', null, 'UIP-8821', '2027-01-12', 0.4, '2-8'),
  ('INS-HUM-01', 'ILR_INSULIN_01', 'ILR_INSULIN_01', 'Human insulin', null, 'INS-1902', '2026-12-01', 0.25, '2-8'),
  ('INS-HUM-02', 'ILR_INSULIN_03', 'ILR_INSULIN_03', 'Human insulin', null, 'INS-1908', '2026-12-01', 0.25, '2-8')
on conflict (unit_id) do nothing;

insert into public.asset_state (
  asset_id, asset_class, label, location, floor, zone, temperature, door_status,
  compressor_health, battery_pct, probe_online, map_x, map_y, topic,
  band_low_c, band_high_c, setpoint_c, capacity_l, used_l, reserved_l, free_l,
  baseline_used_l, sensor_id, demo_role, model_mode, fault_class, minutes_to_breach, recent_c
) values
  ('FREEZER_BLOOD_01', 'blood_rbc', 'RBC Vault 1', 'Floor 1 — Blood Bank A', 1, 'blood-a', 4.0, 'CLOSED', 1.0, 97.0, true, 18, 28, 'cryo/elcia-emc/assets/FREEZER_BLOOD_01/telemetry', 2.0, 6.0, 4.0, 21.0, 12.95, 0, 8.05, 12.6, 'DDL-B01', null, 'stable', 'NONE', 9999, '[]'),
  ('FREEZER_BLOOD_02', 'blood_rbc', 'RBC Vault 2', 'Floor 1 — Blood Bank A', 1, 'blood-a', 4.0, 'CLOSED', 1.0, 97.0, true, 32, 28, 'cryo/elcia-emc/assets/FREEZER_BLOOD_02/telemetry', 2.0, 6.0, 4.0, 21.0, 15.4, 0, 5.6, 15.4, 'DDL-B02', null, 'stable', 'NONE', 9999, '[]'),
  ('FREEZER_BLOOD_03', 'blood_rbc', 'RBC Vault 3 · backup', 'Floor 1 — Blood Bank B', 1, 'blood-b', 4.0, 'CLOSED', 1.0, 97.0, true, 68, 30, 'cryo/elcia-emc/assets/FREEZER_BLOOD_03/telemetry', 2.0, 6.0, 4.0, 19.6, 17.8, 0, 1.8000000000000007, 17.8, 'DDL-B03', 'v7', 'stable', 'NONE', 9999, '[]'),
  ('FREEZER_BLOOD_04', 'blood_rbc', 'RBC Vault 4 · primary', 'Floor 1 — Blood Bank B', 1, 'blood-b', 4.0, 'CLOSED', 1.0, 97.0, true, 82, 30, 'cryo/elcia-emc/assets/FREEZER_BLOOD_04/telemetry', 2.0, 6.0, 4.0, 14.0, 1.4, 0, 12.6, 0.0, 'DDL-B04', 'v3', 'stable', 'NONE', 9999, '[]'),
  ('FREEZER_BLOOD_05', 'blood_rbc', 'ICU satellite 1', 'Floor 2 — ICU Cold', 2, 'icu', 4.0, 'CLOSED', 1.0, 97.0, true, 22, 62, 'cryo/elcia-emc/assets/FREEZER_BLOOD_05/telemetry', 2.0, 6.0, 4.0, 8.4, 0.7, 0, 7.7, 0.0, 'DDL-B05', 'v4', 'stable', 'NONE', 9999, '[]'),
  ('FREEZER_BLOOD_06', 'blood_rbc', 'ICU satellite 2 · cascade', 'Floor 2 — ICU Cold', 2, 'icu', 4.0, 'CLOSED', 1.0, 97.0, true, 36, 62, 'cryo/elcia-emc/assets/FREEZER_BLOOD_06/telemetry', 2.0, 6.0, 4.0, 8.4, 0.0, 0, 8.4, 0.0, 'DDL-B06', 'v8', 'stable', 'NONE', 9999, '[]'),
  ('ILR_VAX_01', 'vaccine_ilr', 'ILR Vaccines 1', 'Floor 2 — Pharmacy', 2, 'pharm', 5.0, 'CLOSED', 1.0, 97.0, true, 70, 58, 'cryo/elcia-emc/assets/ILR_VAX_01/telemetry', 2.0, 8.0, 5.0, 30, 0.0, 0, 30.0, 0.0, 'DDL-V01', null, 'stable', 'NONE', 9999, '[]'),
  ('ILR_VAX_02', 'vaccine_ilr', 'ILR Vaccines 2 · probe', 'Floor 2 — Pharmacy', 2, 'pharm', 5.0, 'CLOSED', 1.0, 97.0, true, 84, 58, 'cryo/elcia-emc/assets/ILR_VAX_02/telemetry', 2.0, 8.0, 5.0, 30, 0.4, 0, 29.6, 0.0, 'DDL-V02', 'lwt', 'stable', 'NONE', 9999, '[]'),
  ('ILR_VAX_03', 'vaccine_ilr', 'ILR Vaccines 3', 'Floor 2 — Pharmacy', 2, 'pharm', 5.0, 'CLOSED', 1.0, 97.0, true, 70, 68, 'cryo/elcia-emc/assets/ILR_VAX_03/telemetry', 2.0, 8.0, 5.0, 30, 0.0, 0, 30.0, 0.0, 'DDL-V03', null, 'stable', 'NONE', 9999, '[]'),
  ('ILR_VAX_04', 'vaccine_ilr', 'ILR Vaccines 4', 'Floor 3 — OT prep', 3, 'ot', 5.0, 'CLOSED', 1.0, 97.0, true, 20, 84, 'cryo/elcia-emc/assets/ILR_VAX_04/telemetry', 2.0, 8.0, 5.0, 20, 0.0, 0, 20.0, 0.0, 'DDL-V04', null, 'stable', 'NONE', 9999, '[]'),
  ('ILR_VAX_05', 'vaccine_ilr', 'ILR Vaccines 5', 'Floor 3 — OT prep', 3, 'ot', 5.0, 'CLOSED', 1.0, 97.0, true, 34, 84, 'cryo/elcia-emc/assets/ILR_VAX_05/telemetry', 2.0, 8.0, 5.0, 20, 0.0, 0, 20.0, 0.0, 'DDL-V05', null, 'stable', 'NONE', 9999, '[]'),
  ('ILR_INSULIN_01', 'insulin_ilr', 'Insulin vault 1', 'Floor 2 — Pharmacy', 2, 'pharm', 5.0, 'CLOSED', 1.0, 97.0, true, 56, 58, 'cryo/elcia-emc/assets/ILR_INSULIN_01/telemetry', 2.0, 8.0, 5.0, 18, 0.25, 0, 17.75, 0.0, 'DDL-I01', null, 'stable', 'NONE', 9999, '[]'),
  ('ILR_INSULIN_02', 'insulin_ilr', 'Insulin vault 2', 'Floor 2 — Pharmacy', 2, 'pharm', 5.0, 'CLOSED', 1.0, 97.0, true, 56, 68, 'cryo/elcia-emc/assets/ILR_INSULIN_02/telemetry', 2.0, 8.0, 5.0, 18, 0.0, 0, 18.0, 0.0, 'DDL-I02', null, 'stable', 'NONE', 9999, '[]'),
  ('ILR_INSULIN_03', 'insulin_ilr', 'Insulin vault 3', 'Floor 1 — Ward store', 1, 'ward', 5.0, 'CLOSED', 1.0, 97.0, true, 18, 38, 'cryo/elcia-emc/assets/ILR_INSULIN_03/telemetry', 2.0, 8.0, 5.0, 12, 0.25, 0, 11.75, 0.0, 'DDL-I03', null, 'stable', 'NONE', 9999, '[]'),
  ('PLT_AGIT_01', 'platelet', 'Platelet agitator 1', 'Floor 1 — Blood Bank A', 1, 'blood-a', 22.0, 'CLOSED', 1.0, 97.0, true, 18, 46, 'cryo/elcia-emc/assets/PLT_AGIT_01/telemetry', 20.0, 24.0, 22.0, 8, 0.0, 0, 8.0, 0.0, 'DDL-P01', null, 'stable', 'NONE', 9999, '[]'),
  ('PLT_AGIT_02', 'platelet', 'Platelet agitator 2', 'Floor 1 — Blood Bank A', 1, 'blood-a', 22.0, 'CLOSED', 1.0, 97.0, true, 32, 46, 'cryo/elcia-emc/assets/PLT_AGIT_02/telemetry', 20.0, 24.0, 22.0, 8, 0.0, 0, 8.0, 0.0, 'DDL-P02', null, 'stable', 'NONE', 9999, '[]'),
  ('PLASMA_FFP_01', 'plasma_ffp', 'Plasma freezer 1', 'Floor 1 — Blood Bank B', 1, 'blood-b', -35.0, 'CLOSED', 1.0, 97.0, true, 68, 42, 'cryo/elcia-emc/assets/PLASMA_FFP_01/telemetry', -40.0, -30.0, -35.0, 36, 0.0, 0, 36.0, 0.0, 'DDL-F01', null, 'stable', 'NONE', 9999, '[]'),
  ('PLASMA_FFP_02', 'plasma_ffp', 'Plasma freezer 2', 'Floor 3 — OT backup', 3, 'ot', -35.0, 'CLOSED', 1.0, 97.0, true, 80, 84, 'cryo/elcia-emc/assets/PLASMA_FFP_02/telemetry', -40.0, -30.0, -35.0, 36, 0.0, 0, 36.0, 0.0, 'DDL-F02', null, 'stable', 'NONE', 9999, '[]'),
  ('WALKIN_COLD_01', 'walkin_cold', 'Walk-in cold 1', 'Floor 1 — Central cold', 1, 'central', 5.0, 'CLOSED', 1.0, 97.0, true, 50, 28, 'cryo/elcia-emc/assets/WALKIN_COLD_01/telemetry', 2.0, 8.0, 5.0, 120, 0.0, 0, 120.0, 0.0, 'DDL-W01', null, 'stable', 'NONE', 9999, '[]'),
  ('WALKIN_COLD_02', 'walkin_cold', 'Walk-in cold 2 · overflow', 'Floor 3 — Central overflow', 3, 'overflow', 5.0, 'CLOSED', 1.0, 97.0, true, 50, 90, 'cryo/elcia-emc/assets/WALKIN_COLD_02/telemetry', 2.0, 8.0, 5.0, 120, 0.0, 0, 120.0, 0.0, 'DDL-W02', null, 'stable', 'NONE', 9999, '[]'),
  ('CART_CRASH_01', 'crash_cart', 'Crash cart A', 'Floor 3 — OT corridor', 3, 'ot', null, 'CLOSED', 1.0, 97.0, true, 12, 90, 'cryo/elcia-emc/assets/CART_CRASH_01/telemetry', null, null, null, 21.0, 0.0, 0, 21.0, 0.0, null, null, 'location', 'NONE', 9999, '[]'),
  ('CART_CRASH_02', 'crash_cart', 'Crash cart B', 'Floor 2 — ICU bay', 2, 'icu', null, 'CLOSED', 1.0, 97.0, true, 12, 68, 'cryo/elcia-emc/assets/CART_CRASH_02/telemetry', null, null, null, 21.0, 0.0, 0, 21.0, 0.0, null, null, 'location', 'NONE', 9999, '[]'),
  ('CART_CRASH_03', 'crash_cart', 'Crash cart C', 'Floor 1 — ER', 1, 'er', null, 'CLOSED', 1.0, 97.0, true, 88, 44, 'cryo/elcia-emc/assets/CART_CRASH_03/telemetry', null, null, null, 21.0, 0.0, 0, 21.0, 0.0, null, null, 'location', 'NONE', 9999, '[]'),
  ('CART_CRASH_04', 'crash_cart', 'Crash cart D', 'Floor 2 — Ward 2B', 2, 'ward', null, 'CLOSED', 1.0, 97.0, true, 88, 68, 'cryo/elcia-emc/assets/CART_CRASH_04/telemetry', null, null, null, 21.0, 0.0, 0, 21.0, 0.0, null, null, 'location', 'NONE', 9999, '[]')
on conflict (asset_id) do nothing;

