from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError
from app.config.database import database
from app.config.settings import settings
from app.middleware.auth import current_user
from app.models import public_document, utc_now, new_id
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.services.auth_service import login, register, token_pair
from app.utils.security import decode_token, hash_token
router = APIRouter(prefix="/auth", tags=["authentication"])
@router.post("/register", status_code=201)
async def register_user(body: RegisterRequest):
    user = await register(body.model_dump(mode="json"))
    return {"user": public_document(user), "message": "Registration successful"}
@router.post("/login")
async def login_user(body: LoginRequest):
    return await login(body.email, body.password)
@router.post("/refresh")
async def refresh(body: RefreshRequest):
    try:
        claims = decode_token(body.refresh_token)
        if claims.get("type") != "refresh": raise HTTPException(401, "Invalid refresh token")
    except JWTError: raise HTTPException(401, "Invalid refresh token")
    saved = await database.refresh_tokens.find_one({"token_hash": hash_token(body.refresh_token), "user_id": claims.get("sub"), "expires_at": {"$gt": utc_now()}})
    user = await database.users.find_one({"_id": claims.get("sub"), "is_active": True})
    if not saved or not user: raise HTTPException(401, "Refresh token expired or revoked")
    await database.refresh_tokens.delete_one({"_id": saved["_id"]})
    pair = token_pair(user)
    await database.refresh_tokens.insert_one({"_id": new_id(), "user_id": user["_id"], "token_hash": hash_token(pair["refresh_token"]), "expires_at": utc_now() + timedelta(days=settings.refresh_token_days), "created_at": utc_now()})
    return pair
@router.post("/logout")
async def logout(body: RefreshRequest, user: dict = Depends(current_user)):
    await database.refresh_tokens.delete_one({"token_hash": hash_token(body.refresh_token), "user_id": user["_id"]})
    return {"message": "Logged out"}
@router.get("/me")
async def me(user: dict = Depends(current_user)):
    return public_document(user)
