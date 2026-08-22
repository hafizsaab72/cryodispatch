import type { AssetState } from "@cryodispatch/shared";

const MODE_COLOR: Record<string, string> = {
  stable: "#3ddc97",
  warming: "#e07a3d",
  breached: "#e23d28",
  probe_dead: "#7b8cff",
  location: "#2ec4b6",
};

const MODE_LABEL: [string, string][] = [
  ["stable", "In band"],
  ["warming", "Predicted breach"],
  ["breached", "Out of band"],
  ["probe_dead", "Probe dead"],
];

// Bands must bracket the map_y clusters in apps/sim/src/sim/hospital.py.
const FLOORS: { y: number; h: number; label: string }[] = [
  { y: 20, h: 32, label: "Floor 1 · Blood bank / ER / central cold" },
  { y: 54, h: 22, label: "Floor 2 · ICU / pharmacy" },
  { y: 78, h: 20, label: "Floor 3 · OT / overflow" },
];

function shortName(id: string): string {
  const [kind, , n] = id.split("_");
  const tag = kind === "FREEZER" ? "RBC" : kind === "ILR" ? "ILR" : kind === "CART" ? "CART" : kind;
  return `${tag}${n ?? ""}`;
}

export function FloorMap({
  assets,
  selected,
  onSelect,
}: {
  assets: AssetState[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex h-full flex-col gap-2">
      <svg viewBox="0 0 100 100" className="min-h-0 flex-1 rounded-xl bg-[#071c26]">
        {FLOORS.map((f) => (
          <g key={f.label}>
            <rect x="2" y={f.y} width="96" height={f.h} rx="2" fill="#0b2430" stroke="#1c4654" strokeWidth="0.3" />
            <text x="3.5" y={f.y + 3.4} fill="#7fa3ad" fontSize="2.2">
              {f.label}
            </text>
          </g>
        ))}
        {assets.map((a) => {
          const color = MODE_COLOR[a.model_mode] ?? "#2ec4b6";
          const active = a.model_mode === "warming" || a.model_mode === "breached";
          const isSelected = a.asset_id === selected;
          return (
            <g key={a.asset_id} onClick={() => onSelect(a.asset_id)} style={{ cursor: "pointer" }}>
              {active ? (
                <circle cx={a.map_x} cy={a.map_y} r="2.4" fill="none" stroke={color} strokeWidth="0.35">
                  <animate attributeName="r" values="2.4;5;2.4" dur="1.6s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0.9" dur="1.6s" repeatCount="indefinite" />
                </circle>
              ) : null}
              <circle cx={a.map_x} cy={a.map_y} r={isSelected ? 2.4 : 1.8} fill={color} />
              {isSelected ? (
                <circle cx={a.map_x} cy={a.map_y} r="3.8" fill="none" stroke={color} strokeWidth="0.35" />
              ) : null}
              <text x={a.map_x} y={a.map_y - 3.2} fill="#d7f3f2" fontSize="2" textAnchor="middle">
                {shortName(a.asset_id)}
              </text>
              {a.temperature != null ? (
                <text x={a.map_x} y={a.map_y + 5} fill={color} fontSize="2.1" textAnchor="middle">
                  {a.temperature.toFixed(1)}°
                </text>
              ) : null}
              <title>
                {a.label} · {a.temperature ?? "no probe"} · {a.model_mode}
              </title>
            </g>
          );
        })}
      </svg>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 px-1 text-xs">
        {MODE_LABEL.map(([mode, label]) => (
          <li key={mode} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ background: MODE_COLOR[mode] }}
            />
            <span className="text-mute">{label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
