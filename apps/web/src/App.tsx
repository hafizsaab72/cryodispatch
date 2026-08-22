import { Lightning, Radio, ThermometerCold, Warning } from "@phosphor-icons/react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { PlantState } from "@cryodispatch/shared";
import { AlertRail } from "./AlertRail";
import { anomaly, fetchCustody, fetchState, subscribe } from "./api";
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
    fetchState()
      .then(setState)
      .catch((e: Error) => setErr(e.message));
    return subscribe((ev) => {
      if (ev.state) setState(ev.state);
    });
  }, []);

  const asset = useMemo(
    () => state?.assets.find((a) => a.asset_id === selected),
    [state, selected],
  );

  async function onPdf(id: string) {
    const c = await fetchCustody(id);
    downloadCustodyPdf(c);
  }

  if (err) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <p className="text-hot max-w-md text-sm">
          {err}. In <code className="font-mono">apps/sim</code> run <code className="font-mono">python -m sim</code>.
        </p>
      </div>
    );
  }
  if (!state) {
    return <div className="text-mute flex h-full items-center justify-center">Connecting to plant…</div>;
  }

  return (
    <div className="flex h-full flex-col">
      <header className="border-line flex items-center justify-between border-b px-4 py-3">
        <div>
          <div className="text-cyan font-mono text-xs tracking-[0.3em] uppercase">ELCIA Medical Centre</div>
          <h1 className="text-lg font-semibold">CryoDispatch · Command Center</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <DemoBtn icon={<Radio size={14} />} label="Kill probe" onClick={() => anomaly("ILR_VAX_02", "lwt")} />
          <DemoBtn
            icon={<ThermometerCold size={14} />}
            label="Compressor V3"
            onClick={() => anomaly("FREEZER_BLOOD_04", "compressor")}
          />
          <DemoBtn
            icon={<Warning size={14} />}
            label="Second vault"
            onClick={() => anomaly("FREEZER_BLOOD_05", "compressor")}
          />
          <DemoBtn icon={<Lightning size={14} />} label="Reset V3" onClick={() => anomaly("FREEZER_BLOOD_04", "reset")} />
          <button
            type="button"
            className="text-mute rounded border border-line px-2 py-1 font-mono text-[10px]"
            onClick={() => setProtocol((p) => !p)}
          >
            Protocol
          </button>
        </div>
      </header>
      <div className="grid min-h-0 flex-1 grid-cols-[1.4fr_0.9fr_0.85fr]">
        <section className="border-line min-h-0 border-r p-3">
          <FloorMap assets={state.assets} selected={selected} onSelect={setSelected} />
        </section>
        <section className="border-line min-h-0 overflow-auto border-r">
          <Gauge asset={asset} />
        </section>
        <section className="min-h-0">
          <AlertRail alerts={state.alerts} missions={state.missions} onPdf={onPdf} />
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
      className="flex items-center gap-1 rounded-md border border-line bg-panel px-2 py-1 font-mono text-[11px] text-ice hover:border-cyan"
    >
      {icon}
      {label}
    </button>
  );
}
