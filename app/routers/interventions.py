import math
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Intervention, Device
from app.models.user import User
from app.schemas.schemas import (
    InterventionCreate, InterventionOut, InterventionListResponse,
)

router = APIRouter()


@router.get("", response_model=InterventionListResponse)
async def list_interventions(
    device_id: Optional[str] = None,
    type:      Optional[str] = None,
    from_:     Optional[date] = Query(None, alias="from"),
    to_:       Optional[date] = Query(None, alias="to"),
    page:      int            = Query(1,  ge=1),
    limit:     int            = Query(20, ge=1, le=100),
    db:        AsyncSession   = Depends(get_db),
    _:         User           = Depends(get_current_user),
):
    query = select(Intervention).order_by(Intervention.created_at.desc())

    if device_id:
        query = query.where(Intervention.device_id == device_id)
    if type:
        query = query.where(Intervention.type == type)
    if from_:
        query = query.where(func.date(Intervention.created_at) >= from_)
    if to_:
        query = query.where(func.date(Intervention.created_at) <= to_)

    total = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar()

    query = query.offset((page - 1) * limit).limit(limit)
    items = (await db.execute(query)).scalars().all()

    # Enrichir avec le nom du device et l'auteur
    data = []
    for item in items:
        dev_result = await db.execute(select(Device).where(Device.id == item.device_id))
        device = dev_result.scalar_one_or_none()
        out = InterventionOut.model_validate(item)
        out.device_name = device.name if device else None
        out.author      = item.author_user.username if item.author_user else None
        data.append(out)

    return InterventionListResponse(
        data=data,
        pagination={
            "page": page, "limit": limit,
            "total": total, "pages": math.ceil(total / limit),
        },
    )


@router.post("", response_model=InterventionOut, status_code=201)
async def create_intervention(
    data:    InterventionCreate,
    db:      AsyncSession = Depends(get_db),
    current: User         = Depends(get_current_user),
):
    device_result = await db.execute(select(Device).where(Device.id == data.device_id))
    if not device_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Équipement introuvable")

    intervention = Intervention(
        device_id=data.device_id,
        author_id=current.id,
        type=data.type,
        description=data.description,
    )
    db.add(intervention)
    await db.flush()
    await db.refresh(intervention)
    return intervention


@router.get("/{intervention_id}", response_model=InterventionOut)
async def get_intervention(
    intervention_id: str,
    db:              AsyncSession = Depends(get_db),
    _:               User         = Depends(get_current_user),
):
    result = await db.execute(
        select(Intervention).where(Intervention.id == intervention_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    return item
