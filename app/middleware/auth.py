from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from app.config.database import database
from app.utils.security import decode_token
bearer = HTTPBearer(auto_error=False)
async def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    denied = HTTPException(401, "Invalid or missing access token", headers={"WWW-Authenticate": "Bearer"})
    if not credentials: raise denied
    try:
        claims = decode_token(credentials.credentials)
        if claims.get("type") != "access": raise denied
        user = await database.users.find_one({"_id": claims["sub"], "is_active": True})
        if not user or user.get("role") != claims.get("role"): raise denied
        return user
    except (JWTError, KeyError, TypeError):
        raise denied
def require_roles(*roles: str):
    async def check_role(user: dict = Depends(current_user)) -> dict:
        if user.get("role") not in roles: raise HTTPException(403, "Insufficient permissions")
        return user
    return check_role
