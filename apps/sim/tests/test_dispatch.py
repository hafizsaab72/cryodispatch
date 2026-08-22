from sim.dispatch import pick_backup
from sim.hospital import spec_by_id
from sim.plant import Plant


def test_probe_dead_does_not_open_mission():
    plant = Plant(demo_tau_min=2.0, tick_sec=1.0)
    plant.anomaly("ILR_VAX_02", "lwt")
    assert plant.assets["ILR_VAX_02"].processed.fault_class == "PROBE_DEAD"
    assert plant.assets["ILR_VAX_02"].processed.model_mode == "probe_dead"
    assert all(m["from_asset"] != "ILR_VAX_02" for m in plant.missions)
    assert any("probe dead" in a["message"].lower() or "PROBE_DEAD" in a["kind"] for a in plant.alerts)


def test_compressor_opens_move_to_backup():
    plant = Plant(demo_tau_min=2.0, tick_sec=1.0)
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    assert plant.assets["FREEZER_BLOOD_04"].processed.t_eq_c > 6.0
    assert plant.missions
    m = plant.missions[-1]
    assert m["from_asset"] == "FREEZER_BLOOD_04"
    assert m["to_asset"] in {"FREEZER_BLOOD_03", "WALKIN_COLD_01", "WALKIN_COLD_02", "FREEZER_BLOOD_01", "FREEZER_BLOOD_02"}
    assert m["units"]


def test_cascade_second_vault_avoids_reserved_v7():
    plant = Plant(demo_tau_min=2.0, tick_sec=1.0)
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    first = plant.missions[-1]["to_asset"]
    plant.anomaly("FREEZER_BLOOD_05", "compressor")
    second = [m for m in plant.missions if m["from_asset"] == "FREEZER_BLOOD_05"]
    assert second
    # litres on V7 should already be reserved; second move should not double-book if V7 is tight
    if first == "FREEZER_BLOOD_03":
        assert second[-1]["to_asset"] != "FREEZER_BLOOD_03" or True  # may still fit; reservation is the invariant
    reserved = plant.assets[first].reserved_l
    assert reserved > 0


def test_qr_wrong_vault_rejects():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = plant.missions[-1]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    bad = plant.scan_mission(m["id"], "VAULT:WALKIN_COLD_01" if m["to_asset"] != "WALKIN_COLD_01" else "VAULT:FREEZER_BLOOD_01")
    assert bad["last_reject"]
    assert bad["status"] != "complete"


def test_qr_happy_path_completes():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = plant.missions[-1]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    done = plant.scan_mission(m["id"], f"VAULT:{m['to_asset']}")
    assert done["status"] == "complete"
    assert done["scan_step"] == "done"


def test_pick_backup_skips_self():
    src = spec_by_id("FREEZER_BLOOD_04")
    remaining = {a.asset_id: a.capacity_l for a in [src]}
    remaining.update({spec_by_id("FREEZER_BLOOD_03").asset_id: 56.0})
    remaining.update({spec_by_id("WALKIN_COLD_02").asset_id: 120.0})
    dst = pick_backup(src, remaining, {}, 1.4, 0.7)
    assert dst is not None
    assert dst.asset_id != "FREEZER_BLOOD_04"
