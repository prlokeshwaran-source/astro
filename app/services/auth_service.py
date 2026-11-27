from datetime import timedelta
from fastapi import HTTPException
from app.config.database import database
from app.config.settings import settings
from app.models import new_id, utc_now
from app.utils.security import create_token, hash_password, hash_token, verify_password
def token_pair(user: dict) -> dict:
    access = create_token(user["_id"], user["role"], "access", timedelta(minutes=settings.access_token_minutes))
    refresh = create_token(user["_id"], user["role"], "refresh", timedelta(days=settings.refresh_token_days))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
async def register(data: dict) -> dict:
    email = data["email"].lower()
    if await database.users.find_one({"email": email}): raise HTTPException(409, "Email is already registered")
    role = data.pop("role", "USER").upper()
    if role not in {"USER", "ASTROLOGER"}: raise HTTPException(400, "Unsupported registration role")
    now = utc_now()
    user = {"_id": new_id(), "name": data.pop("name"), "email": email, "mobile": data.pop("mobile"),
            "password_hash": hash_password(data.pop("password")), "role": role, "is_active": True,
            "created_at": now, "updated_at": now, **data}
    if role == "ASTROLOGER": user["approval_status"] = "PENDING"
    await database.users.insert_one(user)
    return user
async def login(email: str, password: str) -> dict:
    user = await database.users.find_one({"email": email.lower()})
    if not user or not verify_password(password, user["password_hash"]): raise HTTPException(401, "Incorrect email or password")
    if not user.get("is_active", True): raise HTTPException(403, "Account is disabled")
    pair = token_pair(user)
    await database.refresh_tokens.insert_one({"_id": new_id(), "user_id": user["_id"], "token_hash": hash_token(pair["refresh_token"]), "expires_at": utc_now() + timedelta(days=settings.refresh_token_days), "created_at": utc_now()})
    return pair
