import pytest

from sim.dispatch import cascade_risk, pick_backup
from sim.hospital import ASSETS, spec_by_id
from sim.plant import Plant


def _missions_from(plant: Plant, asset_id: str) -> list[dict]:
    return [m for m in plant.missions if m["from_asset"] == asset_id]


def test_probe_dead_tickets_but_never_moves_stock():
    plant = Plant(demo_tau_min=2.0, tick_sec=1.0)
    plant.anomaly("ILR_VAX_02", "lwt")
    processed = plant.assets["ILR_VAX_02"].processed
    assert processed.fault_class == "PROBE_DEAD"
    assert processed.model_mode == "probe_dead"
    assert _missions_from(plant, "ILR_VAX_02") == []
    assert [t for t in plant.tickets if t["asset_id"] == "ILR_VAX_02"]


def test_probe_dead_while_out_of_band_is_both_and_does_move():
    plant = Plant()
    a = plant.assets["FREEZER_BLOOD_04"]
    a.temperature = 9.5  # already hot when the probe dies
    plant.anomaly("FREEZER_BLOOD_04", "lwt")
    assert a.processed.fault_class == "BOTH"
    assert _missions_from(plant, "FREEZER_BLOOD_04")


def test_compressor_predicts_breach_while_air_still_in_band():
    plant = Plant(demo_tau_min=2.0, tick_sec=1.0)
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    a = plant.assets["FREEZER_BLOOD_04"]
    band = a.spec.band
    assert band is not None
    assert a.processed.t_eq_c > band.high, "equilibrium must cross the threshold"
    assert band.low <= a.temperature <= band.high, "air must still be legal at trigger"
    assert 0 < a.processed.minutes_to_breach < 30
    assert a.processed.model_mode == "warming"


def test_compressor_opens_move_to_nearest_backup():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    missions = _missions_from(plant, "FREEZER_BLOOD_04")
    assert len(missions) == 1
    m = missions[0]
    assert m["to_asset"] == "FREEZER_BLOOD_03"
    assert len(m["units"]) == 4
    assert m["staff_name"] == "Nurse Rao"
    assert m["ticket"]["kwh_hold_30m"] > m["ticket"]["kwh_move"]


def test_second_failure_cascades_because_backup_is_full():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    first = _missions_from(plant, "FREEZER_BLOOD_04")[0]
    backup = plant.assets[first["to_asset"]]
    need_second = sum(
        u["volume_l"] for u in plant.inventory if u["asset_id"] == "FREEZER_BLOOD_05"
    )
    assert backup.reserved_l > 0, "first move must hold litres at the destination"
    assert backup.free_l < need_second, "backup must be too full for a second vault"

    plant.anomaly("FREEZER_BLOOD_05", "compressor")
    second = _missions_from(plant, "FREEZER_BLOOD_05")
    assert len(second) == 1
    assert second[0]["to_asset"] != first["to_asset"]
    assert second[0]["to_asset"] == "FREEZER_BLOOD_06"


def test_cascade_risk_flags_a_backup_that_cannot_take_two():
    assert cascade_risk(free_after_l=0.4, other_need_l=0.7) == 1.0
    assert cascade_risk(free_after_l=5.0, other_need_l=0.7) == 0.1
    assert cascade_risk(free_after_l=0.4, other_need_l=0.0) == 0.0


def test_staff_certification_is_a_hard_requirement():
    plant = Plant()
    # Both blood couriers busy: a vaccine tech must not be handed blood,
    # and an unstaffed MOVE must not be created.
    for s in plant.staff:
        if s["cert"] == "blood":
            s["busy"] = True
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    assert _missions_from(plant, "FREEZER_BLOOD_04") == []
    assert [t for t in plant.tickets if t["asset_id"] == "FREEZER_BLOOD_04"]
    assert any("certified courier" in al["message"] for al in plant.alerts)


