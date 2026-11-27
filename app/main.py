from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config.database import close_database, connect_database
from app.config.settings import settings
from app.middleware.error_handler import register_error_handlers
from app.websocket.chat import router as websocket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_database()
    try:
        yield
    finally:
        await close_database()

app = FastAPI(title="Astrology Consultation API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    # Vercel gives preview deployments a distinct hostname. Keep those
    # previews scoped to this frontend's project slug.
    allow_origin_regex=r"https://astro-frontend-six-mauve(?:-[a-z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router)

@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
