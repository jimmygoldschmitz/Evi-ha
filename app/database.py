"""Database module voor EVI Backend."""
from __future__ import annotations

import json
import logging
import aiosqlite
from pathlib import Path
from typing import Optional

_LOGGER = logging.getLogger(__name__)

DB_PATH = Path("/data/evi.db")
SEED_PATH = Path(__file__).parent / "data" / "seed.json"


class Database:
    """SQLite database manager."""

    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async def init(self):
        """Maak tabellen aan als ze niet bestaan."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leveranciers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naam TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS contracten (
                    id TEXT PRIMARY KEY,
                    leverancier_id INTEGER,
                    naam TEXT NOT NULL,
                    type TEXT NOT NULL,
                    var_dyn TEXT NOT NULL,
                    a REAL DEFAULT 0,
                    a_nacht REAL,
                    b REAL DEFAULT 0,
                    b_nacht REAL,
                    c REAL DEFAULT 0,
                    c_nacht REAL,
                    d REAL DEFAULT 0,
                    d_nacht REAL,
                    gsc REAL DEFAULT 0,
                    wkk REAL DEFAULT 0,
                    prijs REAL DEFAULT 0,
                    prijs_nacht REAL,
                    waarde_x_vreg REAL DEFAULT 0,
                    v_vergoeding REAL DEFAULT 0,
                    night_weekend_holiday_rate INTEGER DEFAULT 0,
                    formule TEXT,
                    resolution INTEGER DEFAULT 15,
                    jaarverbruik REAL DEFAULT 3500,
                    handelsnaam TEXT DEFAULT "",
                    productnaam TEXT DEFAULT "",
                    FOREIGN KEY (leverancier_id) REFERENCES leveranciers(id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS contract_paren (
                    id TEXT PRIMARY KEY,
                    naam TEXT NOT NULL,
                    leverancier_id INTEGER,
                    afname_contract_id TEXT,
                    injectie_contract_id TEXT,
                    resolution INTEGER DEFAULT 15,
                    FOREIGN KEY (leverancier_id) REFERENCES leveranciers(id),
                    FOREIGN KEY (afname_contract_id) REFERENCES contracten(id),
                    FOREIGN KEY (injectie_contract_id) REFERENCES contracten(id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS fluvius_zones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_naam TEXT NOT NULL,
                    distributiekost_dag REAL NOT NULL,
                    distributiekost_nacht REAL NOT NULL,
                    distributiekost_nacht_excl REAL,
                    capaciteitstarief REAL DEFAULT 0,
                    databeheer REAL DEFAULT 0,
                    distributiekost_dag_gas REAL DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS postcodes (
                    postcode TEXT PRIMARY KEY,
                    gemeente TEXT NOT NULL,
                    fluvius_zone_id INTEGER NOT NULL,
                    FOREIGN KEY (fluvius_zone_id) REFERENCES fluvius_zones(id)
                )
            """)

            await db.commit()
            _LOGGER.info("Database tabellen aangemaakt")

    async def seed_if_empty(self):
        """Laad seed data als de database leeg is."""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM leveranciers")
            count = (await cursor.fetchone())[0]

            if count == 0:
                _LOGGER.info("Database leeg - seed data laden...")
                await self._load_seed(db)
                _LOGGER.info("Seed data geladen!")
            else:
                _LOGGER.info("Database al gevuld (%d leveranciers)", count)

    async def _load_seed(self, db):
        """Laad seed data vanuit seed.json."""
        if not SEED_PATH.exists():
            _LOGGER.warning("Geen seed.json gevonden, database blijft leeg")
            return

        with open(SEED_PATH, "r", encoding="utf-8") as f:
            seed = json.load(f)

        for zone in seed.get("fluvius_zones", []):
            await db.execute("""
                INSERT OR REPLACE INTO fluvius_zones
                (id, zone_naam, distributiekost_dag, distributiekost_nacht,
                 distributiekost_nacht_excl, capaciteitstarief, databeheer, distributiekost_dag_gas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                zone["id"], zone["zone_naam"],
                zone["distributiekost_dag"], zone["distributiekost_nacht"],
                zone.get("distributiekost_nacht_excl"),
                zone.get("capaciteitstarief", 0), zone.get("databeheer", 0),
                zone.get("distributiekost_dag_gas", 0)
            ))

        for pc in seed.get("postcodes", []):
            await db.execute("""
                INSERT OR REPLACE INTO postcodes (postcode, gemeente, fluvius_zone_id)
                VALUES (?, ?, ?)
            """, (pc["postcode"], pc["gemeente"], pc["fluvius_zone_id"]))

        for lev in seed.get("leveranciers", []):
            await db.execute("""
                INSERT OR REPLACE INTO leveranciers (id, naam, slug)
                VALUES (?, ?, ?)
            """, (lev["id"], lev["naam"], lev["slug"]))

        for c in seed.get("contracten", []):
            await db.execute("""
                INSERT OR REPLACE INTO contracten
                (id, leverancier_id, naam, type, var_dyn, a, a_nacht, b, b_nacht,
                 c, c_nacht, d, d_nacht, gsc, wkk, prijs, prijs_nacht, waarde_x_vreg,
                 v_vergoeding, night_weekend_holiday_rate, formule, resolution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["id"], c["leverancier_id"], c["naam"], c["type"], c["var_dyn"],
                c.get("a", 0), c.get("a_nacht"), c.get("b", 0), c.get("b_nacht"),
                c.get("c", 0), c.get("c_nacht"), c.get("d", 0), c.get("d_nacht"),
                c.get("gsc", 0), c.get("wkk", 0), c.get("prijs", 0), c.get("prijs_nacht"),
                c.get("waarde_x_vreg", 0), c.get("v_vergoeding", 0),
                1 if c.get("night_weekend_holiday_rate", False) else 0,
                c.get("formule"), c.get("resolution", 15)
            ))

        for cp in seed.get("contract_paren", []):
            await db.execute("""
                INSERT OR REPLACE INTO contract_paren
                (id, naam, leverancier_id, afname_contract_id, injectie_contract_id, resolution)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cp["id"], cp["naam"], cp["leverancier_id"],
                cp["afname_contract_id"], cp["injectie_contract_id"],
                cp.get("resolution", 15)
            ))

        await db.commit()

    # ── CONTRACT PAREN ────────────────────────────────────────────────────────

    async def get_contract_pair(self, contract_id: str) -> dict | None:
        """Haal een contract paar op met alle details."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM contract_paren WHERE id = ?", (contract_id,)
            )
            pair = await cursor.fetchone()
            if not pair:
                return None
            pair = dict(pair)

            cursor = await db.execute("SELECT * FROM contracten WHERE id = ?", (pair["afname_contract_id"],))
            afname = await cursor.fetchone()

            cursor = await db.execute("SELECT * FROM contracten WHERE id = ?", (pair["injectie_contract_id"],))
            injectie = await cursor.fetchone()

            cursor = await db.execute("SELECT * FROM leveranciers WHERE id = ?", (pair["leverancier_id"],))
            leverancier = await cursor.fetchone()

            return {
                "contract_id": pair["id"],
                "naam": pair["naam"],
                "leverancier": dict(leverancier) if leverancier else {},
                "resolution": pair["resolution"],
                "afname": dict(afname) if afname else {},
                "injectie": dict(injectie) if injectie else {},
            }

    async def get_all_contract_pairs(self) -> list:
        """Lijst van alle contract paren."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT cp.id, cp.naam, l.naam as leverancier, cp.resolution
                FROM contract_paren cp
                JOIN leveranciers l ON cp.leverancier_id = l.id
                ORDER BY l.naam, cp.naam
            """)
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def create_contract_pair(self, data: dict) -> dict | None:
        """Nieuw contract paar aanmaken."""
        async with aiosqlite.connect(DB_PATH) as db:
            afname = data["afname"]
            injectie = data["injectie"]

            await db.execute("""
                INSERT OR REPLACE INTO contracten
                (id, leverancier_id, naam, type, var_dyn, a, a_nacht, d, d_nacht,
                 gsc, wkk, prijs, prijs_nacht, waarde_x_vreg, v_vergoeding,
                 night_weekend_holiday_rate, formule, resolution)
                VALUES (?, ?, ?, 'afname', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                afname["id"], data["leverancier_id"], afname.get("naam", afname["id"]),
                afname.get("var_dyn", "Dynamisch"),
                afname.get("a", 0), afname.get("a_nacht"),
                afname.get("d", 0), afname.get("d_nacht"),
                afname.get("gsc", 0), afname.get("wkk", 0),
                afname.get("prijs", 0), afname.get("prijs_nacht"),
                afname.get("waarde_x_vreg", 0), afname.get("v_vergoeding", 0),
                1 if afname.get("night_weekend_holiday_rate", False) else 0,
                afname.get("formule"), data.get("resolution", 15)
            ))

            await db.execute("""
                INSERT OR REPLACE INTO contracten
                (id, leverancier_id, naam, type, var_dyn, a, a_nacht, d, d_nacht,
                 gsc, wkk, prijs, prijs_nacht, waarde_x_vreg, v_vergoeding,
                 night_weekend_holiday_rate, formule, resolution)
                VALUES (?, ?, ?, 'injectie', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                injectie["id"], data["leverancier_id"], injectie.get("naam", injectie["id"]),
                injectie.get("var_dyn", "Dynamisch"),
                injectie.get("a", 0), injectie.get("a_nacht"),
                injectie.get("d", 0), injectie.get("d_nacht"),
                injectie.get("gsc", 0), injectie.get("wkk", 0),
                injectie.get("prijs", 0), injectie.get("prijs_nacht"),
                injectie.get("waarde_x_vreg", 0), injectie.get("v_vergoeding", 0),
                1 if injectie.get("night_weekend_holiday_rate", False) else 0,
                injectie.get("formule"), data.get("resolution", 15)
            ))

            await db.execute("""
                INSERT OR REPLACE INTO contract_paren
                (id, naam, leverancier_id, afname_contract_id, injectie_contract_id, resolution)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["naam"], data["leverancier_id"],
                afname["id"], injectie["id"], data.get("resolution", 15)
            ))

            await db.commit()
            return await self.get_contract_pair(data["id"])

    async def update_contract_pair(self, contract_id: str, data: dict) -> dict | None:
        """Contract paar bijwerken."""
        async with aiosqlite.connect(DB_PATH) as db:
            afname = data["afname"]
            injectie = data["injectie"]

            await db.execute("""
                UPDATE contracten SET
                    var_dyn=?, a=?, a_nacht=?, d=?, d_nacht=?, gsc=?, wkk=?,
                    prijs=?, prijs_nacht=?, waarde_x_vreg=?, v_vergoeding=?,
                    night_weekend_holiday_rate=?, formule=?, resolution=?,
                    handelsnaam=?, productnaam=?, jaarverbruik=?
                WHERE id=?
            """, (
                afname.get("var_dyn", "Dynamisch"),
                afname.get("a", 0), afname.get("a_nacht"),
                afname.get("d", 0), afname.get("d_nacht"),
                afname.get("gsc", 0), afname.get("wkk", 0),
                afname.get("prijs", 0), afname.get("prijs_nacht"),
                afname.get("waarde_x_vreg", 0), afname.get("v_vergoeding", 0),
                1 if afname.get("night_weekend_holiday_rate", False) else 0,
                afname.get("formule"), data.get("resolution", 15),
                afname.get("handelsnaam", ""), afname.get("productnaam", ""),
                afname.get("jaarverbruik", 3500),
                afname["id"]
            ))

            await db.execute("""
                UPDATE contracten SET
                    var_dyn=?, a=?, a_nacht=?, d=?, d_nacht=?, gsc=?, wkk=?,
                    prijs=?, formule=?, resolution=?,
                    handelsnaam=?, productnaam=?
                WHERE id=?
            """, (
                injectie.get("var_dyn", "Dynamisch"),
                injectie.get("a", 0), injectie.get("a_nacht"),
                injectie.get("d", 0), injectie.get("d_nacht"),
                injectie.get("gsc", 0), injectie.get("wkk", 0),
                injectie.get("prijs", 0), injectie.get("formule"),
                data.get("resolution", 15),
                injectie.get("handelsnaam", ""), injectie.get("productnaam", ""),
                injectie["id"]
            ))

            await db.execute("""
                UPDATE contract_paren SET naam=?, leverancier_id=?, resolution=?
                WHERE id=?
            """, (data["naam"], data["leverancier_id"], data.get("resolution", 15), contract_id))

            await db.commit()
            return await self.get_contract_pair(contract_id)

    async def delete_contract_pair(self, contract_id: str):
        """Contract paar verwijderen."""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT * FROM contract_paren WHERE id = ?", (contract_id,))
            pair = await cursor.fetchone()
            if pair:
                await db.execute("DELETE FROM contracten WHERE id = ?", (pair[3],))
                await db.execute("DELETE FROM contracten WHERE id = ?", (pair[4],))
                await db.execute("DELETE FROM contract_paren WHERE id = ?", (contract_id,))
                await db.commit()

    # ── ZIP DATA ──────────────────────────────────────────────────────────────

    async def get_zip_data(self, postcode: str) -> dict | None:
        """Haal regio data op voor een postcode."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT p.postcode, p.gemeente, fz.*
                FROM postcodes p
                JOIN fluvius_zones fz ON p.fluvius_zone_id = fz.id
                WHERE p.postcode = ?
            """, (postcode,))
            row = await cursor.fetchone()
            if not row:
                return None
            row = dict(row)
            return {
                "postcode": row["postcode"],
                "municipality": row["gemeente"],
                "region_electricity": {
                    "region_name": row["zone_naam"],
                    "elektriciteit": {
                        "distributiekost_dag": row["distributiekost_dag"],
                        "distributiekost_nacht": row["distributiekost_nacht"],
                        "distributiekost_nacht_excl": row.get("distributiekost_nacht_excl"),
                        "capaciteitstarief": row["capaciteitstarief"],
                        "databeheer": row["databeheer"],
                    }
                },
                "region_gas": {
                    "region_name": row["zone_naam"],
                    "gas": {
                        "distributiekost_dag": row["distributiekost_dag_gas"],
                    }
                }
            }

    # ── POSTCODES ─────────────────────────────────────────────────────────────

    async def get_all_postcodes(self) -> list:
        """Lijst van alle postcodes."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT p.postcode, p.gemeente, fz.zone_naam, fz.id as zone_id
                FROM postcodes p
                JOIN fluvius_zones fz ON p.fluvius_zone_id = fz.id
                ORDER BY p.postcode
            """)
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def create_postcode(self, postcode: str, gemeente: str, zone_id: int) -> dict:
        """Nieuwe postcode toevoegen."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO postcodes (postcode, gemeente, fluvius_zone_id) VALUES (?, ?, ?)",
                (postcode, gemeente, zone_id)
            )
            await db.commit()
            return {"postcode": postcode, "gemeente": gemeente, "fluvius_zone_id": zone_id}

    async def delete_postcode(self, postcode: str):
        """Postcode verwijderen."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM postcodes WHERE postcode = ?", (postcode,))
            await db.commit()

    # ── FLUVIUS ZONES ─────────────────────────────────────────────────────────

    async def get_all_zones(self) -> list:
        """Lijst van alle Fluvius zones."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM fluvius_zones ORDER BY zone_naam")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def create_zone(self, data: dict) -> dict:
        """Nieuwe Fluvius zone aanmaken."""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                INSERT INTO fluvius_zones
                (zone_naam, distributiekost_dag, distributiekost_nacht,
                 distributiekost_nacht_excl, capaciteitstarief, databeheer, distributiekost_dag_gas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data["zone_naam"], data["distributiekost_dag"], data["distributiekost_nacht"],
                data.get("distributiekost_nacht_excl"), data.get("capaciteitstarief", 0),
                data.get("databeheer", 0), data.get("distributiekost_dag_gas", 0)
            ))
            await db.commit()
            zone_id = cursor.lastrowid
            return {"id": zone_id, **data}

    async def update_zone(self, zone_id: int, data: dict) -> dict | None:
        """Fluvius zone bijwerken."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE fluvius_zones SET
                    zone_naam = ?, distributiekost_dag = ?, distributiekost_nacht = ?,
                    distributiekost_nacht_excl = ?, capaciteitstarief = ?,
                    databeheer = ?, distributiekost_dag_gas = ?
                WHERE id = ?
            """, (
                data["zone_naam"], data["distributiekost_dag"], data["distributiekost_nacht"],
                data.get("distributiekost_nacht_excl"), data.get("capaciteitstarief", 0),
                data.get("databeheer", 0), data.get("distributiekost_dag_gas", 0),
                zone_id
            ))
            await db.commit()
            return {"id": zone_id, **data}

    async def delete_zone(self, zone_id: int):
        """Fluvius zone verwijderen."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM fluvius_zones WHERE id = ?", (zone_id,))
            await db.commit()

    # ── LEVERANCIERS ──────────────────────────────────────────────────────────

    async def get_all_leveranciers(self) -> list:
        """Lijst van alle leveranciers."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM leveranciers ORDER BY naam")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def create_leverancier(self, naam: str, slug: str) -> dict:
        """Nieuwe leverancier aanmaken."""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "INSERT INTO leveranciers (naam, slug) VALUES (?, ?)",
                (naam, slug)
            )
            await db.commit()
            return {"id": cursor.lastrowid, "naam": naam, "slug": slug}

    async def delete_leverancier(self, leverancier_id: int):
        """Leverancier verwijderen."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM leveranciers WHERE id = ?", (leverancier_id,))
            await db.commit()
