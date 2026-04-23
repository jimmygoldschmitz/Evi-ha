"""Router voor postcodes beheer."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import Database

router = APIRouter()
db = Database()


class PostcodeCreate(BaseModel):
    postcode: str
    gemeente: str
    fluvius_zone_id: int


@router.get("/")
async def list_postcodes():
    """Lijst van alle postcodes."""
    return await db.get_all_postcodes()


@router.post("/")
async def create_postcode(data: PostcodeCreate):
    """Nieuwe postcode toevoegen."""
    result = await db.create_postcode(data.postcode, data.gemeente, data.fluvius_zone_id)
    if not result:
        raise HTTPException(status_code=400, detail="Kon postcode niet aanmaken")
    return result


@router.delete("/{postcode}")
async def delete_postcode(postcode: str):
    """Postcode verwijderen."""
    await db.delete_postcode(postcode)
    return {"status": "ok"}
