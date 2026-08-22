"""PostgREST publisher for the CryoDispatch plant.

The plant remains the only decision engine. This module copies full in-memory
lists (not the truncated UI snapshot) after the lock drops, and drains
`plant_intents` so web/staff can act without talking to :8787.

Network I/O never runs inside Plant._lock.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

IST = timezone(timedelta(hours=5, minutes=30))
TELEMETRY_EVERY_S = 15.0


def ist_to_iso(value: Any) -> Any:
    """Plant stamps IST strings; Postgres columns are timestamptz."""
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.endswith(" IST"):
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S IST").replace(tzinfo=IST)
        return dt.astimezone(timezone.utc).isoformat()
    return value


def asset_row(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_id": a["asset_id"],
        "asset_class": a["asset_class"],
        "label": a.get("label"),
        "location": a.get("location"),
        "floor": a.get("floor"),
        "zone": a.get("zone"),
        "temperature": a.get("temperature"),
        "door_status": a.get("door_status"),
        "compressor_health": a.get("compressor_health"),
        "battery_pct": a.get("battery_pct"),
        "probe_online": a.get("probe_online"),
        "map_x": a.get("map_x"),
        "map_y": a.get("map_y"),
        "topic": a.get("topic"),
        "timestamp": a.get("timestamp"),
        "minutes_to_breach": a.get("minutes_to_breach"),
        "risk_score": a.get("risk_score"),
        "remaining_efficacy_pct": a.get("remaining_efficacy_pct"),
        "t_eq_c": a.get("t_eq_c"),
        "tau_min": a.get("tau_min"),
        "mkt_c": a.get("mkt_c"),
        "dt_dt_c_per_min": a.get("dT_dt_c_per_min"),
        "predicted_t_60s_c": a.get("predicted_T_60s_c"),
        "breach_threshold_c": a.get("breach_threshold_c"),
        "breach_direction": a.get("breach_direction"),
        "model_mode": a.get("model_mode"),
        "confidence": a.get("confidence"),
        "fault_class": a.get("fault_class"),
        "band_low_c": a.get("band_low_c"),
        "band_high_c": a.get("band_high_c"),
        "setpoint_c": a.get("setpoint_c"),
        "capacity_l": a.get("capacity_l"),
        "used_l": a.get("used_l"),
        "reserved_l": a.get("reserved_l"),
        "free_l": a.get("free_l"),
        "sensor_id": a.get("sensor_id"),
        "demo_role": a.get("demo_role"),
        "recent_c": a.get("recent_c") or [],
        "updated_at": ist_to_iso(a.get("updated_at")),
    }


class Cloud:
    def __init__(self, url: str, service_key: str) -> None:
        self.rest = url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }
        self._http = httpx.Client(timeout=8.0)
        self._last_telemetry = 0.0
        self._last_faults: dict[str, str] = {}

    @classmethod
    def from_env(cls) -> Cloud | None:
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if not url or not key:
            return None
        return cls(url, key)

    def drain(self, plant: Any) -> None:
        rows = self._get("plant_intents", {"status": "eq.pending", "order": "created_at.asc"})
        if not rows:
            return
        for row in rows:
            iid = row["id"]
            self._patch("plant_intents", {"id": f"eq.{iid}"}, {"status": "processing"})
            try:
                result = plant.apply_intent(row["kind"], row.get("payload") or {})
                self._patch(
                    "plant_intents",
                    {"id": f"eq.{iid}"},
                    {
                        "status": "done",
                        "result": result if isinstance(result, dict) else {"ok": True},
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                        "error": None,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                self._patch(
                    "plant_intents",
                    {"id": f"eq.{iid}"},
                    {
                        "status": "error",
                        "error": str(exc),
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

    def publish(self, plant: Any) -> None:
        reset = plant.consume_cloud_reset()
        state = plant.full_state()
        if reset:
            for table in ("alerts", "missions", "tickets", "custody_documents"):
                self._delete_all(table)
            self._delete("plant_intents", {"status": "in.(pending,processing)"})
        self._upsert("plant_meta", "site_id", [
            {
                "site_id": state["site_id"],
                "hospital": state["hospital"],
                "tick": state["tick"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ])
        self._upsert("asset_state", "asset_id", [asset_row(a) for a in state["assets"]])
        self._upsert("alerts", "id", [_alert_row(x) for x in state["alerts"]])
        self._upsert("tickets", "id", [_ticket_row(x) for x in state["tickets"]])
        self._upsert("missions", "id", [_mission_row(x) for x in state["missions"]])
        self._upsert("inventory", "unit_id", list(state["inventory"]))
        self._upsert("staff", "id", list(state["staff"]))
        self._upsert("audit_events", "id", [_audit_row(x) for x in state["audit"]])
        self._upsert(
            "custody_documents",
            "mission_id",
            [{"mission_id": c["mission_id"], "doc": c["doc"]} for c in state["custody"]],
        )
        now = time.time()
        faults = {a["asset_id"]: a.get("fault_class") or "NONE" for a in state["assets"]}
        anomaly = any(faults[k] != self._last_faults.get(k, "NONE") for k in faults)
        if anomaly or now - self._last_telemetry >= TELEMETRY_EVERY_S:
            payload = [
                {"asset_id": a["asset_id"], "payload": a}
                for a in state["assets"]
                if a.get("fault_class") not in (None, "NONE") or anomaly
            ]
            if not payload:
                payload = [{"asset_id": a["asset_id"], "payload": a} for a in state["assets"][:1]]
            self._post("telemetry", payload)
            self._last_telemetry = now
            self._last_faults = faults

    def _get(self, table: str, params: dict[str, str]) -> list[Any]:
        r = self._http.get(f"{self.rest}/{table}", headers=self.headers, params=params)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else []

    def _post(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        headers = {**self.headers, "Prefer": "return=minimal"}
        r = self._http.post(f"{self.rest}/{table}", headers=headers, json=rows)
        r.raise_for_status()

    def _upsert(self, table: str, pk: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=minimal"}
        r = self._http.post(
            f"{self.rest}/{table}",
            headers=headers,
            params={"on_conflict": pk},
            json=rows,
        )
        r.raise_for_status()

    def _patch(self, table: str, params: dict[str, str], body: dict[str, Any]) -> None:
        headers = {**self.headers, "Prefer": "return=minimal"}
        r = self._http.patch(f"{self.rest}/{table}", headers=headers, params=params, json=body)
        r.raise_for_status()

    def _delete(self, table: str, params: dict[str, str]) -> None:
        headers = {**self.headers, "Prefer": "return=minimal"}
        r = self._http.delete(f"{self.rest}/{table}", headers=headers, params=params)
        r.raise_for_status()

    def _delete_all(self, table: str) -> None:
        # PostgREST requires a filter; this matches every row with a non-null PK.
        self._delete(table, {"id": "not.is.null"} if table != "custody_documents" else {"mission_id": "not.is.null"})


def _alert_row(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": a["id"],
        "asset_id": a["asset_id"],
        "kind": a["kind"],
        "severity": a["severity"],
        "message": a["message"],
        "acked_at": ist_to_iso(a.get("acked_at")),
        "created_at": ist_to_iso(a.get("created_at")),
    }


def _ticket_row(t: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": t["id"],
        "alert_id": t.get("alert_id"),
        "asset_id": t["asset_id"],
        "kind": t["kind"],
        "duty_cycle": t.get("duty_cycle"),
        "twin_duty_cycle": t.get("twin_duty_cycle"),
        "parts": t.get("parts"),
        "sla_min": t.get("sla_min"),
        "kwh_hold_30m": t.get("kwh_hold_30m"),
        "kwh_move": t.get("kwh_move"),
        "created_at": ist_to_iso(t.get("created_at")),
    }


def _mission_row(m: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": m["id"],
        "alert_id": m.get("alert_id"),
        "from_asset": m["from_asset"],
        "from_label": m.get("from_label"),
        "to_asset": m["to_asset"],
        "to_label": m.get("to_label"),
        "units": m.get("units") or [],
        "staff_id": m.get("staff_id"),
        "staff_name": m.get("staff_name"),
        "status": m["status"],
        "eta_min": m.get("eta_min"),
        "distance_m": m.get("distance_m"),
        "ticket": m.get("ticket"),
        "scan_step": m.get("scan_step"),
        "last_reject": m.get("last_reject"),
        "routing": m.get("routing"),
        "events": m.get("events") or [],
        "created_at": ist_to_iso(m.get("created_at")),
    }


def _audit_row(ev: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": ev["id"],
        "actor": ev["actor"],
        "action": ev["action"],
        "old_value": ev.get("old_value"),
        "new_value": ev.get("new_value"),
        "reason": ev.get("reason"),
        "payload_hash": ev.get("payload_hash"),
        "created_at": ist_to_iso(ev.get("created_at")),
    }
