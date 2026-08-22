from sim.hospital import ASSETS


def test_twenty_four_assets():
    assert len(ASSETS) == 24
    ids = [a.asset_id for a in ASSETS]
    assert len(ids) == len(set(ids))
    assert "FREEZER_BLOOD_04" in ids
    assert "ILR_VAX_02" in ids
