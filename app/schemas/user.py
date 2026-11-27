from pydantic import BaseModel, Field
from app.utils.i18n import LanguageCode

class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    mobile: str | None = Field(default=None, min_length=6, max_length=20)
    profile_photo: str | None = None
    date_of_birth: str | None = None
    time_of_birth: str | None = None
    place_of_birth: str | None = None
    gender: str | None = None
    preferred_language: LanguageCode = "en"

class LanguagePreferenceUpdate(BaseModel):
    preferred_language: LanguageCode
