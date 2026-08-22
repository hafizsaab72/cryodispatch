/**
 * CryoDispatch ingest — Deno Edge Function.
 * Mirrors apps/sim thermal + greedy dispatch. Rules do not live in the browser.
 *
 * POST JSON telemetry (MQTT-shaped). Upserts asset_state. Appends telemetry
 * every ~15s or on anomaly. Opens alerts / missions.
 */
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const DH_OVER_R = 10000;
const STABLE = 9999;
const TAU = Number(Deno.env.get("DEMO_TAU_MIN") ?? "2");

type Band = { low: number; high: number; set: number; freeze?: number };

const BANDS: Record<string, Band> = {
  blood_rbc: { low: 2, high: 6, set: 4 },
  vaccine_ilr: { low: 2, high: 8, set: 5, freeze: 0 },
  insulin_ilr: { low: 2, high: 8, set: 5, freeze: 0 },
  platelet: { low: 20, high: 24, set: 22 },
  plasma_ffp: { low: -40, high: -30, set: -35 },
  walkin_cold: { low: 2, high: 8, set: 5, freeze: 0 },
};

function tEq(set: number, door: number, health: number) {
  return set + 6.5 * door + 4.0 * (1 - health) + 0.04 * (24 - set);
}

function minutesToBreach(t: number, teq: number, th: number, tau: number) {
  if (t >= th) return { m: 0, mode: "breached" };
  if (teq <= th) return { m: STABLE, mode: "stable" };
  const ratio = (th - teq) / (t - teq);
  if (ratio <= 0) return { m: 0, mode: "breached" };
  return { m: Math.max(0, -tau * Math.log(ratio)), mode: "warming" };
}

function mktC(temps: number[]) {
  if (!temps.length) return null;
  const acc = temps.reduce((s, c) => s + Math.exp(-DH_OVER_R / (c + 273.15)), 0);
  const mean = acc / temps.length;
  if (mean <= 0) return null;
  return DH_OVER_R / -Math.log(mean) - 273.15;
}

function process(body: Record<string, unknown>) {
  const cls = String(body.asset_class ?? "blood_rbc");
  const band = BANDS[cls];
  const probe = body.probe_online !== false;
  if (!band || body.temperature == null) {
    return {
      minutes_to_breach: STABLE,
      risk_score: 0,
      remaining_efficacy_pct: null,
      t_eq_c: null,
      tau_min: TAU,
      mkt_c: null,
      dt_dt_c_per_min: null,
      predicted_t_60s_c: null,
      breach_threshold_c: band?.high ?? null,
      model_mode: cls === "crash_cart" ? "location" : "stable",
      confidence: 0.4,
      fault_class: "NONE",
    };
  }
  const t = Number(body.temperature);
  const door = String(body.door_status).toUpperCase() === "OPEN" ? 1 : 0;
  const health = Number(body.compressor_health ?? 1);
  const teq = tEq(band.set, door, health);
  if (!probe) {
    return {
      minutes_to_breach: STABLE,
      risk_score: 22,
      remaining_efficacy_pct: null,
      t_eq_c: round(teq),
      tau_min: TAU,
      mkt_c: null,
      dt_dt_c_per_min: null,
      predicted_t_60s_c: null,
      breach_threshold_c: band.high,
      model_mode: "probe_dead",
      confidence: 0.95,
      fault_class: "PROBE_DEAD",
    };
  }
  const heat = minutesToBreach(t, teq, band.high, TAU);
  let minutes = heat.m;
  let mode = heat.mode;
  if (t < band.low || t > band.high || (band.freeze != null && t <= band.freeze)) {
    mode = "breached";
    minutes = 0;
  }
  const u = 1 - Math.min(Math.max(minutes / 30, 0), 1);
  const risk = 100 * (0.55 * u + 0.15 * door);
  let fault = "NONE";
  if (mode === "probe_dead") fault = "PROBE_DEAD";
  else if (t < band.low || t > band.high) fault = "THERMAL_EXCURSION";
  else if (door && mode === "stable") fault = "DOOR_OPEN";
  else if (mode === "warming") fault = "THERMAL_EXCURSION";
  const pred = teq + (t - teq) * Math.exp(-1 / TAU);
  const mk = cls === "insulin_ilr" ? mktC([t]) : null;
  return {
    minutes_to_breach: round(minutes),
    risk_score: round(risk),
    remaining_efficacy_pct: null,
    t_eq_c: round(teq),
    tau_min: TAU,
    mkt_c: mk == null ? null : round(mk),
    dt_dt_c_per_min: null,
    predicted_t_60s_c: round(pred),
    breach_threshold_c: band.high,
    model_mode: mode,
    confidence: 0.7,
    fault_class: fault,
  };
}

