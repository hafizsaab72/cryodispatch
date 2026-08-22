export const PLANT_URL = process.env.EXPO_PUBLIC_PLANT_URL ?? "http://127.0.0.1:8787";

export type Mission = {
  id: string;
  from_asset: string;
  from_label?: string;
  to_asset: string;
  to_label?: string;
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

/** Every call goes through here so a non-2xx never masquerades as success. */
async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${PLANT_URL}${path}`, init);
  } catch {
    throw new Error(`Cannot reach plant at ${PLANT_URL}. Check the LAN IP.`);
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Plant returned ${res.status}. ${body.slice(0, 120)}`);
  }
  return res.json() as Promise<T>;
}

export function fetchState(): Promise<PlantState> {
  return call<PlantState>("/api/state");
}

export async function fetchMission(id: string): Promise<Mission | null> {
  const state = await fetchState();
  return state.missions.find((m) => m.id === id) ?? null;
}

export function acceptMission(id: string): Promise<Mission> {
  return call<Mission>(`/api/missions/${id}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: "nurse-rao" }),
  });
}

export function scanMission(id: string, code: string): Promise<Mission> {
  return call<Mission>(`/api/missions/${id}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, actor: "nurse-rao" }),
  });
}
