import type { AssetState } from "@cryodispatch/shared";

const MODE_COLOR: Record<string, string> = {
  stable: "#3ddc97",
  warming: "#e07a3d",
  breached: "#e23d28",
  probe_dead: "#7b8cff",
  location: "#2ec4b6",
};

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
    <svg viewBox="0 0 100 100" className="h-full w-full rounded-xl bg-[#071c26]">
      <rect x="2" y="2" width="96" height="30" rx="2" fill="#0b2430" stroke="#1c4654" />
      <text x="4" y="8" fill="#7fa3ad" fontSize="3">
        Floor 1 · Blood / ER
      </text>
      <rect x="2" y="34" width="96" height="32" rx="2" fill="#0b2430" stroke="#1c4654" />
      <text x="4" y="40" fill="#7fa3ad" fontSize="3">
        Floor 2 · ICU / Pharmacy
      </text>
      <rect x="2" y="68" width="96" height="30" rx="2" fill="#0b2430" stroke="#1c4654" />
      <text x="4" y="74" fill="#7fa3ad" fontSize="3">
        Floor 3 · OT / overflow
      </text>
      {assets.map((a) => {
        const c = MODE_COLOR[a.model_mode] ?? "#2ec4b6";
        const r = a.asset_id === selected ? 3.2 : 2.2;
        return (
          <g key={a.asset_id} onClick={() => onSelect(a.asset_id)} style={{ cursor: "pointer" }}>
            <circle cx={a.map_x} cy={a.map_y} r={r} fill={c} opacity={0.95} />
            {a.asset_id === selected ? (
              <circle cx={a.map_x} cy={a.map_y} r={r + 1.6} fill="none" stroke={c} strokeWidth="0.4" />
            ) : null}
            <title>
              {a.label} {a.temperature ?? "—"}°C {a.model_mode}
            </title>
          </g>
        );
      })}
    </svg>
  );
}
