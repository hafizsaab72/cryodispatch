from __future__ import annotations

import hashlib
import random
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable

from sim.dispatch import cert_for, distance_m, kwh_hold, kwh_move, pick_backup
from sim.hospital import ASSETS, HOSPITAL, INVENTORY, SITE_ID, STAFF
from sim.models import Processed, Telemetry
from sim.thermal import (
    STABLE_SENTINEL,
    minutes_to_breach,
    minutes_to_freeze,
    mkt_c,
    predicted_t,
    remaining_efficacy_pct,
    risk_score,
    slope_c_per_min,
    step_temperature,
    t_eq,
)

Listener = Callable[[dict[str, Any]], None]


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class LiveAsset:
    spec: AssetSpec
    temperature: float | None
    door: float = 0.0
    health: float = 1.0
    battery: float = 97.0
    probe_online: bool = True
    processed: Processed = field(default_factory=Processed)
    history: deque = field(default_factory=lambda: deque(maxlen=8))
    temps_for_mkt: deque = field(default_factory=lambda: deque(maxlen=40))
    elapsed_min: float = 0.0
    used_l: float = 0.0
    reserved_l: float = 0.0


class Plant:
    def __init__(self, demo_tau_min: float = 2.0, tick_sec: float = 1.0) -> None:
        self.demo_tau_min = demo_tau_min
        self.tick_sec = tick_sec
        self.site_id = SITE_ID
        self.hospital = HOSPITAL
        self.tick = 0
        self.rng = random.Random(7)
        self.assets: dict[str, LiveAsset] = {}
        for spec in ASSETS:
            t0 = spec.band.setpoint if spec.band else None
            used = sum(u.volume_l for u in INVENTORY if u.asset_id == spec.asset_id)
            self.assets[spec.asset_id] = LiveAsset(spec=spec, temperature=t0, used_l=used)
        self.inventory = [u.__dict__.copy() for u in INVENTORY]
        self.staff = [{**s.__dict__, "busy": False} for s in STAFF]
        self.alerts: list[dict[str, Any]] = []
        self.missions: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.listeners: list[Listener] = []
        self._active_alert_assets: set[str] = set()
        self._t0 = time.time()

    def subscribe(self, fn: Listener) -> None:
        self.listeners.append(fn)

    def _emit(self, event: dict[str, Any]) -> None:
        event.setdefault("ts", time.time())
        for fn in list(self.listeners):
            fn(event)

    def snapshot(self) -> dict[str, Any]:
        return {
            "site_id": self.site_id,
            "hospital": self.hospital,
            "tick": self.tick,
            "assets": [self._asset_public(a) for a in self.assets.values()],
            "alerts": list(reversed(self.alerts[-40:])),
            "missions": list(reversed(self.missions[-20:])),
            "inventory": self.inventory,
            "staff": self.staff,
            "audit": list(reversed(self.audit[-40:])),
        }

    def _asset_public(self, a: LiveAsset) -> dict[str, Any]:
        p = a.processed
        spec = a.spec
        return {
            "topic": f"cryo/{self.site_id}/assets/{spec.asset_id}/telemetry",
            "asset_id": spec.asset_id,
            "label": spec.label,
            "asset_class": spec.asset_class,
            "location": spec.location,
            "floor": spec.floor,
            "zone": spec.zone,
            "temperature": None if a.temperature is None else round(a.temperature, 3),
            "door_status": "OPEN" if a.door >= 0.5 else "CLOSED",
            "compressor_health": round(a.health, 3),
            "battery_pct": round(a.battery, 1),
            "probe_online": a.probe_online,
            "map_x": spec.map_x + (self.rng.uniform(-0.4, 0.4) if not spec.thermal else 0),
            "map_y": spec.map_y,
            "timestamp": time.time(),
            "band_low_c": spec.band.low if spec.band else None,
            "band_high_c": spec.band.high if spec.band else None,
            "setpoint_c": spec.band.setpoint if spec.band else None,
            "minutes_to_breach": p.minutes_to_breach,
            "risk_score": p.risk_score,
            "remaining_efficacy_pct": p.remaining_efficacy_pct,
            "t_eq_c": p.t_eq_c,
            "tau_min": p.tau_min,
            "mkt_c": p.mkt_c,
            "dT_dt_c_per_min": p.dT_dt_c_per_min,
            "predicted_T_60s_c": p.predicted_T_60s_c,
            "breach_threshold_c": p.breach_threshold_c,
            "model_mode": p.model_mode,
            "confidence": p.confidence,
            "fault_class": p.fault_class,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "capacity_l": spec.capacity_l,
            "used_l": round(a.used_l + a.reserved_l, 3),
            "demo_role": spec.demo_role,
        }

    def telemetry_of(self, a: LiveAsset) -> Telemetry:
        spec = a.spec
        return Telemetry(
            topic=f"cryo/{self.site_id}/assets/{spec.asset_id}/telemetry",
            asset_id=spec.asset_id,
            asset_class=spec.asset_class,
            location=spec.location,
            floor=spec.floor,
            zone=spec.zone,
            temperature=None if a.temperature is None else round(a.temperature, 3),
            door_status="OPEN" if a.door >= 0.5 else "CLOSED",
            compressor_health=round(a.health, 3),
            battery_pct=round(a.battery, 1),
            probe_online=a.probe_online,
            map_x=spec.map_x,
            map_y=spec.map_y,
            timestamp=time.time(),
        )

    def step(self) -> None:
        self.tick += 1
        dt_min = self.tick_sec / 60.0
        t_abs = (time.time() - self._t0) / 60.0
        for a in self.assets.values():
            self._step_asset(a, dt_min, t_abs)
        self._emit({"type": "state", "state": self.snapshot()})

    def _step_asset(self, a: LiveAsset, dt_min: float, t_abs: float) -> None:
        spec = a.spec
        if not spec.thermal or spec.band is None or a.temperature is None:
            a.processed = Processed(model_mode="location", fault_class="NONE", minutes_to_breach=STABLE_SENTINEL)
            # wander crash carts slightly
            if not spec.thermal:
                spec.map_x = min(92, max(8, spec.map_x + self.rng.uniform(-0.15, 0.15)))
            return

        if a.probe_online:
            teq = t_eq(spec.band.setpoint, a.door, a.health)
            tau = self.demo_tau_min
            noise = self.rng.uniform(-0.03, 0.03)
            a.temperature = step_temperature(a.temperature, teq, tau, dt_min) + noise
            a.elapsed_min += dt_min
            a.history.append((t_abs, a.temperature))
            a.temps_for_mkt.append(a.temperature)
            a.battery = max(80.0, a.battery - 0.0008)
        else:
            teq = t_eq(spec.band.setpoint, a.door, a.health)
            tau = self.demo_tau_min

        p = self._process(a, teq, tau)
        a.processed = p
        self._maybe_alert(a)

    def _process(self, a: LiveAsset, teq: float, tau: float) -> Processed:
        spec = a.spec
        assert spec.band is not None
        band = spec.band
        t = a.temperature if a.temperature is not None else band.setpoint

        if not a.probe_online:
            return Processed(
                minutes_to_breach=STABLE_SENTINEL,
                risk_score=22.0,
                t_eq_c=round(teq, 3),
                tau_min=tau,
                breach_threshold_c=band.high,
                model_mode="probe_dead",
                confidence=0.95,
                fault_class="PROBE_DEAD",
            )

        heat_min, _heat_mode = minutes_to_breach(t, teq, band.high, tau)
        freeze_min = STABLE_SENTINEL
        if band.freeze_critical is not None:
            freeze_min = minutes_to_freeze(t, teq, band.freeze_critical, tau)

        minutes = min(heat_min, freeze_min)
        if t > band.high or (band.freeze_critical is not None and t <= band.freeze_critical) or t < band.low:
            mode = "breached"
            minutes = 0.0
        elif minutes < STABLE_SENTINEL:
            mode = "warming"
        else:
            mode = "stable"

        slope = slope_c_per_min(list(a.history))
        mkt = None
        eta = None
        if spec.asset_class in {"insulin_ilr"}:
            mkt = mkt_c(list(a.temps_for_mkt))
            if mkt is not None:
                eta = remaining_efficacy_pct(mkt, max(a.elapsed_min, 0.05))

        if t < band.low or t > band.high:
            fault = "THERMAL_EXCURSION"
        elif a.door >= 0.5 and mode == "stable":
            fault = "DOOR_OPEN"
        elif mode == "warming":
            fault = "THERMAL_EXCURSION"
        else:
            fault = "NONE"

        conf = min(1.0, 0.35 + 0.08 * len(a.history))
        if abs(teq - t) < 0.15:
            conf *= 0.6

        return Processed(
            minutes_to_breach=round(minutes, 3),
            risk_score=round(risk_score(minutes, eta, a.door), 2),
            remaining_efficacy_pct=None if eta is None else round(eta, 2),
            t_eq_c=round(teq, 3),
            tau_min=tau,
            mkt_c=None if mkt is None else round(mkt, 3),
            dT_dt_c_per_min=None if slope is None else round(slope, 4),
            predicted_T_60s_c=round(predicted_t(t, teq, tau, 1.0), 3),
            breach_threshold_c=band.high,
            model_mode=mode,
            confidence=round(conf, 3),
            fault_class=fault,
        )

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Accept an external (ESP32 / MQTT bridge) telemetry dict."""
        aid = payload["asset_id"]
        a = self.assets.get(aid)
        if not a:
            raise KeyError(aid)
        if "temperature" in payload and payload["temperature"] is not None:
            a.temperature = float(payload["temperature"])
        if "compressor_health" in payload:
            a.health = float(payload["compressor_health"])
        if "door_status" in payload:
            a.door = 1.0 if str(payload["door_status"]).upper() == "OPEN" else 0.0
        if "probe_online" in payload:
            a.probe_online = bool(payload["probe_online"])
        teq = t_eq(a.spec.band.setpoint, a.door, a.health) if a.spec.band else 0.0
        if a.spec.band:
            a.processed = self._process(a, teq, self.demo_tau_min)
            self._maybe_alert(a)
        pub = self._asset_public(a)
        self._emit({"type": "ingest", "asset": pub})
        return pub

    def anomaly(self, asset_id: str, kind: str) -> dict[str, Any]:
        a = self.assets[asset_id]
        if kind == "compressor":
            a.health = 0.25
            a.probe_online = True
            self._audit("sim", "anomaly.compressor", "1.0", "0.25", f"{asset_id} compressor derated")
        elif kind == "door":
            a.door = 1.0
            self._audit("sim", "anomaly.door", "CLOSED", "OPEN", f"{asset_id} door stuck open")
        elif kind == "lwt":
            a.probe_online = False
            self._audit("sim", "anomaly.lwt", "online", "offline", f"{asset_id} last-will offline")
        elif kind == "reset":
            a.health = 1.0
            a.door = 0.0
            a.probe_online = True
            if a.spec.band:
                a.temperature = a.spec.band.setpoint
            a.processed = Processed()
            self._active_alert_assets.discard(asset_id)
            self._audit("sim", "anomaly.reset", "fault", "clear", f"{asset_id} reset")
        else:
            raise ValueError(kind)
        # process immediately so T_eq jumps before the next tick
        if a.spec.band and a.temperature is not None:
            teq = t_eq(a.spec.band.setpoint, a.door, a.health)
            a.processed = self._process(a, teq, self.demo_tau_min)
            self._maybe_alert(a)
        self._emit({"type": "anomaly", "asset_id": asset_id, "kind": kind, "state": self.snapshot()})
        return {"ok": True, "asset_id": asset_id, "kind": kind}

    def _maybe_alert(self, a: LiveAsset) -> None:
        p = a.processed
        aid = a.spec.asset_id
        if p.fault_class == "PROBE_DEAD":
            if aid not in self._active_alert_assets:
                self._active_alert_assets.add(aid)
                alert = self._push_alert(
                    aid,
                    "PROBE_DEAD",
                    "critical",
                    f"{a.spec.label}: probe dead (LWT). Ticket only — do not move stock.",
                )
                self._open_ticket_only(a, alert["id"])
            return

        predictive = p.model_mode == "warming" and p.minutes_to_breach < 25
        excursion = p.fault_class == "THERMAL_EXCURSION"
        if not (predictive or excursion):
            return
        if aid in self._active_alert_assets:
            return
        self._active_alert_assets.add(aid)
        mins = p.minutes_to_breach
        msg = (
            f"{a.spec.label}: T_eq={p.t_eq_c}°C. Breach in {mins:.1f} min "
            f"(air still {a.temperature:.1f}°C)."
        )
        alert = self._push_alert(aid, "THERMAL_PREDICT" if p.model_mode != "breached" else "THERMAL_EXCURSION", "critical", msg)
        self._open_mission(a, alert["id"])

    def _push_alert(self, asset_id: str, kind: str, severity: str, message: str) -> dict[str, Any]:
        alert = {
            "id": _id("al"),
            "asset_id": asset_id,
            "kind": kind,
            "severity": severity,
            "message": message,
            "acked_at": None,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.alerts.append(alert)
        self._emit({"type": "alert", "alert": alert})
        return alert

    def _open_ticket_only(self, a: LiveAsset, alert_id: str) -> None:
        ticket = {
            "asset_id": a.spec.asset_id,
            "kind": "instrumentation",
            "duty_cycle": round(0.55 + 0.4 * (1 - a.health), 2),
            "twin_duty_cycle": 0.55,
            "parts": "probe, logger, loom",
            "sla_min": 45,
            "kwh_hold_30m": kwh_hold(a.health),
            "kwh_move": 0.0,
        }
        self._audit("plant", "ticket.open", "", ticket["parts"], f"PROBE_DEAD {a.spec.asset_id} — no evacuate")
        self._emit({"type": "ticket", "ticket": ticket, "alert_id": alert_id})

    def _remaining_map(self) -> dict[str, float]:
        out = {}
        for aid, a in self.assets.items():
            out[aid] = max(0.0, a.spec.capacity_l - a.used_l - a.reserved_l)
        return out

    def _open_mission(self, a: LiveAsset, alert_id: str) -> None:
        units = [u for u in self.inventory if u["asset_id"] == a.spec.asset_id]
        if not units:
            self._open_ticket_only(a, alert_id)
            return
        need_l = sum(u["volume_l"] for u in units)
        remaining = self._remaining_map()
        reserved: dict[str, float] = defaultdict(float)
        # other failing blood vault need (for cascade): if this is V3, V4 still has stock
        other_need = 0.0
        if a.spec.asset_id == "FREEZER_BLOOD_04":
            other_need = sum(u["volume_l"] for u in self.inventory if u["asset_id"] == "FREEZER_BLOOD_05")
        dst = pick_backup(a.spec, remaining, reserved, need_l, other_need)
        if dst is None:
            self._open_ticket_only(a, alert_id)
            return
        self.assets[dst.asset_id].reserved_l += need_l
        d = distance_m(a.spec, dst)
        staff = self._assign_staff(cert_for(a.spec.asset_class), a.spec.floor)
        ticket = {
            "asset_id": a.spec.asset_id,
            "kind": "thermal",
            "duty_cycle": round(0.55 + 0.4 * (1 - a.health), 2),
            "twin_duty_cycle": 0.55,
            "parts": "start-relay, run-cap",
            "sla_min": 45,
            "kwh_hold_30m": kwh_hold(a.health),
            "kwh_move": kwh_move(),
        }
        mission = {
            "id": _id("ms"),
            "alert_id": alert_id,
            "from_asset": a.spec.asset_id,
            "to_asset": dst.asset_id,
            "units": units,
            "staff_id": staff["id"] if staff else None,
            "staff_name": staff["name"] if staff else None,
            "status": "proposed",
            "eta_min": round(1.5 + d / 40.0, 1),
            "distance_m": round(d, 1),
            "ticket": ticket,
            "scan_step": "unit",
            "last_reject": None,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.missions.append(mission)
        self._audit("plant", "mission.propose", a.spec.asset_id, dst.asset_id, f"MOVE {len(units)} units")
        self._emit({"type": "mission", "mission": mission})

    def _assign_staff(self, cert: str, floor: int) -> dict[str, Any] | None:
        free = [s for s in self.staff if s["cert"] == cert and not s["busy"]]
        if not free:
            free = [s for s in self.staff if not s["busy"]]
        if not free:
            return None
        free.sort(key=lambda s: abs(s["floor"] - floor))
        pick = free[0]
        pick["busy"] = True
        return pick

    def accept_mission(self, mission_id: str, actor: str = "nurse-rao") -> dict[str, Any]:
        m = self._mission(mission_id)
        if m["status"] != "proposed":
            return m
        m["status"] = "accepted"
        m["scan_step"] = "unit"
        self._audit(actor, "mission.accept", "proposed", "accepted", m["id"])
        self._emit({"type": "mission", "mission": m})
        return m

    def scan_mission(self, mission_id: str, code: str, actor: str = "nurse-rao") -> dict[str, Any]:
        m = self._mission(mission_id)
        if m["status"] not in {"accepted", "checkout", "in_transit"}:
            m["last_reject"] = "Accept the MOVE first."
            return m
        token = code.strip()
        expected_units = {u["unit_id"] for u in m["units"]}
        step = m["scan_step"]

        def fail(reason: str) -> dict[str, Any]:
            m["last_reject"] = reason
            m["status"] = "accepted" if m["status"] == "proposed" else m["status"]
            self._audit(actor, "scan.reject", token, reason, m["id"])
            self._emit({"type": "scan", "ok": False, "mission": m})
            return m

        if token.startswith("UNIT:"):
            uid = token.split(":", 1)[1]
            if step != "unit":
                return fail(f"Scan the unit first. Expected a bag, not this step ({step}).")
            if uid not in expected_units:
                return fail(f"Wrong unit. Expected one of {sorted(expected_units)}.")
            m["scan_step"] = "source"
            m["last_reject"] = None
            m["status"] = "checkout"
            self._audit(actor, "scan.unit", "", uid, m["id"])
        elif token.startswith("VAULT:"):
            vid = token.split(":", 1)[1]
            if step == "source":
                if vid != m["from_asset"]:
                    return fail(f"Wrong vault. Checkout is {m['from_asset']}.")
                m["scan_step"] = "dest"
                m["status"] = "in_transit"
                m["last_reject"] = None
                self._audit(actor, "scan.source", m["from_asset"], vid, m["id"])
            elif step == "dest":
                if vid != m["to_asset"]:
                    return fail(f"Wrong vault. Destination is {m['to_asset']}.")
                m["scan_step"] = "done"
                m["status"] = "complete"
                m["last_reject"] = None
                self._complete_move(m)
                self._audit(actor, "scan.dest", m["from_asset"], vid, m["id"])
            else:
                return fail("Scan a unit QR first.")
        else:
            return fail("Unknown QR. Use UNIT:… or VAULT:…")

        self._emit({"type": "scan", "ok": True, "mission": m})
        return m

    def _complete_move(self, m: dict[str, Any]) -> None:
        src = self.assets[m["from_asset"]]
        dst = self.assets[m["to_asset"]]
        vol = sum(u["volume_l"] for u in m["units"])
        src.used_l = max(0.0, src.used_l - vol)
        dst.reserved_l = max(0.0, dst.reserved_l - vol)
        dst.used_l += vol
        for u in self.inventory:
            if u["unit_id"] in {x["unit_id"] for x in m["units"]}:
                u["asset_id"] = m["to_asset"]
        for s in self.staff:
            if s["id"] == m["staff_id"]:
                s["busy"] = False

    def ack_alert(self, alert_id: str, actor: str = "command") -> dict[str, Any]:
        for al in self.alerts:
            if al["id"] == alert_id:
                al["acked_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self._audit(actor, "alert.ack", "open", "acked", alert_id)
                self._emit({"type": "alert", "alert": al})
                return al
        raise KeyError(alert_id)

    def custody(self, mission_id: str) -> dict[str, Any]:
        m = self._mission(mission_id)
        src = self.assets[m["from_asset"]]
        dst = self.assets[m["to_asset"]]
        temps = [t for _, t in src.history]
        doc_id = f"COC-{mission_id[-8:].upper()}"
        event_class = src.processed.fault_class
        disposition = "quarantine" if src.processed.model_mode == "breached" else "OK"
        body = {
            "doc_id": doc_id,
            "product": m["units"],
            "from_site": f"{self.hospital} / {src.spec.location}",
            "to_site": f"{self.hospital} / {dst.spec.location}",
            "custody": [
                {"who": "plant", "when": m["created_at"], "location": src.spec.location, "action": "proposed"},
                {"who": m["staff_name"] or "staff", "when": m.get("created_at"), "location": src.spec.location, "action": m["status"]},
            ],
            "band": f"{src.spec.band.low}–{src.spec.band.high}°C" if src.spec.band else "n/a",
            "min_c": min(temps) if temps else src.temperature,
            "max_c": max(temps) if temps else src.temperature,
            "time_out_of_range_min": 0.0 if src.processed.model_mode != "breached" else 0.4,
            "mkt_c": src.processed.mkt_c,
            "sensor_id": f"DDL-{m['from_asset'][-2:]}",
            "calibration_date": "2026-06-11",
            "event_class": event_class,
            "disposition": disposition,
            "audit": self.audit[-12:],
            "footer": "Audit-trail controls inspired by 21 CFR Part 11.10 and CDSCO GDP §15.7. Not FDA-certified.",
        }
        body["payload_hash"] = _hash(repr(body))
        return body

    def protocol(self) -> dict[str, Any]:
        return {
            "site": self.site_id,
            "topics": [
                f"cryo/{self.site_id}/assets/{{id}}/telemetry",
                f"cryo/{self.site_id}/assets/{{id}}/status",
                f"cryo/{self.site_id}/assets/{{id}}/lwt",
                f"cryo/{self.site_id}/cmd/{{id}}/reroute",
                f"cryo/{self.site_id}/alerts/{{alertId}}",
            ],
        }

    def _mission(self, mission_id: str) -> dict[str, Any]:
        for m in self.missions:
            if m["id"] == mission_id:
                return m
        raise KeyError(mission_id)

    def _audit(self, actor: str, action: str, old: str, new: str, reason: str) -> None:
        ev = {
            "id": _id("au"),
            "actor": actor,
            "action": action,
            "old_value": old,
            "new_value": new,
            "reason": reason,
            "payload_hash": _hash(f"{actor}|{action}|{old}|{new}|{reason}"),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.audit.append(ev)
