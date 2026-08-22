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

/** Which temperature rail the countdown is closing on. */
export type BreachDirection = "heat" | "freeze" | "none";

/**
 * The plant writes a sentence, not an enum: "RELEASED — no excursion recorded",
 * "QUARANTINE — DO NOT USE pending QA review", "DRAFT — …" for an unfinished
 * transfer. The prefix is the machine-readable part.
 */
export type Disposition = `RELEASED — ${string}` | `QUARANTINE — ${string}` | `DRAFT — ${string}`;

export type MissionStatus =
  | "proposed"
  | "accepted"
  | "checkout"
  | "in_transit"
  | "complete"
  | "cancelled"
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
  /** Least-squares slope; null until there are enough samples. */
  dT_dt_c_per_min: number | null;
  predicted_T_60s_c: number | null;
  /** Whichever rail `breach_direction` names, not always the ceiling. */
  breach_threshold_c: number | null;
  model_mode: ModelMode;
  confidence: number;
  fault_class: FaultClass;
  /** Optional while the plant rolls it out. */
  breach_direction?: BreachDirection;
}

export interface AssetState extends TelemetryPayload, ProcessedReading {
  label: string;
  band_low_c: number | null;
  band_high_c: number | null;
  setpoint_c: number | null;
  updated_at: string;
  capacity_l: number;
  used_l: number;
  reserved_l: number;
  free_l: number;
  sensor_id: string;
  demo_role: string | null;
  recent_c: number[];
}

export interface InventoryUnit {
  unit_id: string;
  asset_id: string;
  home_asset_id?: string;
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

/** `string` stays open so a new plant ticket kind is not a compile error. */
export type TicketKind = "thermal" | "instrumentation" | (string & {});

export interface Ticket {
  id: string;
  alert_id: string;
  asset_id: string;
  kind: TicketKind;
  duty_cycle: number;
  twin_duty_cycle: number;
  parts: string;
  sla_min: number;
  kwh_hold_30m: number;
  kwh_move: number;
  created_at: string;
}

export interface Routing {
  need_l: number;
  dest_free_before_l: number;
  dest_free_after_l: number;
  peer_headroom_needed_l: number;
  cascade_risk: number;
  note: string;
}

export interface CustodyEvent {
  who: string;
  when: string;
  location: string;
  action: string;
}

export interface Mission {
  id: string;
  alert_id: string;
  from_asset: string;
  from_label: string;
  to_asset: string;
  to_label: string;
  units: InventoryUnit[];
  staff_id: string | null;
  staff_name: string | null;
  status: MissionStatus;
  eta_min: number;
  distance_m: number;
  ticket: Ticket;
  scan_step: "unit" | "source" | "dest" | "done";
  last_reject: string | null;
  routing: Routing;
  events: CustodyEvent[];
  created_at: string;
}

/** `string` stays open so a new plant alert kind is not a compile error. */
export type AlertKind = FaultClass | "THERMAL_PREDICT" | (string & {});

export interface Alert {
  id: string;
  asset_id: string;
  kind: AlertKind;
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

/** The body of `GET /api/custody/{missionId}` — the chain-of-custody certificate. */
export interface CustodyDocument {
  doc_id: string;
  product: InventoryUnit[];
  from_site: string;
  to_site: string;
  custody: CustodyEvent[];
  band: string;
  min_c: number | null;
  max_c: number | null;
  time_out_of_range_min: number;
  observation_window_min: number;
  mkt_c: number | null;
  sensor_id: string;
  calibration_date: string;
  event_class: string;
  disposition: Disposition;
  routing: Routing;
  audit: AuditEvent[];
  footer: string;
  payload_hash: string;
  /** Optional while the plant rolls it out. */
  mission_status?: string;
  /** True when the transfer never completed; `disposition` then starts "DRAFT — ". */
  draft?: boolean;
}

export interface PlantState {
  site_id: string;
  hospital: string;
  tick: number;
  assets: AssetState[];
  alerts: Alert[];
  missions: Mission[];
  tickets: Ticket[];
  inventory: InventoryUnit[];
  staff: StaffMember[];
  audit: AuditEvent[];
}
