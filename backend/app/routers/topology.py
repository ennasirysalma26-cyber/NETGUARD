from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Device, TopologyLink
from app.models.user import User
from app.schemas.schemas import (
    TopologyResponse, TopologyNode, TopologyEdge,
    NodePositionUpdate, LinkCreate,
)

router = APIRouter()


@router.get("", response_model=TopologyResponse)
async def get_topology(
    db: AsyncSession = Depends(get_db),
    _:  User         = Depends(get_current_user),
):
    devices = (await db.execute(select(Device))).scalars().all()
    links   = (await db.execute(select(TopologyLink))).scalars().all()

    nodes = [
        TopologyNode(
            id=d.id, name=d.name, type=d.type,
            status=d.status, ip=d.ip_address,
            x=d.pos_x or 0.0, y=d.pos_y or 0.0,
        )
        for d in devices
    ]
    edges = [
        TopologyEdge(
            id=l.id, source=l.source_id, target=l.target_id,
            label=l.label, type=l.link_type,
        )
        for l in links
    ]
    return TopologyResponse(nodes=nodes, edges=edges)


@router.put("/node/{device_id}")
async def update_node_position(
    device_id: str,
    data:      NodePositionUpdate,
    db:        AsyncSession = Depends(get_db),
    _:         User         = Depends(get_current_user),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    device.pos_x = data.x
    device.pos_y = data.y
    await db.flush()
    return {"id": device.id, "x": data.x, "y": data.y}


@router.post("/link", status_code=201)
async def create_link(
    data: LinkCreate,
    db:   AsyncSession = Depends(get_db),
    _:    User         = Depends(get_current_user),
):
    # Vérifier que les deux devices existent
    for did in [data.source_id, data.target_id]:
        r = await db.execute(select(Device).where(Device.id == did))
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Équipement {did} introuvable")

    # Vérifier qu'un lien n'existe pas déjà
    existing = await db.execute(
        select(TopologyLink).where(
            and_(TopologyLink.source_id == data.source_id,
                 TopologyLink.target_id == data.target_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Lien déjà existant entre ces deux équipements")

    link = TopologyLink(
        source_id=data.source_id,
        target_id=data.target_id,
        label=data.label,
        link_type=data.type,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return {"id": link.id, "source_id": link.source_id, "target_id": link.target_id}


@router.delete("/link/{link_id}")
async def delete_link(
    link_id: str,
    db:      AsyncSession = Depends(get_db),
    _:       User         = Depends(get_current_user),
):
    result = await db.execute(select(TopologyLink).where(TopologyLink.id == link_id))
    link   = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Lien introuvable")
    await db.delete(link)
    return {"message": "Lien supprimé"}
