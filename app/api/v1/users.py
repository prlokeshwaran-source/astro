from fastapi import APIRouter, Depends, HTTPException
from app.config.database import database
from app.middleware.auth import current_user, require_roles
from app.models import public_document, utc_now
from app.schemas.user import LanguagePreferenceUpdate, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def profile(user: dict = Depends(current_user)):
    user.setdefault("preferred_language", "en")
    return public_document(user)

@router.patch("/me")
async def update_profile(body: UserProfileUpdate, user: dict = Depends(current_user)):
    changes = body.model_dump(exclude_unset=True)
    if changes:
        changes["updated_at"] = utc_now()
        await database.users.update_one({"_id": user["_id"]}, {"$set": changes})
        user.update(changes)
    user.setdefault("preferred_language", "en")
    return public_document(user)

@router.put("/me/language")
async def update_language(body: LanguagePreferenceUpdate, user: dict = Depends(current_user)):
    await database.users.update_one({"_id": user["_id"]}, {"$set": {"preferred_language": body.preferred_language, "updated_at": utc_now()}})
    user["preferred_language"] = body.preferred_language
    messages = {"en": "Language preference saved", "ta": "மொழி விருப்பம் சேமிக்கப்பட்டது", "hi": "भाषा की पसंद सहेज दी गई"}
    return {"preferred_language": body.preferred_language, "message": messages[body.preferred_language]}

@router.get("/{user_id}")
async def get_user(user_id: str, actor: dict = Depends(require_roles("ADMIN"))):
    user = await database.users.find_one({"_id": user_id})
    if not user: raise HTTPException(404, "User not found")
    user.setdefault("preferred_language", "en")
    return public_document(user)

