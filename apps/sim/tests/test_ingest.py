import pytest

from sim.plant import Plant


def test_malformed_telemetry_is_rejected_not_crashed():
    plant = Plant()
    with pytest.raises(ValueError):
        plant.ingest({"asset_id": "FREEZER_BLOOD_04", "temperature": "abc"})


def test_compressor_health_outside_unit_interval_is_422():
    plant = Plant()
    with pytest.raises(ValueError, match="compressor_health"):
        plant.ingest({"asset_id": "ILR_VAX_01", "temperature": 5.0, "compressor_health": 3.0})
    assert plant.assets["ILR_VAX_01"].processed.t_eq_c is None or (
        plant.assets["ILR_VAX_01"].health == 1.0
    )


def test_non_finite_temperature_is_rejected():
    plant = Plant()
    with pytest.raises(ValueError, match="finite"):
        plant.ingest({"asset_id": "ILR_VAX_01", "temperature": float("nan")})


def test_missing_asset_id_is_a_validation_error_not_a_lookup():
    plant = Plant()
    with pytest.raises(ValueError, match="asset_id"):
        plant.ingest({"temperature": 5.0})


def test_unknown_asset_raises_keyerror():
    plant = Plant()
    with pytest.raises(KeyError):
        plant.ingest({"asset_id": "NOPE_999", "temperature": 4.0})


def test_hardware_frame_without_a_reading_is_probe_dead_not_a_move():
    plant = Plant()
    plant.ingest(
        {
            "asset_id": "ILR_VAX_02",
            "asset_class": "vaccine_ilr",
            "temperature": None,
            "probe_online": False,
            "compressor_health": 1.0,
            "door_status": "CLOSED",
        }
    )
    a = plant.assets["ILR_VAX_02"]
    assert a.processed.fault_class == "PROBE_DEAD"
    assert not [m for m in plant.missions if m["from_asset"] == "ILR_VAX_02"]


def test_hardware_frame_out_of_band_dispatches():
    plant = Plant()
    plant.ingest({"asset_id": "FREEZER_BLOOD_04", "asset_class": "blood_rbc", "temperature": 9.9})
    a = plant.assets["FREEZER_BLOOD_04"]
    assert a.processed.fault_class == "THERMAL_EXCURSION"
    assert a.processed.model_mode == "breached"
    assert [m for m in plant.missions if m["from_asset"] == "FREEZER_BLOOD_04"]


def test_crash_carts_stay_location_only_after_a_reset():
    plant = Plant()
    plant.reset_all()
    for a in plant.assets.values():
        expected = "stable" if a.spec.thermal else "location"
        assert a.processed.model_mode == expected


def test_custody_product_is_a_snapshot_of_dispatch_not_a_live_pointer():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = [x for x in plant.missions if x["from_asset"] == "FREEZER_BLOOD_04"][0]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    plant.scan_mission(m["id"], f"VAULT:{m['to_asset']}")
    doc = plant.custody(m["id"])
    # The certificate documents a move out of FB04; the product must not already
    # claim to live at the destination.
    assert all(u["asset_id"] == "FREEZER_BLOOD_04" for u in doc["product"])
    assert all(u["asset_id"] == m["to_asset"] for u in plant.inventory if u["unit_id"] == "BAG-ONEG-01")
