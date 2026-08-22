/**
 * Device ingest is the Python plant (`POST /ingest` on :8787).
 * This function is intentionally not a second brain — the old Deno thermal /
 * backupFor path disagreed with the plant (FB05 → WALKIN_COLD_02 instead of FB06).
 */
Deno.serve((req) => {
  const cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Content-Type": "application/json",
  };
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  return new Response(
    JSON.stringify({
      error: "gone",
      message:
        "Post telemetry to the Python plant /ingest. Supabase stores what the plant already decided.",
    }),
    { status: 410, headers: cors },
  );
});
