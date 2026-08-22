import type { PlantState, Mission } from "@cryodispatch/shared";

const BASE = import.meta.env.VITE_PLANT_URL ?? "";

export async function fetchState(): Promise<PlantState> {
  const r = await fetch(`${BASE}/api/state`);
  if (!r.ok) throw new Error("plant unreachable — start python -m sim");
  return r.json();
}

export async function anomaly(asset_id: string, kind: string) {
  const r = await fetch(`${BASE}/api/anomaly`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ asset_id, kind }),
  });
  return r.json();
}

export async function acceptMission(id: string) {
  const r = await fetch(`${BASE}/api/missions/${id}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: "command-center" }),
  });
  return r.json() as Promise<Mission>;
}

export async function fetchCustody(id: string) {
  const r = await fetch(`${BASE}/api/custody/${id}`);
  if (!r.ok) throw new Error("no custody record");
  return r.json();
}

export function subscribe(onEvent: (ev: { type: string; state?: PlantState }) => void) {
  const src = new EventSource(`${BASE}/api/events`);
  src.onmessage = (m) => {
    try {
      onEvent(JSON.parse(m.data));
    } catch {
      /* ignore */
    }
  };
  return () => src.close();
}
