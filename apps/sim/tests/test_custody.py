from sim.plant import Plant


def _completed_mission(plant: Plant) -> dict:
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = [x for x in plant.missions if x["from_asset"] == "FREEZER_BLOOD_04"][0]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    plant.scan_mission(m["id"], f"VAULT:{m['to_asset']}")
    return m


def test_custody_records_distinct_source_and_destination():
    plant = Plant()
    m = _completed_mission(plant)
    doc = plant.custody(m["id"])
    assert doc["from_site"] != doc["to_site"]
    assert "RBC Vault 4" in doc["from_site"]
    assert "RBC Vault 3" in doc["to_site"]


def test_rescued_stock_is_released_not_quarantined():
    plant = Plant()
    m = _completed_mission(plant)
    doc = plant.custody(m["id"])
    assert doc["time_out_of_range_min"] == 0.0
    assert doc["disposition"].startswith("RELEASED")
    assert "predictive relocation" in doc["event_class"]


def test_real_excursion_is_quarantined_with_measured_duration():
    plant = Plant(demo_tau_min=0.05, tick_sec=1.0)
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    for _ in range(20):
        plant.step()
    m = [x for x in plant.missions if x["from_asset"] == "FREEZER_BLOOD_04"][0]
    plant.accept_mission(m["id"])
    plant.scan_mission(m["id"], "UNIT:BAG-ONEG-01")
    plant.scan_mission(m["id"], f"VAULT:{m['from_asset']}")
    plant.scan_mission(m["id"], f"VAULT:{m['to_asset']}")
    doc = plant.custody(m["id"])
    assert doc["time_out_of_range_min"] > 0.0
    assert doc["disposition"].startswith("QUARANTINE")
    assert "excursion" in doc["event_class"]


def test_custody_window_covers_pre_fault_readings():
    plant = Plant()
    for _ in range(10):
        plant.step()
    m = _completed_mission(plant)
    doc = plant.custody(m["id"])
    band_low, band_high = 2.0, 6.0
    assert doc["min_c"] is not None and doc["max_c"] is not None
    assert band_low <= doc["min_c"] <= band_high, "window must include in-band readings"
    assert doc["observation_window_min"] > 0


def test_custody_never_uses_mkt_to_release_blood():
    plant = Plant()
    m = _completed_mission(plant)
    doc = plant.custody(m["id"])
    assert doc["mkt_c"] is None
    assert "never used to release blood" in doc["footer"]
    assert "Not FDA-certified" in doc["footer"]


def test_custody_log_has_every_handoff_with_timestamps():
    plant = Plant()
    m = _completed_mission(plant)
    doc = plant.custody(m["id"])
    actions = [e["action"] for e in doc["custody"]]
    assert "proposed" in actions
    assert "accepted" in actions
    assert any("unit verified" in a for a in actions)
    assert any("checked out" in a for a in actions)
    assert any("checked in" in a for a in actions)
    assert all(e["when"].endswith("IST") for e in doc["custody"])


def test_incomplete_mission_certificate_is_a_draft():
    plant = Plant()
    plant.anomaly("FREEZER_BLOOD_04", "compressor")
    m = [x for x in plant.missions if x["from_asset"] == "FREEZER_BLOOD_04"][0]
    doc = plant.custody(m["id"])
    assert doc["mission_status"] == "proposed"
    assert doc["draft"] is True
    assert doc["disposition"].startswith("DRAFT — ")
    assert "not completed" in doc["disposition"]
    assert doc["event_class"].startswith("DRAFT — ")


def test_completed_mission_certificate_is_not_a_draft():
    plant = Plant()
    m = _completed_mission(plant)
    doc = plant.custody(m["id"])
    assert doc["mission_status"] == "complete"
    assert doc["draft"] is False
    assert not doc["disposition"].startswith("DRAFT")


def test_custody_records_the_routing_reason():
    plant = Plant()
    m = _completed_mission(plant)
    doc = plant.custody(m["id"])
    assert doc["routing"]["need_l"] > 0
    assert "cascade_risk" in doc["routing"]
    assert doc["payload_hash"]
