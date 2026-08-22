import type { CustodyDocument, PlantState } from "@cryodispatch/shared";
import {
  fetchCloudCustody,
  fetchCloudState,
  postIntent,
  subscribeCloud,
  supabaseConfigured,
} from "./cloud";

const PLANT_PORT = 8787;

/**
 * Dev goes through the vite proxy, so a relative base is correct there. A built
 * bundle served off the demo LAN has no proxy, so aim at the plant's own port on
 * whichever host handed us the page.
 */
function plantBase(): string {
  const configured = import.meta.env.VITE_PLANT_URL;
  if (configured) return configured.replace(/\/+$/, "");
  if (import.meta.env.DEV) return "";
  return `${location.protocol}//${location.hostname}:${PLANT_PORT}`;
}

const BASE = plantBase();
const CLOUD = supabaseConfigured();
export const usingCloud = CLOUD;

const UNREACHABLE = CLOUD
  ? "Supabase unreachable — start the plant so it can publish, or unset VITE_SUPABASE_* to use LAN."
  : `Plant unreachable at ${BASE || "the dev proxy"} — start apps/sim ` +
    `(.venv/bin/python -m sim), or set VITE_PLANT_URL to the plant's address and rebuild.`;

async function req(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${BASE}${path}`, init);
  } catch {
    throw new Error(UNREACHABLE);
  }
}

export async function fetchState(): Promise<PlantState> {
  if (CLOUD) return fetchCloudState();
  const r = await req("/api/state");
  if (!r.ok) throw new Error(`${UNREACHABLE} (plant returned ${r.status})`);
  return r.json();
}

export async function anomaly(asset_id: string, kind: string) {
  if (CLOUD) {
    await postIntent({ kind: "anomaly", asset_id, anomaly_kind: kind });
    return { ok: true, pending: true };
  }
  const r = await req("/api/anomaly", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ asset_id, kind }),
  });
  if (!r.ok) throw new Error(`Plant returned ${r.status} for ${asset_id}`);
  return r.json();
}

/** Full plant reset so the demo can be replayed for the next judge. */
export async function resetPlant() {
  if (CLOUD) {
    await postIntent({ kind: "reset" });
    return { ok: true, pending: true };
  }
  const r = await req("/api/reset", { method: "POST" });
  if (!r.ok) throw new Error(`Plant returned ${r.status}`);
  return r.json();
}

export async function fetchCustody(id: string): Promise<CustodyDocument> {
  if (CLOUD) return fetchCloudCustody(id);
  const r = await req(`/api/custody/${id}`);
  if (!r.ok) throw new Error(`No custody record for ${id} (plant returned ${r.status})`);
  return r.json();
}

export function subscribe(onEvent: (ev: { type: string; state?: PlantState }) => void) {
  if (CLOUD) return subscribeCloud(onEvent);
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
