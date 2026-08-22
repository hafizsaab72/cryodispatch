import type { AssetState } from "@cryodispatch/shared";
import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";

export function Gauge({ asset }: { asset: AssetState | undefined }) {
  if (!asset) {
    return <div className="text-mute p-6 text-sm">Select a vault on the floor map.</div>;
  }
  const mins = asset.minutes_to_breach;
  const star = mins >= 9000 ? "stable" : `${mins.toFixed(1)} min`;
  const spark = [
    { t: 0, v: asset.temperature ?? 0 },
    { t: 1, v: asset.predicted_T_60s_c ?? asset.temperature ?? 0 },
  ];
  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div>
        <div className="text-mute font-mono text-xs tracking-widest uppercase">{asset.asset_id}</div>
        <div className="text-xl font-semibold">{asset.label}</div>
        <div className="text-mute text-sm">{asset.location}</div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Stat label="Air" value={asset.temperature == null ? "—" : `${asset.temperature.toFixed(2)}°C`} />
        <Stat label="T_eq" value={asset.t_eq_c == null ? "—" : `${asset.t_eq_c.toFixed(2)}°C`} accent />
        <Stat label="Time-to-breach" value={star} hot={mins < 25} />
        <Stat label="Mode" value={asset.model_mode} />
        <Stat label="Compressor" value={`${Math.round(asset.compressor_health * 100)}%`} />
        <Stat label="Risk" value={asset.risk_score.toFixed(0)} />
        {asset.remaining_efficacy_pct != null ? (
          <Stat label="η (illustrative)" value={`${asset.remaining_efficacy_pct.toFixed(1)}%`} />
        ) : null}
        <Stat label="Fault" value={asset.fault_class} />
      </div>
      {asset.temperature != null ? (
        <div className="h-16">
          <ResponsiveContainer>
            <LineChart data={spark}>
              <YAxis hide domain={["auto", "auto"]} />
              <Line type="monotone" dataKey="v" stroke="#2ec4b6" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
      <p className="text-mute text-xs">
        Newton cooling for the box. Threshold {asset.breach_threshold_c}°C. τ demo-compressed to {asset.tau_min} min.
        Door-open is an event, not an auto-discard.
      </p>
    </div>
  );
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
    <div className="rounded-lg border border-line bg-ink/40 px-3 py-2">
      <div className="text-mute text-[10px] tracking-wider uppercase">{label}</div>
      <div className={`font-mono text-sm ${hot ? "text-hot" : accent ? "text-cyan" : "text-ice"}`}>{value}</div>
    </div>
  );
}
