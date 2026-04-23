"""Prijzen router voor EVI Backend - proxy naar predictor."""
from __future__ import annotations

import aiohttp
import logging
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

_LOGGER = logging.getLogger(__name__)

PREDICTOR_URL = "https://epexpredictor.smartenergycontrol.be"

router = APIRouter()


@router.get("/")
async def get_prices(
    hours: int = Query(default=72, description="Aantal uren vooruit"),
    country: str = Query(default="BE", description="Land (BE, NL, DE, ...)"),
    unit: str = Query(default="CT_PER_KWH", description="Eenheid"),
):
    """Haal EPEX day-ahead + predicted prijzen op.
    
    Proxy naar de predictor API.
    Later vervangen door eigen predictor instance.
    """
    now = datetime.now(timezone.utc).astimezone()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = midnight - timedelta(hours=2)
    start_ts = quote(start_time.strftime("%Y-%m-%d %H:%M:%S"))

    url = (
        f"{PREDICTOR_URL}/prices"
        f"?hours={hours}"
        f"&startTs={start_ts}"
        f"&country={country}"
        f"&evaluation=false"
        f"&unit={unit}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error = await resp.text()
                    raise HTTPException(
                        status_code=resp.status,
                        detail=f"Predictor API fout: {error}"
                    )
    except aiohttp.ClientError as err:
        raise HTTPException(status_code=503, detail=f"Predictor niet bereikbaar: {err}")
