from fastapi import APIRouter, Depends, HTTPException
from app.config.database import database
from app.middleware.auth import require_roles
from app.models import public_document, utc_now
router = APIRouter(prefix="/admin", tags=["admin"])
@router.get("/dashboard")
async def dashboard(admin: dict = Depends(require_roles("ADMIN"))):
    return {"users": await database.users.count_documents({"role":"USER"}), "astrologers": await database.astrologers.count_documents({}), "pending_astrologers": await database.astrologers.count_documents({"approval_status":"PENDING"}), "consultations": await database.consultations.count_documents({}), "completed_consultations": await database.consultations.count_documents({"status":"COMPLETED"}), "open_complaints": await database.complaints.count_documents({"status":"OPEN"})}
@router.get("/astrologers/pending")
async def pending(admin: dict = Depends(require_roles("ADMIN"))):
    return [public_document(a) async for a in database.astrologers.find({"approval_status":"PENDING"}).limit(200)]
@router.patch("/astrologers/{astro_id}/approval")
async def approval(astro_id: str, status: str, admin: dict = Depends(require_roles("ADMIN"))):
    if status not in {"APPROVED", "REJECTED", "SUSPENDED"}: raise HTTPException(400, "Invalid status")
    result = await database.astrologers.update_one({"_id":astro_id}, {"$set":{"approval_status":status,"reviewed_at":utc_now(),"reviewed_by":admin["_id"]}})
    if not result.matched_count: raise HTTPException(404, "Astrologer not found")
    return public_document(await database.astrologers.find_one({"_id":astro_id}))
@router.get("/users")
async def users(admin: dict = Depends(require_roles("ADMIN"))):
    return [public_document(u) async for u in database.users.find({}).sort("created_at",-1).limit(500)]
@router.patch("/users/{user_id}/active")
async def active(user_id: str, enabled: bool, admin: dict = Depends(require_roles("ADMIN"))):
    result = await database.users.update_one({"_id":user_id},{"$set":{"is_active":enabled,"updated_at":utc_now()}})
    if not result.matched_count: raise HTTPException(404,"User not found")
    return public_document(await database.users.find_one({"_id":user_id}))
