export type AssetClass =
  | "blood_rbc"
  | "vaccine_ilr"
  | "insulin_ilr"
  | "platelet"
  | "plasma_ffp"
  | "walkin_cold"
  | "crash_cart";

export type DoorStatus = "OPEN" | "CLOSED";

export type ModelMode = "warming" | "stable" | "breached" | "probe_dead" | "location";

export type FaultClass = "NONE" | "PROBE_DEAD" | "THERMAL_EXCURSION" | "BOTH" | "DOOR_OPEN";

export type Disposition = "OK" | "quarantine" | "rejected";

export type MissionStatus =
  | "proposed"
  | "accepted"
  | "checkout"
  | "in_transit"
  | "complete"
  | "rejected";

export type AnomalyKind = "compressor" | "door" | "lwt" | "reset";

export interface TelemetryPayload {
  topic: string;
  asset_id: string;
  asset_class: AssetClass;
  location: string;
  floor: number;
  zone: string;
  temperature: number | null;
  door_status: DoorStatus;
  compressor_health: number;
  battery_pct: number;
  probe_online: boolean;
  map_x: number;
  map_y: number;
  timestamp: number;
}

export interface ProcessedReading {
  minutes_to_breach: number;
  risk_score: number;
  remaining_efficacy_pct: number | null;
  t_eq_c: number | null;
  tau_min: number | null;
  mkt_c: number | null;
  dT_dt_c_per_min: number | null;
  predicted_T_60s_c: number | null;
  breach_threshold_c: number | null;
  model_mode: ModelMode;
  confidence: number;
  fault_class: FaultClass;
}

export interface AssetState extends TelemetryPayload, ProcessedReading {
  label: string;
  band_low_c: number | null;
  band_high_c: number | null;
  setpoint_c: number | null;
  updated_at: string;
}

export interface InventoryUnit {
  unit_id: string;
  asset_id: string;
  product_name: string;
  blood_type: string | null;
  lot: string;
  expiry: string;
  volume_l: number;
  temp_band: string;
}

export interface StaffMember {
  id: string;
  name: string;
  cert: "blood" | "vaccine" | "maintenance";
  floor: number;
  busy: boolean;
}

export interface Ticket {
  asset_id: string;
  kind: string;
  duty_cycle: number;
  twin_duty_cycle: number;
  parts: string;
  sla_min: number;
  kwh_hold_30m: number;
  kwh_move: number;
}

export interface Mission {
  id: string;
  alert_id: string;
  from_asset: string;
  to_asset: string;
  units: InventoryUnit[];
  staff_id: string | null;
  staff_name: string | null;
  status: MissionStatus;
  eta_min: number;
  distance_m: number;
  ticket: Ticket;
  scan_step: "unit" | "source" | "dest" | "done";
  last_reject: string | null;
  created_at: string;
}

export interface Alert {
  id: string;
  asset_id: string;
  kind: FaultClass | "THERMAL_PREDICT";
  severity: "info" | "warn" | "critical";
  message: string;
  acked_at: string | null;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  actor: string;
  action: string;
  old_value: string;
  new_value: string;
  reason: string;
  payload_hash: string;
  created_at: string;
}

export interface PlantState {
  site_id: string;
  hospital: string;
  tick: number;
  assets: AssetState[];
  alerts: Alert[];
  missions: Mission[];
  inventory: InventoryUnit[];
  staff: StaffMember[];
  audit: AuditEvent[];
}
