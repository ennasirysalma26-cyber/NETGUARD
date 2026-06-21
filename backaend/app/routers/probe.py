from datetime import datetime, timezone, timedelta
from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, decode_token
from app.core.websocket import manager
from app.models.models import Device, ProbeResult, Alert
from app.models.user import User
from app.schemas.schemas import (
    PingRequest, PingResult, ProbeHistoryResponse, ProbePoint,
    SnmpResult, ScanStatusResponse,
)
from app.services.probe_service import ping_host, collect_snmp_full

router = APIRouter()


def _now():
    return datetime.now(timezone.utc)


async def _get_device_or_404(device_id: str, db: AsyncSession) -> Device:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    return device


# ─── PING ────────────────────────────────────────────────────────────────────

@router.post("/ping/{device_id}", response_model=PingResult)
async def ping_device(
    device_id: str,
    data:      PingRequest    = PingRequest(),
    db:        AsyncSession   = Depends(get_db),
    _:         User           = Depends(get_current_user),
):
    device = await _get_device_or_404(device_id, db)

    result = await ping_host(
        ip=device.ip_address,
        count=data.count,
        timeout=data.timeout / 1000,
    )

    # Persister le résultat
    probe = ProbeResult(
        device_id=device.id,
        rtt_avg_ms=result.get("rtt_avg_ms"),
        rtt_min_ms=result.get("rtt_min_ms"),
        rtt_max_ms=result.get("rtt_max_ms"),
        packet_loss=result.get("packet_loss", 100.0),
        status=result["status"],
    )
    db.add(probe)

    # Mettre à jour last_seen si up
    if result["status"] == "up":
        device.last_seen = _now()

    # Détecter un changement de statut → créer une alerte
    old_status = device.status
    new_status = "Actif" if result["status"] == "up" else "Panne"
    if old_status != new_status:
        device.status = new_status
        alert = Alert(
            device_id=device.id,
            severity="critical" if new_status == "Panne" else "info",
            message=f"Changement d'état : {old_status} → {new_status}",
        )
        db.add(alert)
        # Diffuser sur le canal WebSocket alerts
        await manager.broadcast_alert({
            "event":       "status_change",
            "device_id":   device.id,
            "device_name": device.name,
            "old_status":  old_status,
            "new_status":  new_status,
            "changed_at":  _now().isoformat(),
        })

    # Diffuser le résultat de sonde
    await manager.send_probe_result(device.id, {
        "event":       "probe_result",
        "device_id":   device.id,
        "device_name": device.name,
        "status":      result["status"],
        "rtt_ms":      result.get("rtt_avg_ms"),
        "loss_percent":result.get("packet_loss"),
        "probed_at":   _now().isoformat(),
    })

    await db.flush()
    return PingResult(
        device_id=device.id,
        ip=device.ip_address,
        probed_at=_now(),
        **result,
    )


# ─── HISTORIQUE SONDE ────────────────────────────────────────────────────────

@router.get("/history/{device_id}", response_model=ProbeHistoryResponse)
async def probe_history(
    device_id:  str,
    from_:      Optional[datetime] = Query(None, alias="from"),
    to_:        Optional[datetime] = Query(None, alias="to"),
    resolution: str                = Query("5m", pattern="^(raw|1m|5m|1h|1d)$"),
    db:         AsyncSession       = Depends(get_db),
    _:          User               = Depends(get_current_user),
):
    await _get_device_or_404(device_id, db)

    if from_ is None:
        from_ = _now() - timedelta(hours=3)
    if to_ is None:
        to_ = _now()

    query = (
        select(ProbeResult)
        .where(ProbeResult.device_id == device_id)
        .where(ProbeResult.recorded_at >= from_)
        .where(ProbeResult.recorded_at <= to_)
        .order_by(ProbeResult.recorded_at.asc())
    )
    results = (await db.execute(query)).scalars().all()

    if resolution == "raw":
        points = [
            ProbePoint(ts=r.recorded_at, rtt_avg=r.rtt_avg_ms, loss=r.packet_loss)
            for r in results
        ]
    else:
        # Aggrégation simple par bucket de temps
        buckets = _aggregate_results(results, resolution)
        points = [
            ProbePoint(ts=ts, rtt_avg=data["rtt_avg"], loss=data["loss"])
            for ts, data in buckets.items()
        ]

    return ProbeHistoryResponse(device_id=device_id, resolution=resolution, points=points)


