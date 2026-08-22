from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.table import Table

# Allow `python -m sim` from apps/sim without installing.
_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv()

from sim.plant import Plant  # noqa: E402
from sim.server import app, plant as SERVER_PLANT  # noqa: E402


def _table(plant: Plant) -> Table:
    tbl = Table(title=f"CryoDispatch  ·  {plant.hospital}  ·  tick {plant.tick}")
    tbl.add_column("Asset")
    tbl.add_column("T°C", justify="right")
    tbl.add_column("T_eq", justify="right")
    tbl.add_column("t*", justify="right")
    tbl.add_column("Mode")
    tbl.add_column("Fault")
    for a in plant.assets.values():
        if not a.spec.thermal:
            continue
        t = "—" if a.temperature is None else f"{a.temperature:5.2f}"
        teq = "—" if a.processed.t_eq_c is None else f"{a.processed.t_eq_c:5.2f}"
        mins = a.processed.minutes_to_breach
        star = "stable" if mins >= 9000 else f"{mins:6.1f}m"
        tbl.add_row(a.spec.asset_id, t, teq, star, a.processed.model_mode, a.processed.fault_class)
    return tbl


def _loop(plant: Plant, stop: threading.Event, tick_sec: float) -> None:
    ingest_url = os.getenv("INGEST_URL")
    ingest_key = os.getenv("INGEST_KEY", "")
    mqtt_host = os.getenv("MQTT_HOST")
    client = None
    if mqtt_host:
        try:
            import paho.mqtt.client as mqtt

            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            user, pw = os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD")
            if user:
                client.username_pw_set(user, pw)
            client.connect(mqtt_host, int(os.getenv("MQTT_PORT", "1883")), 60)
            client.loop_start()
        except Exception as exc:  # noqa: BLE001
            Console().print(f"[yellow]MQTT skipped:[/yellow] {exc}")
            client = None

    httpx = None
    if ingest_url:
        import httpx as _httpx

        httpx = _httpx.Client(timeout=2.0)

    while not stop.is_set():
        plant.step()
        if httpx and ingest_url:
            for a in plant.assets.values():
                if not a.spec.thermal:
                    continue
                try:
                    httpx.post(
                        ingest_url,
                        json=plant.telemetry_of(a).model_dump(),
                        headers={"Authorization": f"Bearer {ingest_key}"} if ingest_key else {},
                    )
                except Exception:
                    pass
        if client:
            for a in plant.assets.values():
                tel = plant.telemetry_of(a)
                client.publish(tel.topic, tel.model_dump_json(), qos=0)
        stop.wait(tick_sec)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="sim", description="CryoDispatch telemetry plant")
    parser.add_argument("--anomaly", nargs=2, metavar=("ASSET", "KIND"), help="compressor | door | lwt | reset")
    parser.add_argument("--host", default=os.getenv("PLANT_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PLANT_PORT", "8787")))
    parser.add_argument("--tick", type=float, default=float(os.getenv("TICK_SEC", "1.0")))
    parser.add_argument("--tau", type=float, default=float(os.getenv("DEMO_TAU_MIN", "2.0")))
    parser.add_argument("--no-server", action="store_true")
    args = parser.parse_args(argv)

    console = Console()
    plant = SERVER_PLANT
    plant.demo_tau_min = args.tau
    plant.tick_sec = args.tick

    if args.anomaly:
        asset, kind = args.anomaly
        # If a plant is already running, hit its HTTP API so the live demo reacts.
        import httpx

        url = f"http://127.0.0.1:{args.port}/api/anomaly"
        try:
            r = httpx.post(url, json={"asset_id": asset, "kind": kind}, timeout=2.0)
            console.print(r.json())
            return
        except Exception:
            plant.anomaly(asset, kind)
            console.print(plant.assets[asset].processed.model_dump())
            if args.no_server:
                return

    stop = threading.Event()
    worker = threading.Thread(target=_loop, args=(plant, stop, args.tick), daemon=True)
    worker.start()

    if args.no_server:
        try:
            with Live(_table(plant), console=console, refresh_per_second=4) as live:
                while True:
                    live.update(_table(plant))
                    time.sleep(0.25)
        except KeyboardInterrupt:
            stop.set()
        return

    import uvicorn

    def run_uv() -> None:
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

    uv = threading.Thread(target=run_uv, daemon=True)
    uv.start()
    console.print(f"[bold cyan]CryoDispatch plant[/bold cyan]  http://{args.host}:{args.port}")
    console.print("Anomaly: python -m sim --anomaly FREEZER_BLOOD_04 compressor")
    try:
        with Live(_table(plant), console=console, refresh_per_second=4) as live:
            while True:
                live.update(_table(plant))
                time.sleep(0.25)
    except KeyboardInterrupt:
        stop.set()
        console.print("\nstopped")


if __name__ == "__main__":
    main()
