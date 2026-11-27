from typing import Literal
from fastapi import APIRouter, Query
from app.services.geocoding_service import search_birthplace

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get("/search")
async def location_search(
    q: str = Query(min_length=2, max_length=120),
    language: Literal["en", "ta", "hi"] = "en",
):
    results = await search_birthplace(q, language)
    return {
        "query": q,
        "results": results,
        "attribution": "\u00a9 OpenStreetMap contributors",
    }
