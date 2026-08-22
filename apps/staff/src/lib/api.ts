const BASE = process.env.EXPO_PUBLIC_PLANT_URL ?? "http://127.0.0.1:8787";

export type Mission = {
  id: string;
  from_asset: string;
  to_asset: string;
  status: string;
  staff_name: string | null;
  distance_m: number;
  eta_min: number;
  scan_step: string;
  last_reject: string | null;
  units: { unit_id: string; blood_type: string | null; product_name: string }[];
  ticket: { kwh_hold_30m: number; kwh_move: number; parts: string };
};

export type PlantState = {
  missions: Mission[];
  alerts: { id: string; kind: string; message: string; created_at: string }[];
};

export async function fetchState(): Promise<PlantState> {
  const r = await fetch(`${BASE}/api/state`);
  if (!r.ok) throw new Error("Plant offline");
  return r.json();
}

export async function acceptMission(id: string) {
  const r = await fetch(`${BASE}/api/missions/${id}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: "nurse-rao" }),
  });
  return r.json() as Promise<Mission>;
}

export async function scanMission(id: string, code: string) {
  const r = await fetch(`${BASE}/api/missions/${id}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, actor: "nurse-rao" }),
  });
  return r.json() as Promise<Mission>;
}
