from fastapi import APIRouter
from app.api.v1 import admin, astrologers, astrology, auth, calls, chat, complaints, consultations, languages, locations, payments, reports, reviews, users, voice

api_router = APIRouter()
for module in (auth, users, astrologers, astrology, languages, locations, consultations, chat, calls, payments, reports, reviews, complaints, admin, voice):
    api_router.include_router(module.router)
