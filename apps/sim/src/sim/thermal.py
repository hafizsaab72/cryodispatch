from __future__ import annotations

import math
from typing import Literal

DH_OVER_R = 10_000.0  # USP ΔH/R ≈ 83.144 kJ/mol / 8.3144 J
STABLE_SENTINEL = 9999.0


def t_eq(
    t_set: float,
    door: float,
    health: float,
    t_amb: float = 24.0,
    alpha_d: float = 6.5,
    alpha_h: float = 4.0,
    alpha_a: float = 0.04,
) -> float:
    """Equilibrium air temperature of the cabinet (Newton / RC plant)."""
    return t_set + alpha_d * door + alpha_h * (1.0 - health) + alpha_a * (t_amb - t_set)


def step_temperature(t: float, teq: float, tau_min: float, dt_min: float) -> float:
    if tau_min <= 0:
        return teq
    return teq + (t - teq) * math.exp(-dt_min / tau_min)


def minutes_to_breach(t: float, teq: float, t_th: float, tau_min: float) -> tuple[float, Literal["warming", "stable", "breached"]]:
    if t >= t_th:
        return 0.0, "breached"
    if teq <= t_th:
        return STABLE_SENTINEL, "stable"
    ratio = (t_th - teq) / (t - teq)
    if ratio <= 0:
        return 0.0, "breached"
    t_star = -tau_min * math.log(ratio)
    return max(0.0, t_star), "warming"


def minutes_to_freeze(t: float, teq: float, freeze_th: float, tau_min: float) -> float:
    """Time to hit the freeze rail when the cabinet is cooling below freeze_th."""
    if t <= freeze_th:
        return 0.0
    if teq >= freeze_th:
        return STABLE_SENTINEL
    ratio = (freeze_th - teq) / (t - teq)
    if ratio <= 0:
        return 0.0
    return max(0.0, -tau_min * math.log(ratio))


def predicted_t(t: float, teq: float, tau_min: float, horizon_min: float) -> float:
    return teq + (t - teq) * math.exp(-horizon_min / max(tau_min, 1e-6))


def slope_c_per_min(history: list[tuple[float, float]]) -> float | None:
    """history: list of (t_min, temperature). Last N points."""
    if len(history) < 2:
        return None
    t0, y0 = history[0]
    t1, y1 = history[-1]
    dt = t1 - t0
    if abs(dt) < 1e-9:
        return None
    return (y1 - y0) / dt


def mkt_c(temps_c: list[float]) -> float | None:
    if not temps_c:
        return None
    acc = 0.0
    for tc in temps_c:
        tk = tc + 273.15
        acc += math.exp(-DH_OVER_R / tk)
    mean = acc / len(temps_c)
    if mean <= 0:
        return None
    tk = DH_OVER_R / -math.log(mean)
    return tk - 273.15


def remaining_efficacy_pct(mkt: float, elapsed_min: float, t_ref_c: float = 5.0, k_ref: float = 4e-4) -> float:
    """Illustrative first-order loss. Not a release decision."""
    t_mkt = mkt + 273.15
    t_ref = t_ref_c + 273.15
    k = k_ref * math.exp(DH_OVER_R * (1.0 / t_ref - 1.0 / t_mkt))
    eta = 100.0 * math.exp(-k * elapsed_min)
    return max(0.0, min(100.0, eta))


def risk_score(minutes: float, eta: float | None, door: float) -> float:
    u = 1.0 - min(max(minutes / 30.0, 0.0), 1.0)
    efficacy_term = 0.0 if eta is None else (1.0 - eta / 100.0)
    return 100.0 * (0.55 * u + 0.30 * efficacy_term + 0.15 * door)
