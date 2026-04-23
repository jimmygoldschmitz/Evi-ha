"""EVI Backend."""
from __future__ import annotations
import logging, httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import Database
from routers import contracts, zip_data, prices, leveranciers, zones, postcodes

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

app = FastAPI(title="EVI Backend", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
db = Database()

@app.on_event("startup")
async def startup():
    await db.init()
    await db.seed_if_empty()

app.include_router(contracts.router, prefix="/contract", tags=["Contracten"])
app.include_router(zip_data.router, prefix="/zip", tags=["Postcode"])
app.include_router(prices.router, prefix="/prices", tags=["Prijzen"])
app.include_router(leveranciers.router, prefix="/leveranciers", tags=["Leveranciers"])
app.include_router(zones.router, prefix="/zones", tags=["Zones"])
app.include_router(postcodes.router, prefix="/postcodes", tags=["Postcodes"])
app.mount("/admin", StaticFiles(directory="static", html=True), name="admin")

@app.get("/")
async def root():
    return {"name": "EVI Backend", "version": "1.0.0", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/day_ahead")
async def get_day_ahead(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://api-dev.smartenergycontrol.be/resource/day_ahead", headers=headers)
        return resp.json()

@app.get("/epex_live")
async def get_epex_live():
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://epexpredictor.smartenergycontrol.be/prices?hours=-1&fixedPrice=0&taxPercent=0&country=BE&evaluation=true&unit=CT_PER_KWH&timezone=Europe%2FBrussels")
        return resp.json()

@app.get("/merged_full/{contract_id}")
async def get_merged_full(contract_id: str):
    import aiosqlite
    from fastapi import HTTPException
    async with aiosqlite.connect("/data/evi.db") as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM contracten WHERE id LIKE ? AND type='afname'", (contract_id+"%",)) as cur:
            a_row = await cur.fetchone()
        async with conn.execute("SELECT * FROM contracten WHERE id LIKE ? AND type='injectie'", (contract_id+"%",)) as cur:
            i_row = await cur.fetchone()
        if not a_row:
            raise HTTPException(status_code=404, detail="Niet gevonden")
        a = dict(a_row)
        i = dict(i_row) if i_row else {}
        afname = {"id":a["id"],"naam":a["naam"],"type":"afname","var_dyn":a["var_dyn"],"a":a["a"],"a_nacht":a["a_nacht"],"b":a["b"],"b_nacht":a["b_nacht"],"c":a["c"],"c_nacht":a["c_nacht"],"d":a["d"],"d_nacht":a["d_nacht"],"gsc":a["gsc"],"wkk":a["wkk"],"prijs":a["prijs"],"prijs_nacht":a["prijs_nacht"],"v_vergoeding":a["v_vergoeding"],"waarde_x_vreg":a["waarde_x_vreg"],"bijz_accijns":4.748,"bijdrage_energie":0.1926,"handelsnaam":a["handelsnaam"],"productnaam":a["productnaam"],"jaarverbruik":a["jaarverbruik"],"formule":a["formule"],"night_weekend_holiday_rate":a["night_weekend_holiday_rate"]}
        injectie = {"id":i.get("id",contract_id+"-INJ"),"naam":i.get("naam",a["naam"]),"type":"injectie","var_dyn":"Dynamisch","a":i.get("a",0.1),"d":i.get("d",-1.2965),"gsc":0.0,"wkk":0.0,"prijs":0.0,"v_vergoeding":0.0,"waarde_x_vreg":0.0,"bijz_accijns":4.748,"bijdrage_energie":0.1926,"formule":i.get("formule","contract.a*resources.epex+contract.d"),"handelsnaam":a["handelsnaam"],"productnaam":a["productnaam"]}
        return {"contract_id":contract_id,"resolution":a["resolution"],"handelsnaam":a["handelsnaam"],"productnaam":a["productnaam"],"afname_contracts":[afname],"injectie_contracts":[injectie]}


# ─── GAS CONTRACTEN ───────────────────────────────────────────

@app.get("/gas_contract/")
async def list_gas_contracts():
    import aiosqlite
    async with aiosqlite.connect("/data/evi.db") as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("""CREATE TABLE IF NOT EXISTS gas_contracten (
            id TEXT PRIMARY KEY, leverancier_id INTEGER, naam TEXT,
            var_dyn TEXT DEFAULT 'Vast', a REAL DEFAULT 0, d REAL DEFAULT 0,
            gsc REAL DEFAULT 0, wkk REAL DEFAULT 0, prijs REAL DEFAULT 0,
            prijs_nacht REAL, formule TEXT, handelsnaam TEXT DEFAULT '',
            productnaam TEXT DEFAULT '')""")
        await conn.commit()
        async with conn.execute("SELECT * FROM gas_contracten") as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

@app.post("/gas_contract/")
async def create_gas_contract(data: dict):
    import aiosqlite
    async with aiosqlite.connect("/data/evi.db") as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS gas_contracten (
            id TEXT PRIMARY KEY, leverancier_id INTEGER, naam TEXT,
            var_dyn TEXT DEFAULT 'Vast', a REAL DEFAULT 0, d REAL DEFAULT 0,
            gsc REAL DEFAULT 0, wkk REAL DEFAULT 0, prijs REAL DEFAULT 0,
            prijs_nacht REAL, formule TEXT, handelsnaam TEXT DEFAULT '',
            productnaam TEXT DEFAULT '')""")
        await conn.execute("""INSERT OR REPLACE INTO gas_contracten
            (id, leverancier_id, naam, var_dyn, a, d, gsc, wkk, prijs, prijs_nacht, formule, handelsnaam, productnaam)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data.get("id"), data.get("leverancier_id"), data.get("naam"),
             data.get("var_dyn","Vast"), data.get("a",0), data.get("d",0),
             data.get("gsc",0), data.get("wkk",0), data.get("prijs",0),
             data.get("prijs_nacht"), data.get("formule"),
             data.get("handelsnaam",""), data.get("productnaam","")))
        await conn.commit()
    return {"status": "ok"}

@app.put("/gas_contract/{contract_id}")
async def update_gas_contract(contract_id: str, data: dict):
    import aiosqlite
    async with aiosqlite.connect("/data/evi.db") as conn:
        await conn.execute("""UPDATE gas_contracten SET
            naam=?, var_dyn=?, a=?, d=?, gsc=?, wkk=?, prijs=?, prijs_nacht=?,
            formule=?, handelsnaam=?, productnaam=?
            WHERE id=?""",
            (data.get("naam"), data.get("var_dyn","Vast"),
             data.get("a",0), data.get("d",0), data.get("gsc",0),
             data.get("wkk",0), data.get("prijs",0), data.get("prijs_nacht"),
             data.get("formule"), data.get("handelsnaam",""), data.get("productnaam",""),
             contract_id))
        await conn.commit()
    return {"status": "ok"}

@app.delete("/gas_contract/{contract_id}")
async def delete_gas_contract(contract_id: str):
    import aiosqlite
    async with aiosqlite.connect("/data/evi.db") as conn:
        await conn.execute("DELETE FROM gas_contracten WHERE id=?", (contract_id,))
        await conn.commit()
    return {"status": "ok"}

@app.get("/gas_full/{contract_id}")
async def get_gas_full(contract_id: str):
    import aiosqlite
    from fastapi import HTTPException
    async with aiosqlite.connect("/data/evi.db") as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM gas_contracten WHERE id=?", (contract_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Gas contract niet gevonden")
        c = dict(row)
        return {
            "contract_id": contract_id,
            "afname": {
                "id": c["id"], "naam": c["naam"], "var_dyn": c["var_dyn"],
                "a": c["a"], "d": c["d"], "gsc": c["gsc"], "wkk": c["wkk"],
                "prijs": c["prijs"], "prijs_nacht": c["prijs_nacht"],
                "bijz_accijns": 4.748, "bijdrage_energie": 0.1926,
                "formule": c["formule"], "handelsnaam": c["handelsnaam"],
                "productnaam": c["productnaam"],
            }
        }
