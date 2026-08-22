from __future__ import annotations

import httpx

from sim.cloud import Cloud, asset_row, ist_to_iso
from sim.hospital import STAFF
from sim.plant import Plant


def test_full_state_is_not_truncated():
    p = Plant()
    for _ in range(5):
        p.anomaly("FREEZER_BLOOD_04", "compressor")
        p.reset_all()
    p.anomaly("FREEZER_BLOOD_04", "compressor")
    snap = p.snapshot()
    full = p.full_state()
    assert "custody" in full
    assert len(full["assets"]) == 24
    assert len(full["alerts"]) >= len(snap["alerts"])
    assert any(s["id"] == "nurse-dsouza" for s in full["staff"])


def test_reset_sets_cloud_flag_and_clears_missions():
    p = Plant()
    p.anomaly("FREEZER_BLOOD_04", "compressor")
    assert p.missions
    assert p.consume_cloud_reset() is False
    p.reset_all()
    assert p.consume_cloud_reset() is True
    assert p.missions == []
    assert p.consume_cloud_reset() is False


def test_apply_intent_anomaly_and_reset():
    p = Plant()
    p.apply_intent("anomaly", {"asset_id": "ILR_VAX_02", "kind": "lwt"})
    assert p.assets["ILR_VAX_02"].probe_online is False
    assert any(t["kind"] == "instrumentation" for t in p.tickets)
    assert not any(m["from_asset"] == "ILR_VAX_02" for m in p.missions)
    p.apply_intent("reset", {})
    assert p.assets["ILR_VAX_02"].probe_online is True
    assert p.missions == []


def test_apply_intent_accept_and_cascade():
    p = Plant()
    p.apply_intent("anomaly", {"asset_id": "FREEZER_BLOOD_04", "anomaly_kind": "compressor"})
    first = next(m for m in p.missions if m["from_asset"] == "FREEZER_BLOOD_04")
    assert first["to_asset"] == "FREEZER_BLOOD_03"
    p.apply_intent("accept", {"mission_id": first["id"], "actor": "nurse-rao"})
    assert next(m for m in p.missions if m["id"] == first["id"])["status"] != "proposed"
    p.apply_intent("anomaly", {"asset_id": "FREEZER_BLOOD_05", "kind": "compressor"})
    second = next(m for m in p.missions if m["from_asset"] == "FREEZER_BLOOD_05")
    assert second["to_asset"] == "FREEZER_BLOOD_06"


def test_publish_deletes_missions_on_reset():
    deletes: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            deletes.append(str(request.url))
        return httpx.Response(200, json=[])

    cloud = Cloud("https://example.supabase.co", "service-role")
    cloud._http = httpx.Client(transport=httpx.MockTransport(handler))
    p = Plant()
    p.anomaly("FREEZER_BLOOD_04", "compressor")
    cloud.publish(p)
    assert not any("/missions" in url for url in deletes)
    p.reset_all()
    cloud.publish(p)
    assert any("/rest/v1/missions" in url for url in deletes)
    assert any("/rest/v1/alerts" in url for url in deletes)
    assert any("/rest/v1/tickets" in url for url in deletes)
    assert any("/rest/v1/custody_documents" in url for url in deletes)


def test_asset_row_maps_shared_names():
    p = Plant()
    row = asset_row(p.full_state()["assets"][0])
    assert "dt_dt_c_per_min" in row
    assert "predicted_t_60s_c" in row
    assert "dT_dt_c_per_min" not in row


def test_ist_to_iso_roundtrip():
    iso = ist_to_iso("2026-08-23 03:08:00 IST")
    assert iso is not None
    assert "2026-08-22" in iso or "2026-08-23" in iso


def test_seed_staff_includes_dsouza():
    assert any(s.id == "nurse-dsouza" for s in STAFF)
    assert len(STAFF) == 4


def test_ingest_function_is_not_a_second_brain():
    from pathlib import Path

    src = Path(__file__).resolve().parents[3] / "supabase/functions/ingest/index.ts"
    text = src.read_text()
    assert "function backupFor" not in text
    assert "tEq(" not in text
    assert "410" in text
