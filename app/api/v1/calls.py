from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.config.database import database
from app.middleware.auth import current_user
from app.models import new_id, public_document, utc_now
router=APIRouter(prefix="/calls",tags=["calls"])
class CallBody(BaseModel): consultation_id:str
@router.post("/start",status_code=201)
async def start(body:CallBody,user:dict=Depends(current_user)):
    c=await database.consultations.find_one({"_id":body.consultation_id})
    if not c: raise HTTPException(404,"Consultation not found")
    a=await database.astrologers.find_one({"_id":c["astrologer_id"]})
    if user["role"]!="ADMIN" and user["_id"]!=c["user_id"] and (not a or user["_id"]!=a["user_id"]): raise HTTPException(403,"Not a participant")
    d={"_id":new_id(),"consultation_id":c["_id"],"participants":[c["user_id"],a["user_id"] if a else None],"started_at":utc_now(),"ended_at":None}
    await database.calls.insert_one(d); return public_document(d)
@router.post("/{call_id}/end")
async def end(call_id:str,user:dict=Depends(current_user)):
    d=await database.calls.find_one({"_id":call_id})
    if not d: raise HTTPException(404,"Call not found")
    if user["role"]!="ADMIN" and user["_id"] not in d["participants"]: raise HTTPException(403,"Not a participant")
    end_time=utc_now(); duration=max(0,int((end_time-d["started_at"]).total_seconds()))
    await database.calls.update_one({"_id":call_id},{"$set":{"ended_at":end_time,"duration_seconds":duration}})
    return public_document(await database.calls.find_one({"_id":call_id}))
