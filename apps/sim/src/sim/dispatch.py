from __future__ import annotations

from dataclasses import dataclass

from sim.hospital import ASSETS, AssetSpec


def distance_m(a: AssetSpec, b: AssetSpec) -> float:
    floor_m = abs(a.floor - b.floor) * 18.0
    dx = (a.map_x - b.map_x) * 0.45
    dy = (a.map_y - b.map_y) * 0.45
    return (dx * dx + dy * dy) ** 0.5 + floor_m


def same_band(src: AssetSpec, dst: AssetSpec) -> bool:
    if not src.band or not dst.band:
        return False
    # blood can go to walk-in if walk-in is 2-8 and we accept 2-6 product
    if src.asset_class == "blood_rbc" and dst.asset_class in {"blood_rbc", "walkin_cold"}:
        return True
    if src.asset_class in {"vaccine_ilr", "insulin_ilr"} and dst.asset_class in {"vaccine_ilr", "insulin_ilr", "walkin_cold"}:
        return True
    return src.asset_class == dst.asset_class


def cert_for(asset_class: str) -> str:
    if asset_class in {"blood_rbc", "plasma_ffp", "platelet"}:
        return "blood"
    if asset_class in {"vaccine_ilr", "insulin_ilr", "walkin_cold"}:
        return "vaccine"
    return "maintenance"


@dataclass
class DispatchMove:
    from_asset: str
    to_asset: str
    unit_ids: list[str]
    staff_id: str
    staff_name: str
    distance_m: float
    eta_min: float
    kwh_hold_30m: float
    kwh_move: float
    cascade: bool
    ticket_parts: str = "start-relay, run-cap"


def kwh_hold(health: float) -> float:
    # sick compressor drawing ~1.1 kW at high duty for 0.5 h
    duty = 0.55 + 0.4 * (1.0 - health)
    return round(1.1 * duty * 0.5, 3)


def kwh_move() -> float:
    return 0.22  # door-open load + dest extra


def cascade_risk(dst_id: str, reserved: dict[str, float], remaining: dict[str, float], other_need_l: float) -> float:
    """1.0 if this dest is the only overflow left for another failing vault."""
    free = remaining.get(dst_id, 0.0) - reserved.get(dst_id, 0.0)
    if free < other_need_l:
        return 1.0
    # V7 (FREEZER_BLOOD_03) is shared overflow for V3 and V4
    if dst_id == "FREEZER_BLOOD_03":
        return 0.85
    return 0.1


def pick_backup(
    src: AssetSpec,
    remaining: dict[str, float],
    reserved: dict[str, float],
    need_l: float,
    other_need_l: float,
) -> AssetSpec | None:
    candidates: list[tuple[float, AssetSpec]] = []
    for dst in ASSETS:
        if dst.asset_id == src.asset_id or not dst.thermal:
            continue
        if not same_band(src, dst):
            continue
        free = remaining.get(dst.asset_id, dst.capacity_l) - reserved.get(dst.asset_id, 0.0)
        if free < need_l:
            continue
        d = distance_m(src, dst)
        staff_eta = 1.5 + 0.4 * abs(src.floor - dst.floor)
        free_frac = free / max(dst.capacity_l, 1.0)
        cr = cascade_risk(dst.asset_id, reserved, remaining, other_need_l)
        cost = 3.0 * d + 2.0 * staff_eta + 1.0 * (1.0 - free_frac) + 2.0 * kwh_move() + 4.0 * cr
        candidates.append((cost, dst))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]