function round(n: number) {
  return Math.round(n * 1000) / 1000;
}

function backupFor(fromId: string) {
  if (fromId === "FREEZER_BLOOD_04") return "FREEZER_BLOOD_03";
  if (fromId === "FREEZER_BLOOD_05") return "WALKIN_COLD_02";
  return "WALKIN_COLD_01";
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: cors() });
  }
  const body = await req.json();
  const processed = process(body);
  const url = Deno.env.get("SUPABASE_URL")!;
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const sb = createClient(url, key);

  const row = {
    asset_id: body.asset_id,
    asset_class: body.asset_class,
    label: body.label ?? body.asset_id,
    location: body.location,
    floor: body.floor,
    zone: body.zone,
    temperature: body.temperature,
    door_status: body.door_status,
    compressor_health: body.compressor_health,
    battery_pct: body.battery_pct,
    probe_online: body.probe_online !== false,
    map_x: body.map_x,
    map_y: body.map_y,
    topic: body.topic,
    ...processed,
    band_low_c: BANDS[String(body.asset_class)]?.low ?? null,
    band_high_c: BANDS[String(body.asset_class)]?.high ?? null,
    updated_at: new Date().toISOString(),
  };

  await sb.from("asset_state").upsert(row);

  const now = Date.now();
  const last = Number(body._last_history_at ?? 0);
  const anomaly = processed.fault_class !== "NONE";
  if (anomaly || now - last > 15000) {
    await sb.from("telemetry").insert({ asset_id: body.asset_id, payload: { ...body, ...processed } });
  }

  if (processed.fault_class === "PROBE_DEAD" || processed.fault_class === "THERMAL_EXCURSION") {
    const alertId = `al-${body.asset_id}-${processed.fault_class}`;
    const { data: existing } = await sb.from("alerts").select("id").eq("id", alertId).maybeSingle();
    if (!existing) {
      const message = processed.fault_class === "PROBE_DEAD"
        ? `${body.asset_id}: probe dead (LWT). Ticket only — do not move stock.`
        : `${body.asset_id}: T_eq=${processed.t_eq_c}°C. Breach in ${processed.minutes_to_breach} min.`;
      await sb.from("alerts").insert({
        id: alertId,
        asset_id: body.asset_id,
        kind: processed.fault_class,
        severity: "critical",
        message,
      });
      if (processed.fault_class === "THERMAL_EXCURSION") {
        const to = backupFor(String(body.asset_id));
        await sb.from("missions").insert({
          id: `ms-${body.asset_id}`,
          alert_id: alertId,
          from_asset: body.asset_id,
          to_asset: to,
          units: [],
          staff_id: "nurse-rao",
          staff_name: "Nurse Rao",
          status: "proposed",
          ticket: { kind: "thermal", parts: "start-relay, run-cap", sla_min: 45 },
        });
      }
      await sb.from("audit_events").insert({
        id: `au-${alertId}`,
        actor: "ingest",
        action: "alert.open",
        old_value: "NONE",
        new_value: processed.fault_class,
        reason: String(body.asset_id),
        payload_hash: "edge",
      });
    }
  }

  return new Response(JSON.stringify({ ok: true, processed }), {
    headers: { ...cors(), "Content-Type": "application/json" },
  });
});

function cors() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  };
}
