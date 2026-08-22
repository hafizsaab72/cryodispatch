/**
 * Insert a plant intent. The Python plant drains this table each tick and runs
 * its existing methods. This function does not classify faults or pick backups.
 *
 * POST JSON: { kind: "anomaly"|"reset"|"accept"|"scan"|"ack", ...payload }
 */
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const KINDS = new Set(["anomaly", "reset", "accept", "scan", "ack"]);

function cors() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Content-Type": "application/json",
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors() });
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST only" }), { status: 405, headers: cors() });
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "invalid json" }), { status: 400, headers: cors() });
  }

  const kind = String(body.kind ?? "");
  if (!KINDS.has(kind)) {
    return new Response(JSON.stringify({ error: `kind must be one of ${[...KINDS].join(", ")}` }), {
      status: 400,
      headers: cors(),
    });
  }

  const { kind: _k, ...payload } = body;
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) {
    return new Response(JSON.stringify({ error: "missing service role" }), { status: 500, headers: cors() });
  }

  const sb = createClient(url, key);
  const { data, error } = await sb
    .from("plant_intents")
    .insert({ kind, payload, status: "pending" })
    .select("id")
    .single();

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: cors() });
  }
  return new Response(JSON.stringify({ ok: true, id: data.id, kind }), { headers: cors() });
});
