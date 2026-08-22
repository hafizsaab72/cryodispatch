import type { AssetState } from "@cryodispatch/shared";
import { Line, LineChart, ReferenceLine, ResponsiveContainer, YAxis } from "recharts";

const STABLE = 9000;

export function Gauge({ asset }: { asset: AssetState | undefined }) {
  if (!asset) {
    return <div className="text-mute p-6 text-sm">Select a vault on the floor map.</div>;
  }

  const mins = asset.minutes_to_breach;
  const countdown = mins >= STABLE ? null : mins;
  const inBand =
    asset.temperature != null &&
    asset.band_low_c != null &&
    asset.band_high_c != null &&
    asset.temperature >= asset.band_low_c &&
    asset.temperature <= asset.band_high_c;
  // Freeze is as fatal as heat for an alum-adjuvanted vaccine, so name the rail.
  const freezing = asset.breach_direction === "freeze";
  const railName = freezing ? "freeze floor" : "breach ceiling";

  const series = asset.recent_c.map((v, i) => ({ i, v }));

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div>
        <div className="text-mute font-mono text-xs tracking-widest uppercase">{asset.asset_id}</div>
        <div className="text-xl font-semibold">{asset.label}</div>
        <div className="text-mute text-sm">{asset.location}</div>
      </div>

      {/* The whole pitch is this pair: a countdown while the air is still legal. */}
      <div className="border-line bg-ink/40 rounded-xl border px-4 py-3">
        <div className="text-mute text-xs tracking-wider uppercase">
          {freezing ? "Time to freeze rail" : "Time to breach"}
        </div>
        <div
          className={`font-mono text-5xl tabular-nums ${countdown == null ? "text-ok" : countdown < 10 ? "text-hot" : "text-warn"}`}
        >
          {countdown == null ? "stable" : `${countdown.toFixed(1)}m`}
        </div>
        {freezing && countdown != null ? (
          <div className="mt-1 text-sm font-semibold text-[#9aa8ff]">
            Falling toward the freeze floor {fmt(asset.breach_threshold_c, "°C")} — freezing ruins
            alum-adjuvanted vaccine.
          </div>
        ) : null}
        {asset.band_low_c != null && asset.band_high_c != null ? (
          <div
            className={`mt-2 inline-block rounded px-2 py-1 font-mono text-sm ${
              asset.temperature == null
                ? "bg-[#7b8cff]/25 text-[#9aa8ff]"
                : inBand
                  ? "bg-ok/20 text-ok"
                  : "bg-hot/20 text-hot"
            }`}
          >
            {asset.temperature == null
              ? "NO PROBE READING"
              : inBand
                ? "AIR STILL IN BAND"
                : "OUT OF BAND"}{" "}
            · {asset.temperature == null ? "—" : `${asset.temperature.toFixed(2)}°C`} in{" "}
            {asset.band_low_c}–{asset.band_high_c}°C
          </div>
        ) : (
          <div className="text-mute mt-2 text-sm">Location-only asset — no temperature probe</div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Stat label="T_eq (equilibrium)" value={fmt(asset.t_eq_c, "°C")} accent />
        <Stat label="Mode" value={asset.model_mode} />
        <Stat label="Compressor health" value={`${Math.round(asset.compressor_health * 100)}%`} />
        <Stat label="Risk" value={asset.risk_score.toFixed(0)} />
        <Stat label="Fault" value={asset.fault_class} hot={asset.fault_class !== "NONE"} />
        <Stat label="Door" value={asset.door_status} />
        {asset.remaining_efficacy_pct != null ? (
          <Stat label="η illustrative" value={`${asset.remaining_efficacy_pct.toFixed(1)}%`} />
        ) : null}
        <Stat label="Free capacity" value={`${asset.free_l.toFixed(2)} L`} />
      </div>

      {series.length > 1 ? (
        <div className="h-24">
          <ResponsiveContainer>
            <LineChart data={series}>
              <YAxis hide domain={["auto", "auto"]} />
              {asset.band_high_c != null ? (
                <ReferenceLine y={asset.band_high_c} stroke="#e23d28" strokeDasharray="3 3" />
              ) : null}
              {asset.band_low_c != null ? (
                <ReferenceLine y={asset.band_low_c} stroke="#7b8cff" strokeDasharray="3 3" />
              ) : null}
              <Line type="monotone" dataKey="v" stroke="#2ec4b6" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}

      <p className="text-mute text-xs leading-relaxed">
        Newton cooling for the cabinet, {railName} {fmt(asset.breach_threshold_c, "°C")}, τ
        compressed to {fmt(asset.tau_min, " min")} for the demo. Sensor {asset.sensor_id || "n/a"}.
        Door-open is logged as an event, never an automatic discard.
      </p>
    </div>
  );
}

function fmt(v: number | null, unit: string): string {
  return v == null ? "n/a" : `${v}${unit}`;
}

function Stat({
  label,
  value,
  accent,
  hot,
}: {
  label: string;
  value: string;
  accent?: boolean;
  hot?: boolean;
}) {
  return (
    <div className="border-line bg-ink/40 rounded-lg border px-3 py-2">
      <div className="text-mute text-xs tracking-wider uppercase">{label}</div>
      <div className={`font-mono text-sm ${hot ? "text-hot" : accent ? "text-cyan" : "text-ice"}`}>
        {value}
      </div>
    </div>
  );
}
