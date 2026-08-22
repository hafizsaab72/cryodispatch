import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export const PLANT_URL = process.env.EXPO_PUBLIC_PLANT_URL ?? "http://127.0.0.1:8787";
const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? "";
export const USING_CLOUD = Boolean(SUPABASE_URL && SUPABASE_ANON);

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

let _sb: SupabaseClient | null = null;
function sb(): SupabaseClient {
  if (!_sb) _sb = createClient(SUPABASE_URL, SUPABASE_ANON);
  return _sb;
}

function mapMission(row: Record<string, unknown>): Mission {
  const ticket = (row.ticket as Mission["ticket"]) ?? { kwh_hold_30m: 0, kwh_move: 0, parts: "" };
  return {
    id: String(row.id),
    from_asset: String(row.from_asset),
    from_label: row.from_label as string | undefined,
    to_asset: String(row.to_asset),
    to_label: row.to_label as string | undefined,
    status: String(row.status),
    staff_name: (row.staff_name as string | null) ?? null,
    distance_m: Number(row.distance_m ?? 0),
    eta_min: Number(row.eta_min ?? 0),
    scan_step: String(row.scan_step ?? "unit"),
    last_reject: (row.last_reject as string | null) ?? null,
    units: (row.units as Mission["units"]) ?? [],
    ticket,
  };
}

async function postIntent(body: Record<string, unknown>): Promise<void> {
  const r = await fetch(`${SUPABASE_URL.replace(/\/+$/, "")}/functions/v1/intent`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: SUPABASE_ANON,
      Authorization: `Bearer ${SUPABASE_ANON}`,
    },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`Intent failed (${r.status})`);
}

async function sleep(ms: number) {
  await new Promise((r) => setTimeout(r, ms));
}

async function waitForMission(id: string, pred: (m: Mission) => boolean, timeout = 4000): Promise<Mission> {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const m = await fetchMission(id);
    if (m && pred(m)) return m;
    await sleep(200);
  }
  throw new Error("Plant has not processed the intent yet — is python -m sim running?");
}

/** Every LAN call goes through here so a non-2xx never masquerades as success. */
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

export async function fetchState(): Promise<PlantState> {
  if (USING_CLOUD) {
    const { data, error } = await sb().from("missions").select("*").order("created_at", { ascending: false });
    if (error) throw new Error(error.message);
    return { missions: (data ?? []).map((r) => mapMission(r as Record<string, unknown>)), alerts: [] };
  }
  return call<PlantState>("/api/state");
}

export async function fetchMission(id: string): Promise<Mission | null> {
  if (USING_CLOUD) {
    const { data, error } = await sb().from("missions").select("*").eq("id", id).maybeSingle();
    if (error) throw new Error(error.message);
    return data ? mapMission(data as Record<string, unknown>) : null;
  }
  const state = await fetchState();
  return state.missions.find((m) => m.id === id) ?? null;
}

export async function acceptMission(id: string): Promise<Mission> {
  if (USING_CLOUD) {
    await postIntent({ kind: "accept", mission_id: id, actor: "nurse-rao" });
    return waitForMission(id, (m) => m.status !== "proposed");
  }
  return call<Mission>(`/api/missions/${id}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: "nurse-rao" }),
  });
}

export async function scanMission(id: string, code: string): Promise<Mission> {
  if (USING_CLOUD) {
    const before = await fetchMission(id);
    await postIntent({ kind: "scan", mission_id: id, code, actor: "nurse-rao" });
    return waitForMission(
      id,
      (m) =>
        m.scan_step !== before?.scan_step ||
        m.status !== before?.status ||
        m.last_reject !== before?.last_reject,
    );
  }
  return call<Mission>(`/api/missions/${id}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, actor: "nurse-rao" }),
  });
}
