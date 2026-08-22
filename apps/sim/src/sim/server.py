from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from sim.plant import Plant

plant = Plant()
app = FastAPI(title="CryoDispatch Plant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_queues: list[asyncio.Queue] = []


def _fanout(event: dict[str, Any]) -> None:
    raw = json.dumps(event, default=str)
    for q in list(_queues):
        try:
            q.put_nowait(raw)
        except asyncio.QueueFull:
            pass


plant.subscribe(_fanout)


class AnomalyIn(BaseModel):
    asset_id: str
    kind: str


class ScanIn(BaseModel):
    code: str
    actor: str = "nurse-rao"


class AcceptIn(BaseModel):
    actor: str = "nurse-rao"


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "cryodispatch", "site": plant.site_id}


@app.get("/api/state")
def state() -> dict[str, Any]:
    return plant.snapshot()


@app.get("/api/protocol")
def protocol() -> dict[str, Any]:
    return plant.protocol()


@app.get("/api/custody/{mission_id}")
def custody(mission_id: str) -> dict[str, Any]:
    try:
        return plant.custody(mission_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/ingest")
@app.post("/api/ingest")
def ingest(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return plant.ingest(payload)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/anomaly")
def anomaly(body: AnomalyIn) -> dict[str, Any]:
    try:
        return plant.anomaly(body.asset_id, body.kind)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/missions/{mission_id}/accept")
def accept(mission_id: str, body: AcceptIn | None = None) -> dict[str, Any]:
    actor = body.actor if body else "nurse-rao"
    try:
        return plant.accept_mission(mission_id, actor)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/missions/{mission_id}/scan")
def scan(mission_id: str, body: ScanIn) -> dict[str, Any]:
    try:
        return plant.scan_mission(mission_id, body.code, body.actor)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/alerts/{alert_id}/ack")
def ack(alert_id: str) -> dict[str, Any]:
    try:
        return plant.ack_alert(alert_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/events")
async def events() -> StreamingResponse:
    q: asyncio.Queue = asyncio.Queue(maxsize=32)
    _queues.append(q)

    async def gen():
        try:
            yield f"data: {json.dumps({'type': 'hello', 'state': plant.snapshot()}, default=str)}\n\n"
            while True:
                raw = await q.get()
                yield f"data: {raw}\n\n"
        finally:
            if q in _queues:
                _queues.remove(q)

    return StreamingResponse(gen(), media_type="text/event-stream")
