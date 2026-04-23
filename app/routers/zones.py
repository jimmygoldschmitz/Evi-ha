"""Router voor Fluvius zones beheer."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import Database

router = APIRouter()
db = Database()


class ZoneCreate(BaseModel):
    zone_naam: str
    distributiekost_dag: float
    distributiekost_nacht: float
    distributiekost_nacht_excl: Optional[float] = None
    capaciteitstarief: float = 0
    databeheer: float = 0
    distributiekost_dag_gas: float = 0


@router.get("/")
async def list_zones():
    """Lijst van alle Fluvius zones."""
    return await db.get_all_zones()


@router.post("/")
async def create_zone(data: ZoneCreate):
    """Nieuwe Fluvius zone aanmaken."""
    result = await db.create_zone(data.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Kon zone niet aanmaken")
    return result


@router.put("/{zone_id}")
async def update_zone(zone_id: int, data: ZoneCreate):
    """Fluvius zone bijwerken."""
    result = await db.update_zone(zone_id, data.dict())
    if not result:
        raise HTTPException(status_code=404, detail="Zone niet gevonden")
    return result


@router.delete("/{zone_id}")
async def delete_zone(zone_id: int):
    """Fluvius zone verwijderen."""
    await db.delete_zone(zone_id)
    return {"status": "ok"}
