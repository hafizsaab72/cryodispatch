import type { Alert, AssetState, Mission } from "@cryodispatch/shared";

const KIND_COLOR: Record<string, string> = {
  PROBE_DEAD: "text-[#7b8cff]",
  BOTH: "text-hot",
  THERMAL_PREDICT: "text-warn",
  THERMAL_EXCURSION: "text-hot",
};

function clockOnly(stamp: string): string {
  // Plant sends "YYYY-MM-DD HH:MM:SS IST".
  const parts = stamp.split(" ");
  return parts.length >= 2 ? `${parts[1]} IST` : stamp;
}

/** Only assets with a labelled band can be "in band"; carts have no probe. */
function bandTally(assets: AssetState[]): { inBand: number; monitored: number } {
  const monitored = assets.filter((a) => a.band_low_c != null && a.band_high_c != null);
  const inBand = monitored.filter(
    (a) =>
      a.temperature != null && a.temperature >= a.band_low_c! && a.temperature <= a.band_high_c!,
  );
  return { inBand: inBand.length, monitored: monitored.length };
}

export function AlertRail({
  alerts,
  assets,
  missions,
  onPdf,
}: {
  alerts: Alert[];
  assets: AssetState[];
  missions: Mission[];
  onPdf: (missionId: string) => void;
}) {
  const { inBand, monitored } = bandTally(assets);
  return (
    <div className="flex h-full flex-col overflow-auto">
      <h2 className="text-mute px-3 py-2 font-mono text-xs tracking-widest uppercase">
        Alerts / dispatch
      </h2>
      <ul className="space-y-2 px-2 pb-4">
        {alerts.slice(0, 12).map((a) => {
          const m = missions.find((x) => x.alert_id === a.id);
          return (
            <li key={a.id} className="border-line bg-panel rounded-lg border p-3">
              <div className="flex items-center justify-between gap-2">
                <span className={`font-mono text-xs ${KIND_COLOR[a.kind] ?? "text-hot"}`}>
                  {a.kind}
                </span>
                <span className="text-mute font-mono text-xs">{clockOnly(a.created_at)}</span>
              </div>
              <p className="mt-1.5 text-sm leading-snug">{a.message}</p>
              {m ? (
                <div className="mt-2.5 space-y-1 text-sm">
                  <div className="text-cyan font-medium">
                    MOVE {m.units.map((u) => u.blood_type || u.unit_id).join(", ")} → {m.to_asset}
                  </div>
                  <div className="text-mute text-xs">
                    {m.staff_name ?? "no certified courier free"} · {m.distance_m} m · hold{" "}
                    {m.ticket.kwh_hold_30m} kWh vs move {m.ticket.kwh_move} kWh
                  </div>
                  <div className="text-mute text-xs">
                    status {m.status} · scan step {m.scan_step}
                  </div>
                  {m.routing ? (
                    <div className="text-mute text-xs italic">{m.routing.note}</div>
                  ) : null}
                  <button
                    className="bg-cyan text-ink mt-1.5 rounded px-2 py-1 font-mono text-xs"
                    onClick={() => onPdf(m.id)}
                    type="button"
                  >
                    Custody PDF
                  </button>
                </div>
              ) : a.kind === "PROBE_DEAD" ? (
                <div className="text-mute mt-1.5 text-xs">
                  Maintenance ticket raised. Stock stays put — a dead probe is not a hot vault.
                </div>
              ) : null}
            </li>
          );
        })}
        {alerts.length === 0 ? (
          <li className="text-mute px-3 text-sm">
            Plant quiet. {inBand} of {monitored} monitored assets in band.
          </li>
        ) : null}
      </ul>
    </div>
  );
}
