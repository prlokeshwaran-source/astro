from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

class AstrologyChartRequest(BaseModel):
    birth_datetime: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    house_system: str = "P"

    @field_validator("birth_datetime")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("birth_datetime must include a timezone")
        return value.astimezone(timezone.utc)

    @field_validator("house_system")
    @classmethod
    def supported_house_system(cls, value: str) -> str:
        if len(value) != 1 or not value.isalpha():
            raise ValueError("house_system must be a one-letter Swiss Ephemeris code")
        return value.upper()
