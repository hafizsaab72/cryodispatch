from sim.hospital import ASSETS, INVENTORY, STAFF


def test_twenty_four_assets_across_three_floors():
    assert len(ASSETS) == 24
    ids = [a.asset_id for a in ASSETS]
    assert len(ids) == len(set(ids))
    assert {a.floor for a in ASSETS} == {1, 2, 3}


def test_every_product_class_is_represented_with_the_right_band():
    bands = {a.asset_class: (a.band.low, a.band.high) for a in ASSETS if a.band}
    assert bands["blood_rbc"] == (2.0, 6.0)
    assert bands["vaccine_ilr"] == (2.0, 8.0)
    assert bands["insulin_ilr"] == (2.0, 8.0)
    assert bands["platelet"] == (20.0, 24.0)
    assert bands["plasma_ffp"] == (-40.0, -30.0)


def test_freeze_sensitive_classes_carry_a_freeze_rail():
    for a in ASSETS:
        if a.asset_class in {"vaccine_ilr", "insulin_ilr", "walkin_cold"}:
            assert a.band is not None and a.band.freeze_critical == 0.0
        if a.asset_class == "blood_rbc":
            assert a.band is not None and a.band.freeze_critical is None


def test_crash_carts_are_location_only():
    carts = [a for a in ASSETS if a.asset_class == "crash_cart"]
    assert len(carts) == 4
    assert all(not c.thermal and c.band is None for c in carts)


def test_map_coordinates_are_grouped_by_floor():
    """The command centre draws floor bands, so floors must not interleave."""
    by_floor: dict[int, list[float]] = {}
    for a in ASSETS:
        by_floor.setdefault(a.floor, []).append(a.map_y)
    assert max(by_floor[1]) < min(by_floor[2])
    assert max(by_floor[2]) < min(by_floor[3])


def test_backup_vault_is_nearly_full_so_the_cascade_is_real():
    backup = next(a for a in ASSETS if a.asset_id == "FREEZER_BLOOD_03")
    free = backup.capacity_l - backup.baseline_used_l
    primary_need = sum(u.volume_l for u in INVENTORY if u.asset_id == "FREEZER_BLOOD_04")
    second_need = sum(u.volume_l for u in INVENTORY if u.asset_id == "FREEZER_BLOOD_05")
    assert free >= primary_need, "backup must fit the first failing vault"
    assert free < primary_need + second_need, "but not both"


def test_two_blood_certified_couriers_exist():
    assert len([s for s in STAFF if s.cert == "blood"]) >= 2


def test_every_thermal_asset_has_a_sensor_id():
    assert all(a.sensor_id for a in ASSETS if a.thermal)
