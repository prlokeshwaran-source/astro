from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from app.config.database import database
from app.models import new_id, utc_now
from app.utils.security import decode_token

router = APIRouter()
class ConnectionManager:
    def __init__(self): self.rooms: dict[str, set[WebSocket]] = defaultdict(set)
    async def connect(self, room: str, socket: WebSocket):
        await socket.accept(); self.rooms[room].add(socket)
    def disconnect(self, room: str, socket: WebSocket):
        self.rooms[room].discard(socket)
        if not self.rooms[room]: self.rooms.pop(room, None)
    async def broadcast(self, room: str, payload: dict):
        stale = []
        for socket in self.rooms.get(room, set()):
            try: await socket.send_json(payload)
            except Exception: stale.append(socket)
        for socket in stale: self.disconnect(room, socket)
manager = ConnectionManager()

@router.websocket("/ws/chat/{consultation_id}")
async def chat_socket(ws: WebSocket, consultation_id: str, token: str):
    try:
        claims = decode_token(token)
        if claims.get("type") != "access": raise ValueError("Not access token")
        user = await database.users.find_one({"_id": claims.get("sub"), "is_active": True})
        consultation = await database.consultations.find_one({"_id": consultation_id})
        astrologer = await database.astrologers.find_one({"_id": consultation["astrologer_id"]}) if consultation else None
        member = consultation and user and (user["role"] == "ADMIN" or user["_id"] == consultation["user_id"] or (astrologer and user["_id"] == astrologer["user_id"]))
        if not member: raise ValueError("Not a consultation participant")
    except (JWTError, ValueError, TypeError):
        await ws.close(code=1008); return
    await manager.connect(consultation_id, ws)
    try:
        while True:
            content = (await ws.receive_text())[:10000]
            message = {"_id": new_id(), "consultation_id": consultation_id, "sender_id": user["_id"],
                       "sender_role": user["role"], "sender_name": user.get("name", user["role"].title()),
                       "content": content, "read_at": None, "created_at": utc_now()}
            await database.messages.insert_one(message)
            await manager.broadcast(consultation_id, {"id": message["_id"], "sender_id": user["_id"],
                "sender_role": user["role"], "sender_name": user.get("name", user["role"].title()),
                "content": content, "created_at": message["created_at"].isoformat()})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(consultation_id, ws)