def test_thermal_then_probe_dead_does_not_open_a_second_mission():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_05", "compressor")
    first = _missions_from(plant, "FREEZER_BLOOD_05")
    assert len(first) == 1
    reserved = plant.assets[first[0]["to_asset"]].reserved_l
    plant.assets["FREEZER_BLOOD_05"].temperature = 9.0
    plant.anomaly("FREEZER_BLOOD_05", "lwt")
    assert plant.assets["FREEZER_BLOOD_05"].processed.fault_class == "BOTH"
    second = _missions_from(plant, "FREEZER_BLOOD_05")
    assert len(second) == 1
    assert plant.assets[first[0]["to_asset"]].reserved_l == reserved
    assert any(ev["action"] == "mission.escalate" for ev in plant.audit)


def test_measured_slope_is_least_squares_not_two_point_noise():
    plant = Plant(demo_tau_min=2.0, tick_sec=1.0)
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    for _ in range(40):
        plant.step()
    slope = plant.assets["FREEZER_BLOOD_04"].processed.dT_dt_c_per_min
    assert slope is not None
    assert slope > 0.05


def test_lock_is_reentrant_from_a_snapshot_listener():
    plant = Plant()
    seen = {"n": 0}

    def peek(_ev):
        plant.snapshot()
        seen["n"] += 1

    plant.subscribe(peek)
    plant.step()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    assert seen["n"] >= 1


def test_door_open_is_an_event_not_a_move_when_tau_is_realistic():
    plant = Plant(demo_tau_min=30.0, tick_sec=1.0)
    plant.anomaly("ILR_VAX_01", "door")
    a = plant.assets["ILR_VAX_01"]
    assert a.processed.fault_class == "DOOR_OPEN"
    assert a.processed.minutes_to_breach >= 5.0
    assert _missions_from(plant, "ILR_VAX_01") == []
    assert any(al["kind"] == "DOOR_OPEN" and al["severity"] == "warn" for al in plant.alerts)
    a.door = 0.0
    teq = a.spec.band.setpoint if a.spec.band else 5.0
    # Recompute with the door closed and health still 1.0.
    from sim.thermal import t_eq

    a.processed = plant._process(a, t_eq(a.spec.band.setpoint, a.door, a.health), 30.0)
    plant._maybe_alert(a)
    assert a.processed.fault_class == "NONE"


def test_door_open_escalates_when_countdown_is_short():
    plant = Plant(demo_tau_min=2.0, tick_sec=1.0)
    plant.anomaly("ILR_VAX_01", "door")
    a = plant.assets["ILR_VAX_01"]
    assert a.processed.fault_class == "THERMAL_EXCURSION"
    assert a.processed.minutes_to_breach < 5.0


def test_breach_direction_names_the_freeze_rail():
    plant = Plant()
    a = plant.assets["ILR_VAX_01"]
    a.temperature = 4.0
    p = plant._process(a, teq=-2.0, tau=2.0)
    assert p.breach_direction == "freeze"
    assert p.breach_threshold_c == 0.0
    assert 0 < p.minutes_to_breach < 30


def test_reset_all_restores_battery_and_keeps_tick_and_audit():
    plant = Plant()
    plant.tick = 12
    plant.assets["FREEZER_BLOOD_04"].battery = 90.0
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    audit_len = len(plant.audit)
    plant.reset_all()
    assert plant.assets["FREEZER_BLOOD_04"].battery == 97.0
    assert plant.tick == 12
    assert len(plant.audit) == audit_len + 1


def test_scan_after_completion_emits_a_scan_event():
    plant = Plant()
    events: list[dict] = []
    plant.subscribe(events.append)
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = _missions_from(plant, "FREEZER_BLOOD_04")[0]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    plant.scan_mission(m["id"], f"VAULT:{m['to_asset']}")
    before = len(events)
    again = plant.scan_mission(m["id"], "VAULT:WALKIN_COLD_01")
    assert again["status"] == "complete"
    assert again["last_reject"] is None
    assert any(e.get("type") == "scan" for e in events[before:])


def test_unknown_anomaly_kind_names_the_valid_kinds():
    plant = Plant()
    with pytest.raises(ValueError, match="compressor"):
        plant.anomaly("ILR_VAX_01", "nope")


