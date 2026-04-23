"""Router voor leveranciers beheer."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import Database

router = APIRouter()
db = Database()


class LeverancierCreate(BaseModel):
    naam: str
    slug: str


@router.get("/")
async def list_leveranciers():
    """Lijst van alle leveranciers."""
    return await db.get_all_leveranciers()


@router.post("/")
async def create_leverancier(data: LeverancierCreate):
    """Nieuwe leverancier aanmaken."""
    result = await db.create_leverancier(data.naam, data.slug)
    if not result:
        raise HTTPException(status_code=400, detail="Kon leverancier niet aanmaken")
    return result


@router.delete("/{leverancier_id}")
async def delete_leverancier(leverancier_id: int):
    """Leverancier verwijderen."""
    await db.delete_leverancier(leverancier_id)
    return {"status": "ok"}
