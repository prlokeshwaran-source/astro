from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_db: str = "astrology_platform"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    cors_origins: str = "http://localhost:5173,https://astro-frontend-six-mauve.vercel.app"
    openai_api_key: str | None = None
    tts_model: str = "gpt-4o-mini-tts"
    geocoder_user_agent: str = "AstrologyConsultationPlatform/1.0"
    admin_email: str | None = None
    admin_password: str | None = None
    ai_provider: str = "gemini"
    report_ai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    @property
    def allowed_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
settings = Settings()
