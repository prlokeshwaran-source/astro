from fastapi import APIRouter
from app.utils.i18n import language_list

router = APIRouter(prefix="/languages", tags=["languages"])

@router.get("")
async def get_languages():
    return {"languages": language_list()}