def test_custody_events_never_invent_a_nurse():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = _missions_from(plant, "FREEZER_BLOOD_04")[0]
    m["staff_name"] = None
    plant.accept_mission(m["id"], actor="nurse-rao")
    who = [e["who"] for e in m["events"] if e["action"] == "accepted"]
    assert who == ["unassigned"]


def test_qr_wrong_vault_rejects_and_does_not_complete():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = _missions_from(plant, "FREEZER_BLOOD_04")[0]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    wrong = "WALKIN_COLD_01" if m["to_asset"] != "WALKIN_COLD_01" else "FREEZER_BLOOD_01"
    bad = plant.scan_mission(m["id"], f"VAULT:{wrong}")
    assert bad["last_reject"] == f"Wrong vault. Destination is {m['to_asset']}."
    assert bad["status"] == "in_transit"
    assert bad["scan_step"] == "dest"


def test_qr_happy_path_completes_and_moves_stock():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = _missions_from(plant, "FREEZER_BLOOD_04")[0]
    dest = m["to_asset"]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    done = plant.scan_mission(m["id"], f"VAULT:{dest}")
    assert done["status"] == "complete"
    assert done["scan_step"] == "done"
    assert done["last_reject"] is None
    moved = {u["unit_id"] for u in m["units"]}
    assert all(u["asset_id"] == dest for u in plant.inventory if u["unit_id"] in moved)
    assert plant.assets[dest].reserved_l == 0.0


def test_scan_after_completion_does_not_raise_a_false_error():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = _missions_from(plant, "FREEZER_BLOOD_04")[0]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    plant.scan_mission(m["id"], f"VAULT:{m['to_asset']}")
    again = plant.scan_mission(m["id"], "VAULT:WALKIN_COLD_01")
    assert again["status"] == "complete"
    assert again["last_reject"] is None


def test_demo_can_be_run_twice_after_asset_reset():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m1 = _missions_from(plant, "FREEZER_BLOOD_04")[0]
    plant.accept_mission(m1["id"])
    plant.scan_mission(m1["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m1["id"], f"VAULT:{m1['from_asset']}")
    plant.scan_mission(m1["id"], f"VAULT:{m1['to_asset']}")

    plant.anomaly("FREEZER_BLOOD_04", "reset")
    assert all(not s["busy"] for s in plant.staff)
    assert not [al for al in plant.alerts if al["asset_id"] == "FREEZER_BLOOD_04"]

    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    second = _missions_from(plant, "FREEZER_BLOOD_04")
    assert len(second) == 2, "a reset asset must be able to raise a fresh MOVE"
    assert len(second[-1]["units"]) == 4, "stock must be back home after reset"
    assert second[-1]["staff_name"] == "Nurse Rao"


def test_reset_all_returns_plant_to_opening_state():
    plant = Plant()
    opening_free = {aid: a.free_l for aid, a in plant.assets.items()}
    plant.anomaly("ILR_VAX_02", "lwt")
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    plant.anomaly("FREEZER_BLOOD_05", "compressor")
    plant.reset_all()
    assert plant.alerts == []
    assert plant.missions == []
    assert plant.tickets == []
    assert all(not s["busy"] for s in plant.staff)
    assert {aid: a.free_l for aid, a in plant.assets.items()} == opening_free
    assert all(u["asset_id"] == u["home_asset_id"] for u in plant.inventory)
    for a in plant.assets.values():
        assert a.processed.fault_class == "NONE"


def test_pick_backup_skips_self_and_respects_capacity():
    src = spec_by_id("FREEZER_BLOOD_04")
    remaining = {a.asset_id: a.capacity_l - a.baseline_used_l for a in ASSETS}
    dst = pick_backup(src, remaining, {}, need_l=1.4, other_need_l=0.7)
    assert dst is not None and dst.asset_id == "FREEZER_BLOOD_03"

    remaining["FREEZER_BLOOD_03"] = 0.4  # backup now full
    dst2 = pick_backup(src, remaining, {}, need_l=1.4, other_need_l=0.7)
    assert dst2 is not None
    assert dst2.asset_id != "FREEZER_BLOOD_03"
    assert dst2.asset_id != src.asset_id
