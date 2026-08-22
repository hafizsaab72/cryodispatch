from sim.thermal import (
    MIN_SLOPE_SAMPLES,
    STABLE_SENTINEL,
    minutes_to_breach,
    minutes_to_freeze,
    remaining_efficacy_pct,
    slope_c_per_min,
    step_temperature,
    t_eq,
)


def test_compressor_derate_raises_teq_above_threshold():
    teq_ok = t_eq(4.0, door=0.0, health=1.0)
    teq_fail = t_eq(4.0, door=0.0, health=0.25)
    assert teq_ok < 6.0
    assert teq_fail > 6.0


def test_minutes_to_breach_jumps_while_air_still_legal():
    t_air = 4.2
    teq = t_eq(4.0, door=0.0, health=0.25)
    tau = 2.0
    t_star = minutes_to_breach(t_air, teq, 6.0, tau)
    assert 0 < t_star < 30
    assert t_air < 6.0


def test_stable_when_teq_below_threshold():
    t_star = minutes_to_breach(4.0, 4.2, 6.0, 2.0)
    assert t_star == STABLE_SENTINEL


def test_step_moves_toward_teq():
    t1 = step_temperature(4.0, 12.0, tau_min=2.0, dt_min=0.5)
    assert 4.0 < t1 < 12.0


def test_efficacy_is_bounded():
    eta = remaining_efficacy_pct(mkt=12.0, elapsed_min=5.0)
    assert 0 <= eta <= 100


def test_least_squares_slope_recovers_a_linear_ramp():
    # 0.4 °C/min plus small noise — the old 2-point estimator swung wildly.
    history = [(i * 0.1, 4.0 + 0.4 * i * 0.1 + ((-1) ** i) * 0.02) for i in range(20)]
    slope = slope_c_per_min(history)
    assert slope is not None
    assert 0.30 < slope < 0.50


def test_slope_needs_enough_samples():
    assert slope_c_per_min([(0.0, 4.0), (1.0, 5.0)]) is None
    assert MIN_SLOPE_SAMPLES == 5
    short = [(float(i), 4.0 + i) for i in range(MIN_SLOPE_SAMPLES - 1)]
    assert slope_c_per_min(short) is None


def test_slope_is_none_when_time_does_not_advance():
    history = [(1.0, 4.0 + i * 0.1) for i in range(10)]
    assert slope_c_per_min(history) is None


def test_minutes_to_freeze_is_finite_when_teq_is_below_the_rail():
    t_star = minutes_to_freeze(4.0, teq=-2.0, freeze_th=0.0, tau_min=2.0)
    assert 0 < t_star < 10
    assert minutes_to_freeze(4.0, teq=4.2, freeze_th=0.0, tau_min=2.0) == STABLE_SENTINEL
