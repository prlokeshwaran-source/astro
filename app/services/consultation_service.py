from datetime import datetime, timedelta
from fastapi import HTTPException
from app.config.database import database
from app.models import new_id, utc_now

VALID_TYPES = {"CHAT", "AUDIO", "VIDEO"}
ALLOWED_TRANSITIONS = {
    "PENDING": {"ACCEPTED", "REJECTED", "CANCELLED"},
    "ACCEPTED": {"IN_PROGRESS", "CANCELLED"},
    "IN_PROGRESS": {"COMPLETED"},
}

async def create_consultation(user_id: str, astrologer_id: str, kind: str,
                              scheduled_at: datetime, duration_minutes: int = 30) -> dict:
    kind = kind.upper()
    if kind not in VALID_TYPES:
        raise HTTPException(422, "Consultation type must be CHAT, AUDIO, or VIDEO")
    if scheduled_at <= utc_now():
        raise HTTPException(422, "Scheduled time must be in the future")
    astrologer = await database.astrologers.find_one({"_id": astrologer_id, "approval_status": "APPROVED"})
    if not astrologer:
        raise HTTPException(404, "Approved astrologer not found")
    booking_end = scheduled_at + timedelta(minutes=duration_minutes)
    overlap = await database.consultations.find_one({
        "astrologer_id": astrologer_id,
        "status": {"$in": ["PENDING", "ACCEPTED", "IN_PROGRESS"]},
        "scheduled_at": {"$lt": booking_end},
        "$expr": {"$gt": [{"$add": ["$scheduled_at", {"$multiply": ["$duration_minutes", 60000]}]}, scheduled_at]},
    })
    if overlap:
        raise HTTPException(409, "Astrologer has a conflicting booking")
    doc = {"_id": new_id(), "user_id": user_id, "astrologer_id": astrologer_id,
           "consultation_type": kind, "scheduled_at": scheduled_at,
           "duration_minutes": duration_minutes, "status": "PENDING", "payment_status": "UNPAID",
           "created_at": utc_now(), "updated_at": utc_now()}
    await database.consultations.insert_one(doc)
    return doc

async def transition_consultation(consultation_id: str, actor_role: str, actor_id: str,
                                  new_status: str, notes: str | None = None) -> dict:
    consultation = await database.consultations.find_one({"_id": consultation_id})
    if not consultation:
        raise HTTPException(404, "Consultation not found")
    status = new_status.upper()
    if status not in ALLOWED_TRANSITIONS.get(consultation["status"], set()):
        raise HTTPException(409, f"Cannot change consultation from {consultation['status']} to {status}")
    if actor_role == "USER":
        if actor_id != consultation["user_id"] or status != "CANCELLED":
            raise HTTPException(403, "User may only cancel their own booking")
    elif actor_role == "ASTROLOGER":
        assigned = await database.astrologers.find_one({"_id": consultation["astrologer_id"], "user_id": actor_id})
        if not assigned:
            raise HTTPException(403, "Not the assigned astrologer")
    elif actor_role != "ADMIN":
        raise HTTPException(403, "Not allowed")
    changes = {"status": status, "updated_at": utc_now()}
    if notes is not None and actor_role in {"ASTROLOGER", "ADMIN"}:
        changes["astrologer_notes"] = notes
    await database.consultations.update_one({"_id": consultation_id}, {"$set": changes})
    consultation.update(changes)
    return consultation
