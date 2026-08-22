import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type {
  Alert,
  AssetState,
  AuditEvent,
  CustodyDocument,
  InventoryUnit,
  Mission,
  PlantState,
  StaffMember,
  Ticket,
} from "@cryodispatch/shared";

export function supabaseConfigured(): boolean {
  return Boolean(import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY);
}

let _sb: SupabaseClient | null = null;

function sb(): SupabaseClient {
  if (_sb) return _sb;
  const url = import.meta.env.VITE_SUPABASE_URL as string;
  const key = import.meta.env.VITE_SUPABASE_ANON_KEY as string;
  _sb = createClient(url, key);
  return _sb;
}

function toIst(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(d);
  const g = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
  return `${g("year")}-${g("month")}-${g("day")} ${g("hour")}:${g("minute")}:${g("second")} IST`;
}

function mapAsset(row: Record<string, unknown>): AssetState {
  return {
    ...(row as unknown as AssetState),
    dT_dt_c_per_min: (row.dt_dt_c_per_min as number | null) ?? null,
    predicted_T_60s_c: (row.predicted_t_60s_c as number | null) ?? null,
    recent_c: (row.recent_c as number[]) ?? [],
    updated_at: toIst(row.updated_at as string),
  };
}

function mapAlert(row: Record<string, unknown>): Alert {
  return {
    ...(row as unknown as Alert),
    created_at: toIst(row.created_at as string),
    acked_at: row.acked_at ? toIst(row.acked_at as string) : null,
  };
}

function mapMission(row: Record<string, unknown>): Mission {
  return {
    ...(row as unknown as Mission),
    units: (row.units as Mission["units"]) ?? [],
    events: (row.events as Mission["events"]) ?? [],
    routing: row.routing as Mission["routing"],
    created_at: toIst(row.created_at as string),
  };
}

export async function fetchCloudState(): Promise<PlantState> {
  const client = sb();
  const [
    meta,
    assets,
    alerts,
    missions,
    tickets,
    inventory,
    staff,
    audit,
  ] = await Promise.all([
    client.from("plant_meta").select("*").limit(1),
    client.from("asset_state").select("*"),
    client.from("alerts").select("*").order("created_at", { ascending: false }),
    client.from("missions").select("*").order("created_at", { ascending: false }),
    client.from("tickets").select("*").order("created_at", { ascending: false }),
    client.from("inventory").select("*"),
    client.from("staff").select("*"),
    client.from("audit_events").select("*").order("created_at", { ascending: false }).limit(40),
  ]);
  const err =
    meta.error ||
    assets.error ||
    alerts.error ||
    missions.error ||
    tickets.error ||
    inventory.error ||
    staff.error ||
    audit.error;
  if (err) throw new Error(err.message);
  const m = meta.data?.[0] as { site_id: string; hospital: string; tick: number } | undefined;
  return {
    site_id: m?.site_id ?? "elcia-emc",
    hospital: m?.hospital ?? "ELCIA Medical Centre",
    tick: m?.tick ?? 0,
    assets: (assets.data ?? []).map((r) => mapAsset(r as Record<string, unknown>)),
    alerts: (alerts.data ?? []).map((r) => mapAlert(r as Record<string, unknown>)),
    missions: (missions.data ?? []).map((r) => mapMission(r as Record<string, unknown>)),
    tickets: (tickets.data ?? []) as Ticket[],
    inventory: (inventory.data ?? []) as InventoryUnit[],
    staff: (staff.data ?? []) as StaffMember[],
    audit: (audit.data ?? []).map((r) => ({
      ...(r as AuditEvent),
      created_at: toIst((r as AuditEvent).created_at),
    })),
  };
}

export async function fetchCloudCustody(id: string): Promise<CustodyDocument> {
  const { data, error } = await sb().from("custody_documents").select("doc").eq("mission_id", id).maybeSingle();
  if (error) throw new Error(error.message);
  if (!data?.doc) throw new Error(`No custody record for ${id}`);
  return data.doc as CustodyDocument;
}

export async function postIntent(body: Record<string, unknown>): Promise<void> {
  const url = `${(import.meta.env.VITE_SUPABASE_URL as string).replace(/\/+$/, "")}/functions/v1/intent`;
  const r = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: import.meta.env.VITE_SUPABASE_ANON_KEY as string,
      Authorization: `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY as string}`,
    },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`Intent failed (${r.status})`);
}

export function subscribeCloud(onEvent: (ev: { type: string; state?: PlantState }) => void): () => void {
  const client = sb();
  let timer: ReturnType<typeof setTimeout> | null = null;
  const pull = () => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fetchCloudState()
        .then((state) => onEvent({ type: "state", state }))
        .catch(() => {
          /* bootstrap retry lives in App.tsx */
        });
    }, 80);
  };
  pull();
  const ch = client
    .channel("cryodispatch-plant")
    .on("postgres_changes", { event: "*", schema: "public", table: "asset_state" }, pull)
    .on("postgres_changes", { event: "*", schema: "public", table: "alerts" }, pull)
    .on("postgres_changes", { event: "*", schema: "public", table: "missions" }, pull)
    .on("postgres_changes", { event: "*", schema: "public", table: "tickets" }, pull)
    .on("postgres_changes", { event: "*", schema: "public", table: "plant_meta" }, pull)
    .on("postgres_changes", { event: "*", schema: "public", table: "inventory" }, pull)
    .on("postgres_changes", { event: "*", schema: "public", table: "staff" }, pull)
    .on("postgres_changes", { event: "*", schema: "public", table: "custody_documents" }, pull)
    .subscribe();
  return () => {
    if (timer) clearTimeout(timer);
    void client.removeChannel(ch);
  };
}
