from sim.thermal import minutes_to_breach, remaining_efficacy_pct, step_temperature, t_eq


def test_compressor_derate_raises_teq_above_threshold():
    teq_ok = t_eq(4.0, door=0.0, health=1.0)
    teq_fail = t_eq(4.0, door=0.0, health=0.25)
    assert teq_ok < 6.0
    assert teq_fail > 6.0


def test_minutes_to_breach_jumps_while_air_still_legal():
    t_air = 4.2
    teq = t_eq(4.0, door=0.0, health=0.25)
    tau = 2.0
    t_star, mode = minutes_to_breach(t_air, teq, 6.0, tau)
    assert mode == "warming"
    assert 0 < t_star < 30
    assert t_air < 6.0


def test_stable_when_teq_below_threshold():
    t_star, mode = minutes_to_breach(4.0, 4.2, 6.0, 2.0)
    assert mode == "stable"
    assert t_star > 1000


def test_step_moves_toward_teq():
    t1 = step_temperature(4.0, 12.0, tau_min=2.0, dt_min=0.5)
    assert 4.0 < t1 < 12.0


def test_efficacy_is_bounded():
    eta = remaining_efficacy_pct(mkt=12.0, elapsed_min=5.0)
    assert 0 <= eta <= 100
