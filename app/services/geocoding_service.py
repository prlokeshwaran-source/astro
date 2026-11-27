import asyncio
import time
from fastapi import HTTPException
import httpx
from app.config.database import database
from app.config.settings import settings

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
MIN_INTERVAL_SECONDS = 1.05
_request_lock = asyncio.Lock()
_last_request_at = 0.0

async def search_birthplace(query: str, language: str = "en") -> list[dict]:
    global _last_request_at
    normalized = " ".join(query.strip().split())
    if len(normalized) < 2:
        raise HTTPException(422, "Enter at least two characters for the birthplace")
    cache_key = f"{language}:{normalized.casefold()}"
    cached = await database.geocode_cache.find_one({"_id": cache_key})
    if cached:
        return cached["results"]

    params = {"q": normalized, "format": "jsonv2", "limit": 5, "addressdetails": 1,
              "accept-language": {"en": "en", "ta": "ta", "hi": "hi"}.get(language, "en")}
    headers = {"User-Agent": settings.geocoder_user_agent}
    try:
        async with _request_lock:
            wait = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
            if wait > 0:
                await asyncio.sleep(wait)
            async with httpx.AsyncClient(timeout=12, headers=headers) as client:
                response = await client.get(NOMINATIM_URL, params=params)
                response.raise_for_status()
                places = response.json()
            _last_request_at = time.monotonic()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Location lookup is temporarily unavailable") from exc

    results = [{"name": p.get("name") or p.get("display_name", ""),
                "display_name": p.get("display_name", ""),
                "latitude": float(p["lat"]), "longitude": float(p["lon"])}
               for p in places if p.get("lat") and p.get("lon")]
    await database.geocode_cache.update_one({"_id": cache_key}, {"$set": {"query": normalized,
        "language": language, "results": results}}, upsert=True)
    return results

