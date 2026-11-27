from pydantic import BaseModel, Field
class AstrologerRegistration(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    experience: int = Field(ge=0, le=80)
    specialization: list[str] = Field(min_length=1)
    languages: list[str] = Field(min_length=1)
    consultation_price: float = Field(gt=0)
    bio: str = Field(min_length=20, max_length=5000)
class AstrologerProfileUpdate(BaseModel):
    experience: int | None = Field(default=None, ge=0, le=80)
    specialization: list[str] | None = None
    languages: list[str] | None = None
    consultation_price: float | None = Field(default=None, gt=0)
    bio: str | None = Field(default=None, max_length=5000)
    profile_photo: str | None = None
    availability: dict | None = None
