import { ArrowCounterClockwise, Lightning, Radio, ThermometerCold, Warning } from "@phosphor-icons/react";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import type { PlantState } from "@cryodispatch/shared";
import { AlertRail } from "./AlertRail";
import { anomaly, fetchCustody, fetchState, resetPlant, subscribe } from "./api";
import { FloorMap } from "./FloorMap";
import { Gauge } from "./Gauge";
import { downloadCustodyPdf } from "./pdf";
import { ProtocolPanel } from "./ProtocolPanel";

export default function App() {
  const [state, setState] = useState<PlantState | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>("FREEZER_BLOOD_04");
  const [protocol, setProtocol] = useState(true);

  useEffect(() => {
    let alive = true;
    let live = false;
    let retry: ReturnType<typeof setInterval> | null = null;

    const stopRetry = () => {
      if (retry !== null) clearInterval(retry);
      retry = null;
    };

    const pull = () =>
      fetchState()
        .then((s) => {
          if (!alive) return;
          // One good frame is all the poll owed us; SSE drives every tick after this.
          stopRetry();
          if (live) return;
          setState(s);
          setErr(null);
        })
        // A retry that fails before anything has loaded is worth a banner; a late
        // failure once we are streaming is not.
        .catch((e: Error) => {
          if (alive && retry !== null) setErr(e.message);
        });

    // Keep retrying so opening the browser before the plant is not fatal.
    retry = setInterval(pull, 3000);
    pull();

    const stop = subscribe((ev) => {
      if (!alive || !ev.state) return;
      live = true;
      stopRetry();
      setState(ev.state);
      setErr(null);
    });
    return () => {
      alive = false;
      stopRetry();
      stop();
    };
  }, []);

  const asset = useMemo(() => state?.assets.find((a) => a.asset_id === selected), [state, selected]);

  const run = useCallback(async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      setErr(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "action failed");
    }
  }, []);

  const onPdf = useCallback(
    (id: string) => run(async () => downloadCustodyPdf(await fetchCustody(id))),
    [run],
  );

  if (!state) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-8">
        <p className="text-mute text-sm">Connecting to plant…</p>
        {err ? (
          <p className="text-hot max-w-md text-center text-sm">
            {err}. In <code className="font-mono">apps/sim</code> run{" "}
            <code className="font-mono">.venv/bin/python -m sim</code>.
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <header className="border-line flex items-center justify-between gap-4 border-b px-4 py-3">
        <div>
          <div className="text-cyan font-mono text-xs tracking-[0.3em] uppercase">
            {state.hospital}
          </div>
          <h1 className="text-lg font-semibold">CryoDispatch · Command Center</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <DemoBtn
            icon={<Radio size={16} />}
            label="Kill probe"
            onClick={() => run(() => anomaly("ILR_VAX_02", "lwt"))}
          />
          <DemoBtn
            icon={<ThermometerCold size={16} />}
            label="Compressor fail"
            onClick={() => run(() => anomaly("FREEZER_BLOOD_04", "compressor"))}
          />
          <DemoBtn
            icon={<Warning size={16} />}
            label="Second vault"
            onClick={() => run(() => anomaly("FREEZER_BLOOD_05", "compressor"))}
          />
          <DemoBtn
            icon={<ArrowCounterClockwise size={16} />}
            label="Reset plant"
            onClick={() => run(resetPlant)}
          />
          <button
            type="button"
            className="text-mute border-line rounded border px-2 py-1 font-mono text-xs"
            onClick={() => setProtocol((p) => !p)}
          >
            <Lightning size={14} className="inline" /> Protocol
          </button>
        </div>
      </header>
      {err ? (
        <div className="bg-hot/20 text-hot border-hot/40 border-b px-4 py-2 text-sm">{err}</div>
      ) : null}
      <div className="grid min-h-0 flex-1 grid-cols-[1.4fr_0.9fr_0.85fr]">
        <section className="border-line min-h-0 border-r p-3">
          <FloorMap assets={state.assets} selected={selected} onSelect={setSelected} />
        </section>
        <section className="border-line min-h-0 overflow-auto border-r">
          <Gauge asset={asset} />
        </section>
        <section className="min-h-0">
          <AlertRail
            alerts={state.alerts}
            assets={state.assets}
            missions={state.missions}
            onPdf={onPdf}
          />
        </section>
      </div>
      <ProtocolPanel open={protocol} />
    </div>
  );
}

function DemoBtn({
  label,
  onClick,
  icon,
}: {
  label: string;
  onClick: () => void;
  icon: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="border-line bg-panel text-ice hover:border-cyan flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 font-mono text-xs"
    >
      {icon}
      {label}
    </button>
  );
}
