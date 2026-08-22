export function ProtocolPanel({ open }: { open: boolean }) {
  if (!open) return null;
  return (
    <aside className="border-line bg-panel max-h-48 overflow-auto border-t p-3 font-mono text-[11px] text-ice">
      <div className="text-cyan mb-1">MQTT contract — devices speak this; UIs subscribe to the plant, not the broker.</div>
      <pre className="text-mute whitespace-pre-wrap">
        {`cryo/elcia-emc/assets/{id}/telemetry   QoS 0
cryo/elcia-emc/assets/{id}/status       QoS 1 retained
cryo/elcia-emc/assets/{id}/lwt          LWT offline → PROBE_DEAD
cryo/elcia-emc/cmd/{id}/reroute
cryo/elcia-emc/alerts/{alertId}

HTTP POST /ingest is the same JSON with topic in the body.`}
      </pre>
    </aside>
  );
}
