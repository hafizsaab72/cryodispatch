insert into public.staff (id, name, cert, floor, busy) values
  ('nurse-rao', 'Nurse Rao', 'blood', 1, false),
  ('tech-mehta', 'Tech Mehta', 'vaccine', 2, false),
  ('engr-iyer', 'Engr Iyer', 'maintenance', 1, false)
on conflict (id) do nothing;

insert into public.inventory (unit_id, asset_id, product_name, blood_type, lot, expiry, volume_l, temp_band) values
  ('BAG-ONEG-01', 'FREEZER_BLOOD_04', 'Packed RBC', 'O-neg', 'B24-4411', '2026-09-04', 0.35, '2-6'),
  ('BAG-ONEG-02', 'FREEZER_BLOOD_04', 'Packed RBC', 'O-neg', 'B24-4412', '2026-09-05', 0.35, '2-6'),
  ('BAG-APOS-01', 'FREEZER_BLOOD_04', 'Packed RBC', 'A-pos', 'B24-4501', '2026-09-08', 0.35, '2-6'),
  ('BAG-APOS-02', 'FREEZER_BLOOD_04', 'Packed RBC', 'A-pos', 'B24-4502', '2026-09-08', 0.35, '2-6'),
  ('BAG-BPOS-01', 'FREEZER_BLOOD_05', 'Packed RBC', 'B-pos', 'B24-4601', '2026-09-03', 0.35, '2-6'),
  ('BAG-OPOS-01', 'FREEZER_BLOOD_05', 'Packed RBC', 'O-pos', 'B24-4701', '2026-09-06', 0.35, '2-6')
on conflict (unit_id) do nothing;
