"""Postcode router voor EVI Backend."""
from fastapi import APIRouter, HTTPException
from database import Database

router = APIRouter()
db = Database()


@router.get("/{postcode}")
async def get_zip_data(postcode: str):
    """Haal regio/distributiekosten op voor een postcode.
    
    Geeft Fluvius zone data terug inclusief
    distributiekosten dag/nacht en capaciteitstarief.
    """
    data = await db.get_zip_data(postcode)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Postcode '{postcode}' niet gevonden"
        )
    return data