def _aggregate_results(results, resolution: str) -> dict:
    intervals = {"1m": 60, "5m": 300, "1h": 3600, "1d": 86400}
    bucket_secs = intervals.get(resolution, 300)
    buckets = {}
    for r in results:
        ts = r.recorded_at
        bucket_ts = datetime(
            ts.year, ts.month, ts.day,
            ts.hour, (ts.minute // (bucket_secs // 60)) * (bucket_secs // 60),
            tzinfo=ts.tzinfo,
        )
        buckets.setdefault(bucket_ts, {"rtts": [], "losses": []})
        if r.rtt_avg_ms is not None:
            buckets[bucket_ts]["rtts"].append(r.rtt_avg_ms)
        buckets[bucket_ts]["losses"].append(r.packet_loss)

    return {
        ts: {
            "rtt_avg": round(sum(d["rtts"]) / len(d["rtts"]), 2) if d["rtts"] else None,
            "loss":    round(sum(d["losses"]) / len(d["losses"]), 1),
        }
        for ts, d in sorted(buckets.items())
    }


# ─── SNMP ────────────────────────────────────────────────────────────────────

@router.post("/snmp/{device_id}", response_model=SnmpResult)
async def snmp_device(
    device_id: str,
    db:        AsyncSession = Depends(get_db),
    _:         User         = Depends(get_current_user),
):
    device = await _get_device_or_404(device_id, db)

    if not device.snmp_enabled:
        raise HTTPException(status_code=400, detail="SNMP non activé sur cet équipement")

    community = device.snmp_community or "public"
    data = await collect_snmp_full(device.ip_address, community)

    return SnmpResult(
        device_id=device.id,
        probed_at=_now(),
        system=data["system"],
        resources=data["resources"],
        interfaces=data["interfaces"],
    )


# ─── SCAN STATUS ─────────────────────────────────────────────────────────────

@router.get("/scan/status", response_model=ScanStatusResponse)
async def scan_status(
    db: AsyncSession = Depends(get_db),
    _:  User         = Depends(get_current_user),
):
    result = await db.execute(select(Device))
    devices = result.scalars().all()

    up   = sum(1 for d in devices if d.status == "Actif")
    down = sum(1 for d in devices if d.status == "Panne")
    maint= sum(1 for d in devices if d.status == "Maintenance")

    return ScanStatusResponse(
        scanned_at=_now(),
        summary={"total": len(devices), "up": up, "down": down, "maintenance": maint},
        devices=[
            {"id": d.id, "name": d.name, "status": d.status,
             "rtt": None, "last_seen": d.last_seen}
            for d in devices
        ],
    )


# ─── WEBSOCKET : SONDES ──────────────────────────────────────────────────────

@router.websocket("/ws/probe")
async def ws_probe(websocket: WebSocket, token: Optional[str] = None):
    if not token:
        await websocket.close(code=4001)
        return
    try:
        decode_token(token)
    except Exception:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket, "probe")
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")
            ids    = msg.get("device_ids", [])
            if action == "subscribe":
                manager.subscribe(websocket, ids)
                await websocket.send_text(json.dumps({
                    "event": "subscribed", "device_ids": ids
                }))
            elif action == "unsubscribe":
                manager.unsubscribe(websocket, ids)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "probe")


# ─── WEBSOCKET : ALERTES ─────────────────────────────────────────────────────

@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket, token: Optional[str] = None):
    if not token:
        await websocket.close(code=4001)
        return
    try:
        decode_token(token)
    except Exception:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket, "alerts")
    try:
        while True:
            # Canal passif : on reste connecté sans envoyer de messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "alerts")
