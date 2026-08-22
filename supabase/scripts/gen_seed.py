"""Regenerate supabase/seed.sql from hospital.py. Run from repo root:

    PYTHONPATH=apps/sim/src python supabase/scripts/gen_seed.py
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/sim/src"))

from sim.hospital import ASSETS, HOSPITAL, INVENTORY, SITE_ID, STAFF  # noqa: E402


def sql_str(v: object) -> str:
    if v is None:
        return "null"
    return "'" + str(v).replace("'", "''") + "'"


def n(v: object) -> str:
    return "null" if v is None else str(v)


def main() -> None:
    lines: list[str] = [
        "-- Generated from apps/sim/src/sim/hospital.py — run supabase/scripts/gen_seed.py to refresh.",
        f"insert into public.plant_meta (site_id, hospital, tick) values ({sql_str(SITE_ID)}, {sql_str(HOSPITAL)}, 0)",
        "on conflict (site_id) do update set hospital = excluded.hospital;",
        "",
        "insert into public.staff (id, name, cert, floor, busy) values",
    ]
    lines.append(
        ",\n".join(
            f"  ({sql_str(s.id)}, {sql_str(s.name)}, {sql_str(s.cert)}, {s.floor}, false)" for s in STAFF
        )
    )
    lines.append("on conflict (id) do nothing;")
    lines.append("")
    lines.append(
        "insert into public.inventory "
        "(unit_id, asset_id, home_asset_id, product_name, blood_type, lot, expiry, volume_l, temp_band) values"
    )
    inv = []
    for u in INVENTORY:
        inv.append(
            f"  ({sql_str(u.unit_id)}, {sql_str(u.asset_id)}, {sql_str(u.asset_id)}, "
            f"{sql_str(u.product_name)}, {sql_str(u.blood_type)}, {sql_str(u.lot)}, "
            f"{sql_str(u.expiry)}, {u.volume_l}, {sql_str(u.temp_band)})"
        )
    lines.append(",\n".join(inv))
    lines.append("on conflict (unit_id) do nothing;")
    lines.append("")
    lines.append("insert into public.asset_state (")
    lines.append("  asset_id, asset_class, label, location, floor, zone, temperature, door_status,")
    lines.append("  compressor_health, battery_pct, probe_online, map_x, map_y, topic,")
    lines.append("  band_low_c, band_high_c, setpoint_c, capacity_l, used_l, reserved_l, free_l,")
    lines.append("  baseline_used_l, sensor_id, demo_role, model_mode, fault_class, minutes_to_breach, recent_c")
    lines.append(") values")
    rows = []
    for a in ASSETS:
        t = a.band.setpoint if a.band else None
        low = a.band.low if a.band else None
        high = a.band.high if a.band else None
        setp = a.band.setpoint if a.band else None
        used = a.baseline_used_l + sum(u.volume_l for u in INVENTORY if u.asset_id == a.asset_id)
        free = max(0.0, a.capacity_l - used)
        mode = "stable" if a.thermal else "location"
        rows.append(
            "  ("
            f"{sql_str(a.asset_id)}, {sql_str(a.asset_class)}, {sql_str(a.label)}, {sql_str(a.location)}, "
            f"{a.floor}, {sql_str(a.zone)}, {n(t)}, 'CLOSED', 1.0, 97.0, true, {a.map_x}, {a.map_y}, "
            f"{sql_str(f'cryo/{SITE_ID}/assets/{a.asset_id}/telemetry')}, "
            f"{n(low)}, {n(high)}, {n(setp)}, {a.capacity_l}, {used}, 0, {free}, "
            f"{a.baseline_used_l}, {sql_str(a.sensor_id) if a.sensor_id else 'null'}, {sql_str(a.demo_role)}, "
            f"{sql_str(mode)}, 'NONE', 9999, '[]'"
            ")"
        )
    lines.append(",\n".join(rows))
    lines.append("on conflict (asset_id) do nothing;")
    dest = ROOT / "supabase/seed.sql"
    dest.write_text("\n".join(lines) + "\n")
    print(f"wrote {dest} ({len(ASSETS)} assets, {len(STAFF)} staff, {len(INVENTORY)} units)")


if __name__ == "__main__":
    main()
