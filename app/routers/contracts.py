"""Router voor contracten beheer."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import Database

router = APIRouter()
db = Database()


class ContractAfname(BaseModel):
    id: str
    var_dyn: str = "Dynamisch"
    a: float = 0
    a_nacht: Optional[float] = None
    d: float = 0
    d_nacht: Optional[float] = None
    gsc: float = 0
    wkk: float = 0
    prijs: float = 0
    prijs_nacht: Optional[float] = None
    waarde_x_vreg: float = 0
    v_vergoeding: float = 0
    night_weekend_holiday_rate: bool = False
    formule: Optional[str] = None
    handelsnaam: str = ""
    productnaam: str = ""
    jaarverbruik: float = 3500


class ContractInjectie(BaseModel):
    id: str
    var_dyn: str = "Dynamisch"
    a: float = 0
    a_nacht: Optional[float] = None
    d: float = 0
    d_nacht: Optional[float] = None
    gsc: float = 0
    wkk: float = 0
    prijs: float = 0
    formule: Optional[str] = None
    handelsnaam: str = ""
    productnaam: str = ""


class ContractPaarCreate(BaseModel):
    id: str
    naam: str
    leverancier_id: int
    resolution: int = 15
    afname: ContractAfname
    injectie: ContractInjectie


@router.get("/")
async def list_contracts():
    """Lijst van alle beschikbare contracten."""
    return await db.get_all_contract_pairs()


@router.get("/{contract_id}")
async def get_contract(contract_id: str):
    """Haal contract data op via contract ID."""
    data = await db.get_contract_pair(contract_id)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Contract '{contract_id}' niet gevonden"
        )
    return data


@router.post("/")
async def create_contract(data: ContractPaarCreate):
    """Nieuw contract paar aanmaken."""
    result = await db.create_contract_pair(data.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Kon contract niet aanmaken")
    return result


@router.put("/{contract_id}")
async def update_contract(contract_id: str, data: ContractPaarCreate):
    """Contract paar bijwerken."""
    existing = await db.get_contract_pair(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Contract '{contract_id}' niet gevonden")
    result = await db.update_contract_pair(contract_id, data.dict())
    return result


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str):
    """Contract paar verwijderen."""
    await db.delete_contract_pair(contract_id)
    return {"status": "ok"}
