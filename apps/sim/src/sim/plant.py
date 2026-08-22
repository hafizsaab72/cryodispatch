from __future__ import annotations

import hashlib
import math
import random
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sim.dispatch import (
    cascade_risk,
    cert_for,
    distance_m,
    kwh_hold,
    kwh_move,
    pick_backup,
    same_band,
)
from sim.hospital import ASSETS, HOSPITAL, INVENTORY, SITE_ID, STAFF, AssetSpec
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

IST = timezone(timedelta(hours=5, minutes=30))
TERMINAL_MISSION = {"complete", "cancelled", "rejected"}
ANOMALY_KINDS = ("compressor", "door", "lwt", "reset")
# An open door with the air still in band is an event, not a discard: it stays a
# DOOR_OPEN warning until the countdown gets this short, then it is a real move.
DOOR_ESCALATE_MIN = 5.0
# Samples regressed for the displayed dT/dt — ~30 s at 1 Hz.
SLOPE_WINDOW = 30
OPENING_BATTERY_PCT = 97.0


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _num(
    value: Any, field: str, aid: str, lo: float | None = None, hi: float | None = None
) -> float:
    """Parse one telemetry number, rejecting the frames that silently poison the model."""
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{aid}: non-numeric {field} ({value!r})") from exc
    if not math.isfinite(num):
        # NaN survives max(0.0, nan) inside the countdown and reads as "breach now".
        raise ValueError(f"{aid}: {field} must be a finite number, got {value!r}")
    if lo is not None and hi is not None and not lo <= num <= hi:
        raise ValueError(f"{aid}: {field} must be within [{lo}, {hi}], got {num}")
    return num


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


