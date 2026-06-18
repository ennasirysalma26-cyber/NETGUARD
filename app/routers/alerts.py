from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Alert, Device
from app.models.user import User
from app.schemas.schemas import AlertOut, AcknowledgeRequest

router = APIRouter()


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    severity: Optional[str] = Query(None, pattern="^(critical|warning|info)$"),
    acknowledged: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _:  User         = Depends(get_current_user),
):
    query = select(Alert).order_by(Alert.triggered_at.desc())
    if severity:
        query = query.where(Alert.severity == severity)
    if acknowledged is not None:
        query = query.where(Alert.acknowledged == acknowledged)

    items = (await db.execute(query)).scalars().all()

    results = []
    for alert in items:
        dev = (await db.execute(select(Device).where(Device.id == alert.device_id))).scalar_one_or_none()
        out = AlertOut.model_validate(alert)
        out.device_name = dev.name if dev else None
        results.append(out)
    return results


@router.put("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: str,
    data:     AcknowledgeRequest,
    db:       AsyncSession = Depends(get_db),
    current:  User         = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert  = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    alert.acknowledged    = True
    alert.acknowledged_by = current.username
    alert.acknowledged_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    db:       AsyncSession = Depends(get_db),
    _:        User         = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert  = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    await db.delete(alert)
    return {"message": "Alerte supprimée"}
