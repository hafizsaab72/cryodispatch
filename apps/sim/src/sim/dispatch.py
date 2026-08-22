from __future__ import annotations

from sim.hospital import ASSETS, AssetSpec


def distance_m(a: AssetSpec, b: AssetSpec) -> float:
    floor_m = abs(a.floor - b.floor) * 18.0
    dx = (a.map_x - b.map_x) * 0.45
    dy = (a.map_y - b.map_y) * 0.45
    return (dx * dx + dy * dy) ** 0.5 + floor_m


def same_band(src: AssetSpec, dst: AssetSpec) -> bool:
    if not src.band or not dst.band:
        return False
    # Blood may overflow into a 2–8°C walk-in; the product band (2–6) still governs.
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


def kwh_hold(health: float) -> float:
    """Energy to keep a degraded compressor running for 30 minutes."""
    duty = 0.55 + 0.4 * (1.0 - health)
    return round(1.1 * duty * 0.5, 3)


def kwh_move() -> float:
    """Door-open load at both ends plus destination pull-down."""
    return 0.22


def cascade_risk(free_after_l: float, other_need_l: float) -> float:
    """How badly this destination would block a second failing vault.

    1.0 when taking this move would leave too little headroom for the next
    vault at risk. Explainable on stage: we prefer a backup that can absorb
    two failures over one that can only absorb ours.
    """
    if other_need_l <= 0:
        return 0.0
    if free_after_l < other_need_l:
        return 1.0
    if free_after_l < other_need_l * 2:
        return 0.5
    return 0.1


def pick_backup(
    src: AssetSpec,
    remaining: dict[str, float],
    reserved: dict[str, float],
    need_l: float,
    other_need_l: float,
) -> AssetSpec | None:
    """Greedy destination choice. O(vaults), explainable, no solver."""
    candidates: list[tuple[float, str, AssetSpec]] = []
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
        cr = cascade_risk(free - need_l, other_need_l)
        cost = 3.0 * d + 2.0 * staff_eta + 1.0 * (1.0 - free_frac) + 2.0 * kwh_move() + 4.0 * cr
        candidates.append((cost, dst.asset_id, dst))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]
