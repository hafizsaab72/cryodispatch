from __future__ import annotations

from pydantic import BaseModel, Field


class Telemetry(BaseModel):
    topic: str
    asset_id: str
    asset_class: str
    location: str
    floor: int
    zone: str
    temperature: float | None
    door_status: str
    compressor_health: float = Field(ge=0, le=1)
    battery_pct: float
    probe_online: bool = True
    map_x: float
    map_y: float
    timestamp: float


class Processed(BaseModel):
    minutes_to_breach: float = 9999.0
    risk_score: float = 0.0
    remaining_efficacy_pct: float | None = None
    t_eq_c: float | None = None
    tau_min: float | None = None
    mkt_c: float | None = None
    dT_dt_c_per_min: float | None = None
    predicted_T_60s_c: float | None = None
    breach_threshold_c: float | None = None
    # Which rail the countdown is actually running to: "heat" | "freeze" | "none".
    breach_direction: str = "none"
    model_mode: str = "stable"
    confidence: float = 0.4
    fault_class: str = "NONE"
