import type { Alert, Mission } from "@cryodispatch/shared";

export function AlertRail({
  alerts,
  missions,
  onPdf,
}: {
  alerts: Alert[];
  missions: Mission[];
  onPdf: (missionId: string) => void;
}) {
  return (
    <div className="flex h-full flex-col overflow-auto">
      <h2 className="text-mute px-3 py-2 font-mono text-xs tracking-widest uppercase">Alerts / MOVE</h2>
      <ul className="space-y-2 px-2 pb-4">
        {alerts.slice(0, 12).map((a) => {
          const m = missions.find((x) => x.alert_id === a.id);
          return (
            <li key={a.id} className="rounded-lg border border-line bg-panel p-3">
              <div className="flex items-center justify-between gap-2">
                <span
                  className={`font-mono text-[10px] ${a.kind === "PROBE_DEAD" ? "text-[#7b8cff]" : "text-hot"}`}
                >
                  {a.kind}
                </span>
                <span className="text-mute text-[10px]">{a.created_at}</span>
              </div>
              <p className="mt-1 text-sm">{a.message}</p>
              {m ? (
                <div className="mt-2 text-xs">
                  <div className="text-cyan font-medium">
                    MOVE {m.units.map((u) => u.blood_type || u.unit_id).join(", ")} → {m.to_asset}
                  </div>
                  <div className="text-mute">
                    {m.staff_name} · {m.distance_m} m · hold {m.ticket.kwh_hold_30m} kWh vs move {m.ticket.kwh_move}{" "}
                    kWh · {m.status}
                  </div>
                  <button
                    className="mt-2 rounded bg-cyan px-2 py-1 font-mono text-[10px] text-ink"
                    onClick={() => onPdf(m.id)}
                    type="button"
                  >
                    Custody PDF
                  </button>
                </div>
              ) : a.kind === "PROBE_DEAD" ? (
                <div className="text-mute mt-1 text-xs">Ticket only. Dead probe ≠ spoiled blood.</div>
              ) : null}
            </li>
          );
        })}
        {alerts.length === 0 ? <li className="text-mute px-3 text-sm">Plant quiet.</li> : null}
      </ul>
    </div>
  );
}
