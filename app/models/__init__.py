"""Shared MongoDB document helpers and timestamps."""
from datetime import datetime, timezone
from bson import ObjectId

def new_id() -> str:
    return str(ObjectId())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def public_document(document: dict | None) -> dict | None:
    if document is None: return None
    result = dict(document)
    result["id"] = str(result.pop("_id"))
    result.pop("password_hash", None)
    return result
