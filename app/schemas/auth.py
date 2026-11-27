from pydantic import BaseModel, EmailStr, Field
from app.utils.i18n import LanguageCode

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(min_length=6, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: str = "USER"
    preferred_language: LanguageCode = "en"
    date_of_birth: str | None = None
    time_of_birth: str | None = None
    place_of_birth: str | None = None
    gender: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str
