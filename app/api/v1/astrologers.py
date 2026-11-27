from fastapi import APIRouter, Depends, HTTPException, Query
from app.config.database import database
from app.middleware.auth import require_roles
from app.models import new_id, public_document, utc_now
from app.schemas.astrologer import AstrologerProfileUpdate, AstrologerRegistration
router = APIRouter(prefix="/astrologers", tags=["astrologers"])
@router.post("/apply", status_code=201)
async def apply(body: AstrologerRegistration, user: dict = Depends(require_roles("USER"))):
    data = body.model_dump()
    data.update({"user_id": user["_id"], "approval_status": "PENDING", "is_online": False, "rating": 0, "review_count": 0, "created_at": utc_now()})
    await database.astrologers.insert_one({"_id": new_id(), **data})
    await database.users.update_one({"_id": user["_id"]}, {"$set": {"role": "ASTROLOGER"}})
    return {"message": "Application submitted for admin approval"}
@router.get("")
async def search(specialization: str | None = None, language: str | None = None, min_experience: int | None = Query(default=None, ge=0), page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100)):
    query = {"approval_status": "APPROVED"}
    if specialization: query["specialization"] = specialization
    if language: query["languages"] = language
    if min_experience is not None: query["experience"] = {"$gte": min_experience}
    total = await database.astrologers.count_documents(query)
    cur = database.astrologers.find(query).skip((page-1)*page_size).limit(page_size)
    return {"items": [public_document(x) async for x in cur], "total": total, "page": page, "page_size": page_size}
@router.get("/me")
async def my_profile(user: dict = Depends(require_roles("ASTROLOGER"))):
    profile = await database.astrologers.find_one({"user_id": user["_id"]})
    if not profile: raise HTTPException(404, "Profile not found")
    return public_document(profile)
@router.patch("/me")
async def update_profile(body: AstrologerProfileUpdate, user: dict = Depends(require_roles("ASTROLOGER"))):
    changes = body.model_dump(exclude_unset=True)
    changes["updated_at"] = utc_now()
    await database.astrologers.update_one({"user_id": user["_id"]}, {"$set": changes})
    return public_document(await database.astrologers.find_one({"user_id": user["_id"]}))