@dataclass
class LiveAsset:
    spec: AssetSpec
    temperature: float | None
    map_x: float = 0.0
    map_y: float = 0.0
    door: float = 0.0
    health: float = 1.0
    battery: float = OPENING_BATTERY_PCT
    probe_online: bool = True
    processed: Processed = field(default_factory=Processed)
    history: deque = field(default_factory=lambda: deque(maxlen=8))
    temps_for_mkt: deque = field(default_factory=lambda: deque(maxlen=40))
    # 15 minutes at 1 Hz — the window a custody certificate reports on.
    custody_window: deque = field(default_factory=lambda: deque(maxlen=900))
    elapsed_min: float = 0.0
    excursion_min: float = 0.0
    door_open_min: float = 0.0
    used_l: float = 0.0
    reserved_l: float = 0.0

    @property
    def free_l(self) -> float:
        return max(0.0, self.spec.capacity_l - self.used_l - self.reserved_l)


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
            self.assets[spec.asset_id] = LiveAsset(
                spec=spec, temperature=t0, map_x=spec.map_x, map_y=spec.map_y
            )
        # `home_asset_id` lets a reset put every bag back where it started.
        self.inventory = [{**u.__dict__, "home_asset_id": u.asset_id} for u in INVENTORY]
        self.staff = [{**s.__dict__, "busy": False} for s in STAFF]
        self.alerts: list[dict[str, Any]] = []
        self.missions: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.tickets: list[dict[str, Any]] = []
        self.listeners: list[Listener] = []
        self._active_alerts: set[tuple[str, str]] = set()
        self._t0 = time.time()
        # The tick thread and uvicorn's endpoint threadpool both mutate alerts,
        # missions, inventory and reserved litres. Re-entrant because these
        # entry points call one another (step -> snapshot, anomaly -> reset).
        self._lock = threading.RLock()
        self._recompute_capacity()

    # ------------------------------------------------------------------ wiring

    def subscribe(self, fn: Listener) -> None:
        self.listeners.append(fn)

    def _emit(self, event: dict[str, Any]) -> None:
        event.setdefault("ts", time.time())
        for fn in list(self.listeners):
            fn(event)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "site_id": self.site_id,
                "hospital": self.hospital,
                "tick": self.tick,
                "assets": [self._asset_public(a) for a in self.assets.values()],
                "alerts": list(reversed(self.alerts[-40:])),
                "missions": list(reversed(self.missions[-20:])),
                "tickets": list(reversed(self.tickets[-20:])),
                "inventory": self.inventory,
                "staff": self.staff,
                "audit": list(reversed(self.audit[-40:])),
            }

    def _sample_clock(self) -> float:
        """Seconds stamped on a recorded reading.

        Wall clock when the plant runs live, tick-derived when steps are
        fast-forwarded (tests, replay), so a measured slope means the same
        thing in both. Monotonic either way.
        """
        return max(time.time(), self._t0 + self.tick * self.tick_sec)

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
            "map_x": round(a.map_x, 2),
            "map_y": round(a.map_y, 2),
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
            "breach_direction": p.breach_direction,
            "model_mode": p.model_mode,
            "confidence": p.confidence,
            "fault_class": p.fault_class,
            "updated_at": _now_ist(),
            "capacity_l": spec.capacity_l,
            "used_l": round(a.used_l, 3),
            "reserved_l": round(a.reserved_l, 3),
            "free_l": round(a.free_l, 3),
            "sensor_id": spec.sensor_id,
            "demo_role": spec.demo_role,
            # Real measured tail so the UI plots history, not a synthetic line.
            "recent_c": [round(t, 3) for _, t in list(a.custody_window)[-60:]],
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
            map_x=round(a.map_x, 2),
            map_y=round(a.map_y, 2),
            timestamp=time.time(),
        )

    # ------------------------------------------------------------------ physics

    def step(self) -> None:
        with self._lock:
            self.tick += 1
            dt_min = self.tick_sec / 60.0
            t_abs = (time.time() - self._t0) / 60.0
            for a in self.assets.values():
                self._step_asset(a, dt_min, t_abs)
            self._emit({"type": "state", "state": self.snapshot()})

    def _step_asset(self, a: LiveAsset, dt_min: float, t_abs: float) -> None:
        spec = a.spec
        if not spec.thermal or spec.band is None:
            a.processed = Processed(
                model_mode="location", fault_class="NONE", minutes_to_breach=STABLE_SENTINEL
            )
            a.map_x = min(92.0, max(8.0, a.map_x + self.rng.uniform(-0.15, 0.15)))
            return

        teq = t_eq(spec.band.setpoint, a.door, a.health)
        tau = self.demo_tau_min
        if a.probe_online and a.temperature is not None:
            noise = self.rng.uniform(-0.03, 0.03)
            a.temperature = step_temperature(a.temperature, teq, tau, dt_min) + noise
            a.elapsed_min += dt_min
            a.history.append((t_abs, a.temperature))
            a.temps_for_mkt.append(a.temperature)
            a.custody_window.append((self._sample_clock(), a.temperature))
            a.battery = max(80.0, a.battery - 0.0008)
            if a.temperature < spec.band.low or a.temperature > spec.band.high:
                a.excursion_min += dt_min
            if a.door >= 0.5:
                a.door_open_min += dt_min

        a.processed = self._process(a, teq, tau)
        self._maybe_alert(a)

    def _process(self, a: LiveAsset, teq: float, tau: float) -> Processed:
        spec = a.spec
        assert spec.band is not None
        band = spec.band
        t = a.temperature if a.temperature is not None else band.setpoint
        out_of_band = t < band.low or t > band.high

        if not a.probe_online:
            # Instrumentation fault. If the last known reading was already out of
            # band we are blind AND hot — that is the BOTH case, and only that
            # case may move stock.
            blind_and_hot = out_of_band
            return Processed(
                minutes_to_breach=STABLE_SENTINEL,
                risk_score=64.0 if blind_and_hot else 22.0,
                t_eq_c=round(teq, 3),
                tau_min=tau,
                breach_threshold_c=band.high,
                model_mode="probe_dead",
                confidence=0.95,
                fault_class="BOTH" if blind_and_hot else "PROBE_DEAD",
            )

        heat_min = minutes_to_breach(t, teq, band.high, tau)
        freeze_min = STABLE_SENTINEL
        if band.freeze_critical is not None:
            freeze_min = minutes_to_freeze(t, teq, band.freeze_critical, tau)

        # freeze_critical is always below band.low, so out_of_band already covers a
        # freeze-rail crossing — do not re-test t <= freeze_critical.
        if out_of_band:
            mode = "breached"
            minutes = 0.0
            if t > band.high:
                direction = "heat"
                threshold = band.high
            else:
                direction = "freeze"
                threshold = band.freeze_critical if band.freeze_critical is not None else band.low
        elif freeze_min < heat_min:
            mode = "warming"
            minutes = freeze_min
            direction = "freeze"
            threshold = band.freeze_critical
        elif heat_min < STABLE_SENTINEL:
            mode = "warming"
            minutes = heat_min
            direction = "heat"
            threshold = band.high
        else:
            mode = "stable"
            minutes = STABLE_SENTINEL
            direction = "none"
            threshold = band.high

        window = list(a.custody_window)[-SLOPE_WINDOW:]
        slope = slope_c_per_min([(ts / 60.0, temp) for ts, temp in window])
        mkt = None
        eta = None
        # MKT is a thermal-stress index for pharma-fridge stock only. USP <1079.2>
        # forbids using it to release vaccines or blood, so it never gates a decision.
        if spec.asset_class == "insulin_ilr":
            mkt = mkt_c(list(a.temps_for_mkt))
            if mkt is not None:
                eta = remaining_efficacy_pct(mkt, max(a.elapsed_min, 0.05))

        if out_of_band:
            fault = "THERMAL_EXCURSION"
        elif a.door >= 0.5 and minutes >= DOOR_ESCALATE_MIN:
            # Air still legal: close the door. Do not evacuate.
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
            breach_threshold_c=threshold,
            breach_direction=direction,
            model_mode=mode,
            confidence=round(conf, 3),
            fault_class=fault,
        )

    # ------------------------------------------------------------------ inputs

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Accept external (ESP32 / MQTT bridge) telemetry."""
        with self._lock:
            aid = payload.get("asset_id")
            if not isinstance(aid, str) or not aid.strip():
                raise ValueError("missing asset_id")
            a = self.assets.get(aid)
            if not a:
                raise KeyError(aid)
            if payload.get("temperature") is not None:
                a.temperature = _num(payload["temperature"], "temperature", aid)
                a.custody_window.append((self._sample_clock(), a.temperature))
            if "compressor_health" in payload:
                a.health = _num(payload["compressor_health"], "compressor_health", aid, 0.0, 1.0)
            if "door_status" in payload:
                a.door = 1.0 if str(payload["door_status"]).upper() == "OPEN" else 0.0
            if "probe_online" in payload:
                a.probe_online = bool(payload["probe_online"])
            if a.spec.band:
                teq = t_eq(a.spec.band.setpoint, a.door, a.health)
                a.processed = self._process(a, teq, self.demo_tau_min)
                self._maybe_alert(a)
            pub = self._asset_public(a)
            self._emit({"type": "ingest", "asset": pub})
            return pub

    def anomaly(self, asset_id: str, kind: str) -> dict[str, Any]:
        with self._lock:
            return self._anomaly(asset_id, kind)

    def _anomaly(self, asset_id: str, kind: str) -> dict[str, Any]:
        if kind == "reset" and asset_id.upper() == "ALL":
            return self._reset_all()
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
            self._reset_asset(a)
        else:
            raise ValueError(f"unknown kind {kind!r}; valid: {', '.join(ANOMALY_KINDS)}")
        if a.spec.band and a.temperature is not None:
            # Recompute now so T_eq jumps before the next tick.
            teq = t_eq(a.spec.band.setpoint, a.door, a.health)
            a.processed = self._process(a, teq, self.demo_tau_min)
            self._maybe_alert(a)
        self._emit({"type": "anomaly", "asset_id": asset_id, "kind": kind, "state": self.snapshot()})
        return {"ok": True, "asset_id": asset_id, "kind": kind}

    def reset_all(self) -> dict[str, Any]:
        """Return the whole plant to its opening state so the demo can be re-run."""
        with self._lock:
            return self._reset_all()

    def _reset_all(self) -> dict[str, Any]:
        for a in self.assets.values():
            self._reset_asset(a, restock=False)
        for u in self.inventory:
            u["asset_id"] = u["home_asset_id"]
        for s in self.staff:
            s["busy"] = False
        self.alerts.clear()
        self.missions.clear()
        self.tickets.clear()
        self._active_alerts.clear()
        self._recompute_capacity()
        # tick and audit stay: tick is a monotonic clock, audit is append-only.
        # Do not clear them on reset.
        self._audit("command", "plant.reset", "dirty", "clean", "full plant reset for next run")
        self._emit({"type": "reset", "state": self.snapshot()})
        return {"ok": True, "asset_id": "ALL", "kind": "reset"}

    def _reset_asset(self, a: LiveAsset, restock: bool = True) -> None:
        aid = a.spec.asset_id
        a.health = 1.0
        a.door = 0.0
        a.probe_online = True
        a.battery = OPENING_BATTERY_PCT
        if a.spec.band:
            a.temperature = a.spec.band.setpoint
        a.processed = Processed(
            model_mode="stable" if a.spec.thermal else "location",
            minutes_to_breach=STABLE_SENTINEL,
        )
        a.history.clear()
        a.temps_for_mkt.clear()
        a.custody_window.clear()
        a.elapsed_min = 0.0
        a.excursion_min = 0.0
        a.door_open_min = 0.0

        if not restock:
            return

        for m in self.missions:
            if m["from_asset"] == aid and m["status"] not in TERMINAL_MISSION:
                m["status"] = "cancelled"
                self._release_staff(m["staff_id"])
        for u in self.inventory:
            if u["home_asset_id"] == aid:
                u["asset_id"] = aid
        self.alerts = [al for al in self.alerts if al["asset_id"] != aid]
        self.tickets = [t for t in self.tickets if t["asset_id"] != aid]
        self._active_alerts = {k for k in self._active_alerts if k[0] != aid}
        self._recompute_capacity()
        self._audit("sim", "anomaly.reset", "fault", "clear", f"{aid} reset and restocked")

    def _recompute_capacity(self) -> None:
        """Single source of truth: stock from inventory, holds from open missions."""
        for a in self.assets.values():
            a.used_l = a.spec.baseline_used_l + sum(
                u["volume_l"] for u in self.inventory if u["asset_id"] == a.spec.asset_id
            )
            a.reserved_l = 0.0
        for m in self.missions:
            if m["status"] in TERMINAL_MISSION:
                continue
            dst = self.assets.get(m["to_asset"])
            if dst:
                dst.reserved_l += sum(u["volume_l"] for u in m["units"])

    # ------------------------------------------------------------------ alerts

    def _maybe_alert(self, a: LiveAsset) -> None:
        p = a.processed
        aid = a.spec.asset_id

        if p.fault_class == "PROBE_DEAD":
            if self._claim_alert(aid, "PROBE_DEAD"):
                alert = self._push_alert(
                    aid,
                    "PROBE_DEAD",
                    "critical",
                    f"{a.spec.label}: probe dead (LWT). Ticket only — do not move stock.",
                )
                self._open_ticket(a, alert["id"], kind="instrumentation")
            return

        if p.fault_class == "BOTH":
            if self._claim_alert(aid, "BOTH"):
                alert = self._push_alert(
                    aid,
                    "BOTH",
                    "critical",
                    f"{a.spec.label}: blind and out of band. Evacuate and re-instrument.",
                )
                self._open_mission(a, alert["id"])
            return

        if p.fault_class == "NONE":
            self._active_alerts.discard((aid, "DOOR"))
            return

        if p.fault_class == "DOOR_OPEN":
            if self._claim_alert(aid, "DOOR"):
                air = "unknown" if a.temperature is None else f"{a.temperature:.1f}°C"
                self._push_alert(
                    aid,
                    "DOOR_OPEN",
                    "warn",
                    f"{a.spec.label}: door open, air still {air} in band. Close the door — "
                    f"do not move stock (countdown {p.minutes_to_breach:.1f} min).",
                )
            return

        if p.fault_class != "THERMAL_EXCURSION":
            return
        if not self._claim_alert(aid, "THERMAL"):
            return

        kind = "THERMAL_EXCURSION" if p.model_mode == "breached" else "THERMAL_PREDICT"
        air = "unknown" if a.temperature is None else f"{a.temperature:.1f}°C"
        if p.model_mode == "breached":
            msg = f"{a.spec.label}: out of band at {air}. Quarantine and evacuate."
        else:
            verb = "Freeze" if p.breach_direction == "freeze" else "Breach"
            msg = (
                f"{a.spec.label}: T_eq={p.t_eq_c}°C. {verb} in {p.minutes_to_breach:.1f} min "
                f"(air still {air}, band {a.spec.band.low}–{a.spec.band.high}°C)."
            )
        alert = self._push_alert(aid, kind, "critical", msg)
        self._open_mission(a, alert["id"])

    def _claim_alert(self, asset_id: str, fault_key: str) -> bool:
        key = (asset_id, fault_key)
        if key in self._active_alerts:
            return False
        self._active_alerts.add(key)
        return True

    def _push_alert(self, asset_id: str, kind: str, severity: str, message: str) -> dict[str, Any]:
        alert = {
            "id": _id("al"),
            "asset_id": asset_id,
            "kind": kind,
            "severity": severity,
            "message": message,
            "acked_at": None,
            "created_at": _now_ist(),
        }
        self.alerts.append(alert)
        self._emit({"type": "alert", "alert": alert})
        return alert

    def _open_ticket(self, a: LiveAsset, alert_id: str, kind: str) -> dict[str, Any]:
        instrumentation = kind == "instrumentation"
        ticket = {
            "id": _id("tk"),
            "alert_id": alert_id,
            "asset_id": a.spec.asset_id,
            "kind": kind,
            "duty_cycle": round(0.55 + 0.4 * (1 - a.health), 2),
            "twin_duty_cycle": 0.55,
            "parts": "probe, logger, loom" if instrumentation else "start-relay, run-cap",
            "sla_min": 45,
            "kwh_hold_30m": kwh_hold(a.health),
            "kwh_move": 0.0 if instrumentation else kwh_move(),
            "created_at": _now_ist(),
        }
        self.tickets.append(ticket)
        reason = (
            f"PROBE_DEAD {a.spec.asset_id} — instrument only, stock stays put"
            if instrumentation
            else f"thermal {a.spec.asset_id} — compressor service"
        )
        self._audit("plant", "ticket.open", "", ticket["parts"], reason)
        self._emit({"type": "ticket", "ticket": ticket, "alert_id": alert_id})
        return ticket

    # ------------------------------------------------------------------ dispatch

    def _peer_need_l(self, src: AssetSpec) -> float:
        """Largest single peer vault that shares this backup pool.

        We keep headroom for it, so a second failure is not stranded.
        """
        needs = [
            sum(u["volume_l"] for u in self.inventory if u["asset_id"] == other.asset_id)
            for other in ASSETS
            if other.asset_id != src.asset_id and other.thermal and same_band(src, other)
        ]
        return max(needs) if needs else 0.0

    def _open_mission(self, a: LiveAsset, alert_id: str) -> None:
        open_here = [
            m
            for m in self.missions
            if m["from_asset"] == a.spec.asset_id and m["status"] not in TERMINAL_MISSION
        ]
        if open_here:
            self._audit(
                "plant",
                "mission.escalate",
                open_here[0]["id"],
                a.processed.fault_class,
                f"{a.spec.asset_id} already has an open mission; not opening a second",
            )
            return

        units = [u for u in self.inventory if u["asset_id"] == a.spec.asset_id]
        if not units:
            self._open_ticket(a, alert_id, kind="thermal")
            return

        need_l = sum(u["volume_l"] for u in units)
        remaining = {aid: la.free_l for aid, la in self.assets.items()}
        other_need = self._peer_need_l(a.spec)
        dst = pick_backup(a.spec, remaining, {}, need_l, other_need)
        if dst is None:
            self._open_ticket(a, alert_id, kind="thermal")
            self._push_alert(
                a.spec.asset_id,
                "THERMAL_EXCURSION",
                "critical",
                f"{a.spec.label}: no backup vault has {need_l:.2f} L free. Escalate to on-call.",
            )
            return

        staff = self._assign_staff(cert_for(a.spec.asset_class), a.spec.floor)
        if staff is None:
            self._open_ticket(a, alert_id, kind="thermal")
            self._push_alert(
                a.spec.asset_id,
                "THERMAL_EXCURSION",
                "critical",
                f"{a.spec.label}: no certified courier is available. Move queued for escalation.",
            )
            return

        free_before = self.assets[dst.asset_id].free_l
        cr = cascade_risk(free_before - need_l, other_need)
        self.assets[dst.asset_id].reserved_l += need_l
        d = distance_m(a.spec, dst)
        ticket = self._open_ticket(a, alert_id, kind="thermal")
        mission = {
            "id": _id("ms"),
            "alert_id": alert_id,
            "from_asset": a.spec.asset_id,
            "from_label": a.spec.label,
            "to_asset": dst.asset_id,
            "to_label": dst.label,
            # Snapshot, not a live reference: a custody certificate must record the
            # product as it was at dispatch, not follow it to its destination.
            "units": [dict(u) for u in units],
            "staff_id": staff["id"] if staff else None,
            "staff_name": staff["name"] if staff else None,
            "status": "proposed",
            "eta_min": round(1.5 + d / 40.0, 1),
            "distance_m": round(d, 1),
            "ticket": ticket,
            "scan_step": "unit",
            "last_reject": None,
            "routing": {
                "need_l": round(need_l, 3),
                "dest_free_before_l": round(free_before, 3),
                "dest_free_after_l": round(free_before - need_l, 3),
                "peer_headroom_needed_l": round(other_need, 3),
                "cascade_risk": cr,
                "note": (
                    "destination cannot absorb a second failure — next vault will cascade"
                    if cr >= 1.0
                    else "destination retains headroom for a peer failure"
                ),
            },
            "events": [],
            "created_at": _now_ist(),
        }
        self._log_mission_event(mission, "plant", a.spec.location, "proposed")
        self.missions.append(mission)
        self._audit(
            "plant",
            "mission.propose",
            a.spec.asset_id,
            dst.asset_id,
            f"MOVE {len(units)} units ({need_l:.2f} L), cascade_risk={cr}",
        )
        self._emit({"type": "mission", "mission": mission})

    def _assign_staff(self, cert: str, floor: int) -> dict[str, Any] | None:
        """Certification is a hard requirement — no cross-cert fallback."""
        free = [s for s in self.staff if s["cert"] == cert and not s["busy"]]
        if not free:
            return None
        free.sort(key=lambda s: (abs(s["floor"] - floor), s["id"]))
        pick = free[0]
        pick["busy"] = True
        return pick

    def _release_staff(self, staff_id: str | None) -> None:
        for s in self.staff:
            if s["id"] == staff_id:
                s["busy"] = False

    def _log_mission_event(self, m: dict[str, Any], who: str, location: str, action: str) -> None:
        m["events"].append({"who": who, "when": _now_ist(), "location": location, "action": action})

    # ------------------------------------------------------------------ custody

    def accept_mission(self, mission_id: str, actor: str = "nurse-rao") -> dict[str, Any]:
        with self._lock:
            m = self._mission(mission_id)
            if m["status"] != "proposed":
                return m
            m["status"] = "accepted"
            m["scan_step"] = "unit"
            who = m["staff_name"] or "unassigned"
            self._log_mission_event(m, who, self.assets[m["from_asset"]].spec.location, "accepted")
            self._audit(actor, "mission.accept", "proposed", "accepted", m["id"])
            self._emit({"type": "mission", "mission": m})
            return m

    def scan_mission(self, mission_id: str, code: str, actor: str = "nurse-rao") -> dict[str, Any]:
        with self._lock:
            return self._scan_mission(mission_id, code, actor)

    def _scan_mission(self, mission_id: str, code: str, actor: str) -> dict[str, Any]:
        m = self._mission(mission_id)
        if m["status"] == "complete":
            self._emit({"type": "scan", "ok": True, "mission": m})
            return m
        if m["status"] not in {"accepted", "checkout", "in_transit"}:
            m["last_reject"] = "Accept the MOVE first."
            self._emit({"type": "scan", "ok": False, "mission": m})
            return m

        token = code.strip().upper()
        expected_units = {u["unit_id"] for u in m["units"]}
        step = m["scan_step"]
        who = m["staff_name"] or "unassigned"

        def fail(reason: str) -> dict[str, Any]:
            m["last_reject"] = reason
            scanned = token.split(":", 1)[1] if ":" in token else token
            self._log_mission_event(m, who, scanned, f"scan rejected — {reason}")
            self._audit(actor, "scan.reject", token, reason, m["id"])
            self._emit({"type": "scan", "ok": False, "mission": m})
            return m

        if token.startswith("UNIT:"):
            uid = token.split(":", 1)[1]
            if step != "unit":
                return fail(f"Scan the vault next, not a bag (step: {step}).")
            if uid not in expected_units:
                return fail(f"Wrong unit. This move covers {', '.join(sorted(expected_units))}.")
            m["scan_step"] = "source"
            m["status"] = "checkout"
            m["last_reject"] = None
            self._log_mission_event(m, who, m["from_asset"], f"unit verified {uid}")
            self._audit(actor, "scan.unit", "", uid, m["id"])
        elif token.startswith("VAULT:"):
            vid = token.split(":", 1)[1]
            if step == "source":
                if vid != m["from_asset"]:
                    return fail(f"Wrong vault. Checkout is {m['from_asset']}.")
                m["scan_step"] = "dest"
                m["status"] = "in_transit"
                m["last_reject"] = None
                self._log_mission_event(m, who, vid, "checked out of source")
                self._audit(actor, "scan.source", m["from_asset"], vid, m["id"])
            elif step == "dest":
                if vid != m["to_asset"]:
                    return fail(f"Wrong vault. Destination is {m['to_asset']}.")
                m["scan_step"] = "done"
                m["status"] = "complete"
                m["last_reject"] = None
                self._complete_move(m)
                self._log_mission_event(m, who, vid, "checked in at destination")
                self._audit(actor, "scan.dest", m["from_asset"], vid, m["id"])
            else:
                return fail("Scan the unit QR first.")
        else:
            return fail("Unknown QR. Expected UNIT:… or VAULT:…")

        self._emit({"type": "scan", "ok": True, "mission": m})
        return m

    def _complete_move(self, m: dict[str, Any]) -> None:
        moved = {u["unit_id"] for u in m["units"]}
        for u in self.inventory:
            if u["unit_id"] in moved:
                u["asset_id"] = m["to_asset"]
        self._release_staff(m["staff_id"])
        self._recompute_capacity()

    def ack_alert(self, alert_id: str, actor: str = "command") -> dict[str, Any]:
        with self._lock:
            return self._ack_alert(alert_id, actor)

    def _ack_alert(self, alert_id: str, actor: str) -> dict[str, Any]:
        for al in self.alerts:
            if al["id"] == alert_id:
                al["acked_at"] = _now_ist()
                self._audit(actor, "alert.ack", "open", "acked", alert_id)
                self._emit({"type": "alert", "alert": al})
                return al
        raise KeyError(alert_id)

    def custody(self, mission_id: str) -> dict[str, Any]:
        m = self._mission(mission_id)
        src = self.assets[m["from_asset"]]
        dst = self.assets[m["to_asset"]]
        band = src.spec.band
        temps = [t for _, t in src.custody_window] or (
            [src.temperature] if src.temperature is not None else []
        )

        excursion = src.excursion_min > 0.0
        blind = not src.probe_online
        if excursion:
            event_class = "product excursion (outside labelled band)"
            disposition = "QUARANTINE — DO NOT USE pending QA review"
        elif blind:
            event_class = "instrumentation fault (temperature unverified)"
            disposition = "QUARANTINE — probe unverified"
        elif src.door_open_min > 0.0:
            event_class = "door-open event (air only, core lag not exceeded)"
            disposition = "RELEASED — door event logged, no product excursion"
        else:
            event_class = "in-spec — predictive relocation before breach"
            disposition = "RELEASED — no excursion recorded"

        body = {
            "doc_id": f"COC-{mission_id[-8:].upper()}",
            "product": m["units"],
            "from_site": f"{self.hospital} · {src.spec.label} · {src.spec.location}",
            "to_site": f"{self.hospital} · {dst.spec.label} · {dst.spec.location}",
            "custody": m["events"],
            "band": f"{band.low}–{band.high}°C" if band else "n/a",
            "min_c": round(min(temps), 2) if temps else None,
            "max_c": round(max(temps), 2) if temps else None,
            "time_out_of_range_min": round(src.excursion_min, 2),
            "observation_window_min": round(len(src.custody_window) * self.tick_sec / 60.0, 2),
            "mkt_c": src.processed.mkt_c,
            "sensor_id": src.spec.sensor_id or f"DDL-{m['from_asset'][-2:]}",
            "calibration_date": src.spec.calibration_date,
            "event_class": event_class,
            "disposition": disposition,
            "routing": m["routing"],
            "audit": [ev for ev in self.audit if m["id"] in (ev["reason"], ev["new_value"])][-12:]
            or self.audit[-12:],
            "footer": (
                "Audit-trail controls inspired by 21 CFR Part 11.10 and CDSCO GDP §15.7. "
                "Not FDA-certified, not NABH/WHO PQS accredited. MKT is a thermal-stress "
                "index and is never used to release blood or vaccines."
            ),
            "mission_status": m["status"],
            "draft": m["status"] != "complete",
        }
        if body["draft"]:
            body["disposition"] = (
                "DRAFT — transfer not completed, no disposition asserted"
            )
            body["event_class"] = (
                f"DRAFT — transfer not completed (mission {m['status']})"
            )
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
        self.audit.append(
            {
                "id": _id("au"),
                "actor": actor,
                "action": action,
                "old_value": old,
                "new_value": new,
                "reason": reason,
                "payload_hash": _hash(f"{actor}|{action}|{old}|{new}|{reason}"),
                "created_at": _now_ist(),
            }
        )
