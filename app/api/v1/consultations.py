from fastapi import APIRouter, Depends, HTTPException, Query
from app.config.database import database
from app.middleware.auth import current_user, require_roles
from app.models import new_id, public_document, utc_now
from app.schemas.consultation import ConsultationCreate, ConsultationStatusUpdate
from app.services.consultation_service import transition_consultation
router = APIRouter(prefix="/consultations", tags=["consultations"])
@router.post("", status_code=201)
async def book(body: ConsultationCreate, user: dict = Depends(require_roles("USER"))):
    astro = await database.astrologers.find_one({"_id": body.astrologer_id, "approval_status": "APPROVED"})
    if not astro: raise HTTPException(404, "Approved astrologer not found")
    if body.scheduled_at <= utc_now(): raise HTTPException(400, "Consultation must be in the future")
    doc = {"_id": new_id(), "user_id": user["_id"], "astrologer_id": astro["_id"], "consultation_type": body.consultation_type, "scheduled_at": body.scheduled_at, "duration_minutes": body.duration_minutes, "status": "PENDING", "payment_status": "UNPAID", "created_at": utc_now()}
    await database.consultations.insert_one(doc)
    return public_document(doc)
@router.get("")
async def listing(user: dict = Depends(current_user), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    if user["role"] == "USER": query = {"user_id": user["_id"]}
    elif user["role"] == "ASTROLOGER":
        profile = await database.astrologers.find_one({"user_id": user["_id"]})
        query = {"astrologer_id": profile["_id"] if profile else ""}
    else: query = {}
    cur = database.consultations.find(query).sort("scheduled_at", -1).skip((page-1)*page_size).limit(page_size)
    items = []
    async for consultation in cur:
        item = public_document(consultation)
        profile = await database.astrologers.find_one({"_id": consultation["astrologer_id"]})
        client = await database.users.find_one({"_id": consultation["user_id"]})
        if user["role"] == "USER":
            item["counterpart_name"] = (profile or {}).get("name", "Astrologer")
            item["counterpart_role"] = "ASTROLOGER"
        elif user["role"] == "ASTROLOGER":
            item["counterpart_name"] = (client or {}).get("name", "Client")
            item["counterpart_role"] = "USER"
        else:
            item["counterpart_name"] = (client or {}).get("name", "Client")
            item["counterpart_role"] = "USER"
        items.append(item)
    return {"items": items, "total": await database.consultations.count_documents(query), "page": page, "page_size": page_size}
@router.patch("/{consultation_id}")
async def update(consultation_id: str, body: ConsultationStatusUpdate, user: dict = Depends(current_user)):
    updated = await transition_consultation(
        consultation_id, user["role"], user["_id"], body.status, body.notes
    )
    return public_document(updated)
