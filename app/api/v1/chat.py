import base64
import binascii
import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator, model_validator

from app.config.database import database
from app.middleware.auth import current_user
from app.models import new_id, public_document, utc_now
from app.websocket.chat import manager

router = APIRouter(prefix="/chat", tags=["chat"])
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024
MAX_BASE64_CHARS = 4 * ((MAX_ATTACHMENT_BYTES + 2) // 3)


class MessageAttachment(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=150)
    size_bytes: int = Field(gt=0, le=MAX_ATTACHMENT_BYTES)
    data_base64: str = Field(min_length=4, max_length=MAX_BASE64_CHARS)

    @field_validator("mime_type")
    @classmethod
    def valid_mime_type(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+", value):
            raise ValueError("Invalid attachment content type")
        return value.lower()

    @model_validator(mode="after")
    def validate_attachment(self):
        self.filename = self.filename.replace("\\", "/").split("/")[-1].strip()
        if not self.filename or any(ord(character) < 32 for character in self.filename):
            raise ValueError("Invalid attachment filename")
        try:
            data = base64.b64decode(self.data_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Attachment must contain valid base64 data") from exc
        if len(data) != self.size_bytes or len(data) > MAX_ATTACHMENT_BYTES:
            raise ValueError("Attachment size does not match its base64 data")
        return self


class MessageBody(BaseModel):
    content: str = Field(default="", max_length=10000)
    attachment: MessageAttachment | None = None

    @model_validator(mode="after")
    def require_message_content(self):
        if not self.content.strip() and self.attachment is None:
            raise ValueError("Enter a message or attach a file")
        return self


def public_message(message: dict) -> dict:
    result = public_document(message)
    if result.get("attachment"):
        result["attachment"] = {
            key: value for key, value in result["attachment"].items() if key != "data_base64"
        }
    return result


async def ensure_member(consultation_id: str, user: dict) -> dict:
    consultation = await database.consultations.find_one({"_id": consultation_id})
    if not consultation:
        raise HTTPException(404, "Consultation not found")
    astrologer = await database.astrologers.find_one({"_id": consultation["astrologer_id"]})
    member = (
        user["role"] == "ADMIN"
        or user["_id"] == consultation["user_id"]
        or (astrologer and user["_id"] == astrologer["user_id"])
    )
    if not member:
        raise HTTPException(403, "Not a consultation participant")
    return consultation


@router.post("/{consultation_id}/messages", status_code=201)
async def send(consultation_id: str, body: MessageBody, user: dict = Depends(current_user)):
    consultation = await ensure_member(consultation_id, user)
    message = {
        "_id": new_id(),
        "consultation_id": consultation_id,
        "sender_id": user["_id"],
        "sender_role": user["role"],
        "sender_name": user.get("name", user["role"].title()),
        **body.model_dump(),
        "read_at": None,
        "created_at": utc_now(),
    }
    await database.messages.insert_one(message)
    result = public_message(message)
    broadcast_message = {**result, "created_at": message["created_at"].isoformat()}
    await manager.broadcast(consultation_id, broadcast_message)
    return result


@router.get("/{consultation_id}/messages")
async def history(consultation_id: str, user: dict = Depends(current_user)):
    consultation = await ensure_member(consultation_id, user)
    messages = [message async for message in database.messages.find(
        {"consultation_id": consultation_id}
    ).sort("created_at", 1).limit(500)]
    sender_ids = list({message.get("sender_id") for message in messages if message.get("sender_id")})
    names = {}
    if sender_ids:
        names = {
            profile["_id"]: profile.get("name")
            async for profile in database.users.find({"_id": {"$in": sender_ids}}, {"name": 1})
        }
    astrologer = await database.astrologers.find_one({"_id": consultation["astrologer_id"]})
    result = []
    for message in messages:
        sender_id = message.get("sender_id")
        if sender_id == consultation["user_id"]:
            role = "USER"
        elif astrologer and sender_id == astrologer.get("user_id"):
            role = "ASTROLOGER"
        else:
            role = "ADMIN"
        result.append(public_message({
            **message,
            "sender_role": message.get("sender_role", role),
            "sender_name": message.get("sender_name") or names.get(sender_id) or role.title(),
        }))
    return result


@router.get("/{consultation_id}/messages/{message_id}/attachment")
async def attachment(consultation_id: str, message_id: str, user: dict = Depends(current_user)):
    await ensure_member(consultation_id, user)
    message = await database.messages.find_one({
        "_id": message_id,
        "consultation_id": consultation_id,
    })
    if not message or not message.get("attachment", {}).get("data_base64"):
        raise HTTPException(404, "Attachment not found")
    metadata = message["attachment"]
    try:
        content = base64.b64decode(metadata["data_base64"], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(500, "Stored attachment is invalid") from exc
    filename = metadata["filename"].replace("\r", "").replace("\n", "") or "attachment"
    return Response(
        content=content,
        media_type=metadata.get("mime_type") or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "X-Content-Type-Options": "nosniff",
        },
    )
