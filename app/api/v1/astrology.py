from fastapi import APIRouter, Depends, Query
from app.middleware.auth import current_user
from app.schemas.astrology import AstrologyChartRequest
from app.services.astrology_service import generate_chart

router = APIRouter(prefix="/astrology", tags=["astrology"])

@router.post("/chart")
async def chart(body: AstrologyChartRequest, language: str | None = Query(default=None, pattern="^(en|ta|hi)$"), user: dict = Depends(current_user)):
    selected_language = language or user.get("preferred_language", "en")
    return await generate_chart(body, selected_language)
