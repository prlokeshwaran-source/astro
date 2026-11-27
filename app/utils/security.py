from datetime import datetime, timedelta, timezone
import hashlib
from jose import jwt
from pwdlib import PasswordHash
from app.config.settings import settings
password_hasher = PasswordHash.recommended()
def hash_password(password: str) -> str:
    return password_hasher.hash(password)
def verify_password(password: str, hashed: str) -> bool:
    return password_hasher.verify(password, hashed)
def create_token(subject: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": subject, "role": role, "type": token_type, "iat": now, "exp": now + expires_delta}
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
