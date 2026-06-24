import csv
import io
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.models import Device, Intervention
from app.models.user import User
from app.schemas.schemas import (
    DeviceCreate, DeviceUpdate, DeviceOut, DeviceListResponse,
)

router = APIRouter()


def _now():
    return datetime.now(timezone.utc)


# ─── LIST ────────────────────────────────────────────────────────────────────

@router.get("", response_model=DeviceListResponse)
async def list_devices(
    page:     int            = Query(1,   ge=1),
    limit:    int            = Query(20,  ge=1, le=100),
    type:     Optional[str]  = None,
    status:   Optional[str]  = None,
    location: Optional[str]  = None,
    q:        Optional[str]  = None,
    sort:     Optional[str]  = Query("name", pattern="^(name|ip_address|status|created_at)$"),
    order:    Optional[str]  = Query("asc",  pattern="^(asc|desc)$"),
    db:       AsyncSession   = Depends(get_db),
    _:        User           = Depends(get_current_user),
):
    query = select(Device)

    if type:
        query = query.where(Device.type == type)
    if status:
        query = query.where(Device.status == status)
    if location:
        query = query.where(Device.location.ilike(f"%{location}%"))
    if q:
        query = query.where(or_(
            Device.name.ilike(f"%{q}%"),
            Device.ip_address.ilike(f"%{q}%"),
            Device.model.ilike(f"%{q}%"),
        ))

    sort_col = getattr(Device, sort, Device.name)
    query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    devices = result.scalars().all()

    return DeviceListResponse(
        data=devices,
        pagination={
            "page": page, "limit": limit,
            "total": total, "pages": math.ceil(total / limit),
        },
    )


# ─── GET ONE ─────────────────────────────────────────────────────────────────

@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(
    device_id: str,
    db:        AsyncSession = Depends(get_db),
    _:         User         = Depends(get_current_user),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    return device


# ─── CREATE ──────────────────────────────────────────────────────────────────

@router.post("", response_model=DeviceOut, status_code=201)
async def create_device(
    data: DeviceCreate,
    db:   AsyncSession = Depends(get_db),
    _:    User         = Depends(require_role("admin", "technicien")),
):
    # Vérifier unicité IP
    existing = await db.execute(select(Device).where(Device.ip_address == data.ip_address))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"IP {data.ip_address} déjà utilisée")

    # Vérifier unicité nom
    existing_name = await db.execute(select(Device).where(Device.name == data.name))
    if existing_name.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Nom '{data.name}' déjà utilisé")

    device = Device(**data.model_dump())
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device


# ─── UPDATE ──────────────────────────────────────────────────────────────────

@router.put("/{device_id}", response_model=DeviceOut)
async def update_device(
    device_id: str,
    data:      DeviceUpdate,
    db:        AsyncSession = Depends(get_db),
    current:   User         = Depends(require_role("admin", "technicien")),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")

    update_data = data.model_dump(exclude_none=True)

    # Vérifier unicité IP si changée
    if "ip_address" in update_data and update_data["ip_address"] != device.ip_address:
        conflict = await db.execute(
            select(Device).where(Device.ip_address == update_data["ip_address"])
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="IP déjà utilisée")

    old_status = device.status
    for key, val in update_data.items():
        setattr(device, key, val)
    device.updated_at = _now()

    # Créer une intervention automatique si le statut change
    if "status" in update_data and update_data["status"] != old_status:
        intervention = Intervention(
            device_id=device.id,
            author_id=current.id,
            type="Panne" if update_data["status"] == "Panne" else "Maintenance",
            description=f"Changement de statut : {old_status} → {update_data['status']}",
        )
        db.add(intervention)

    await db.flush()
    await db.refresh(device)
    return device


# ─── DELETE ──────────────────────────────────────────────────────────────────

@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    db:        AsyncSession = Depends(get_db),
    _:         User         = Depends(require_role("admin")),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")

    name = device.name
    await db.delete(device)
    return {"message": f"Équipement {name} supprimé", "deleted_at": _now()}


# ─── IMPORT CSV ──────────────────────────────────────────────────────────────

@router.post("/import")
async def import_csv(
    file:    UploadFile = File(...),
    db:      AsyncSession = Depends(get_db),
    _:       User         = Depends(require_role("admin", "technicien")),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Format CSV requis")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 Mo)")

    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    required = {"name", "type", "ip_address"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"Colonnes requises manquantes : {required - set(reader.fieldnames or [])}",
        )

    imported, skipped, errors = 0, 0, []

    for row_num, row in enumerate(reader, start=2):
        try:
            data = DeviceCreate(
                name=row["name"].strip(),
                type=row.get("type", "Ordinateur").strip(),
                model=row.get("model", "").strip() or None,
                ip_address=row["ip_address"].strip(),
                mac_address=row.get("mac_address", "").strip() or None,
                location=row.get("location", "").strip() or None,
                status=row.get("status", "Actif").strip() or "Actif",
            )
        except Exception as e:
            errors.append({"row": row_num, "reason": str(e)})
            skipped += 1
            continue

        # Check duplicate IP
        exists = await db.execute(select(Device).where(Device.ip_address == data.ip_address))
        if exists.scalar_one_or_none():
            errors.append({"row": row_num, "reason": f"IP {data.ip_address} déjà existante"})
            skipped += 1
            continue

        db.add(Device(**data.model_dump()))
        imported += 1

    await db.flush()
    return {"imported": imported, "skipped": skipped, "errors": errors}


# ─── EXPORT CSV ──────────────────────────────────────────────────────────────

@router.get("/export")
async def export_csv(
    format: str           = Query("csv", pattern="^(csv|json)$"),
    status: Optional[str] = None,
    db:     AsyncSession  = Depends(get_db),
    _:      User          = Depends(get_current_user),
):
    query = select(Device)
    if status:
        query = query.where(Device.status == status)

    result  = await db.execute(query)
    devices = result.scalars().all()

    output  = io.StringIO()
    writer  = csv.writer(output)
    writer.writerow(["name","type","model","ip_address","mac_address","location","status","snmp_enabled"])
    for d in devices:
        writer.writerow([d.name, d.type, d.model, d.ip_address,
                         d.mac_address, d.location, d.status, d.snmp_enabled])

    output.seek(0)
    filename = f"netadmin_export_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
