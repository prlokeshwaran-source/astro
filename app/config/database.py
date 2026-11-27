from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from app.config.settings import settings
from app.models import new_id, utc_now
from app.utils.security import hash_password
client = AsyncMongoClient(settings.mongodb_uri, server_api=ServerApi("1"))
database = client[settings.mongodb_db]
async def connect_database() -> None:
    await client.admin.command("ping")
    await database.users.create_index("email", unique=True)
    await database.refresh_tokens.create_index("token_hash", unique=True)
    await database.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)
    await database.consultations.create_index([("user_id", 1), ("scheduled_at", 1)])
    await database.messages.create_index([("consultation_id", 1), ("created_at", 1)])
    await database.geocode_cache.create_index("query")
    if settings.admin_email and settings.admin_password:
        email = settings.admin_email.lower()
        existing_admin = await database.users.find_one({"email": email})
        if existing_admin is None:
            now = utc_now()
            await database.users.insert_one({
                "_id": new_id(), "name": "Administrator", "email": email,
                "mobile": "0000000000", "password_hash": hash_password(settings.admin_password),
                "role": "ADMIN", "is_active": True, "created_at": now, "updated_at": now,
            })
        elif existing_admin.get("role") != "ADMIN":
            raise RuntimeError(f"Configured admin email {email!r} belongs to a non-admin account")
async def close_database() -> None:
    await client.close()

