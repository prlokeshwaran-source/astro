from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.config.database import database
from app.middleware.auth import current_user, require_roles
from app.models import new_id, public_document, utc_now
router=APIRouter(prefix="/payments",tags=["payments"])
class PaymentBody(BaseModel):
    consultation_id:str
    provider:str=Field(min_length=2,max_length=50)
    provider_reference:str|None=None
@router.post("",status_code=201)
async def create(body:PaymentBody,user:dict=Depends(require_roles("USER"))):
    c=await database.consultations.find_one({"_id":body.consultation_id,"user_id":user["_id"]})
    if not c: raise HTTPException(404,"Consultation not found")
    a=await database.astrologers.find_one({"_id":c["astrologer_id"]})
    d={"_id":new_id(),"consultation_id":c["_id"],"user_id":user["_id"],"amount":a.get("consultation_price",0) if a else 0,"currency":"INR","provider":body.provider,"provider_reference":body.provider_reference,"status":"PENDING","created_at":utc_now()}
    await database.payments.insert_one(d); return public_document(d)
@router.get("/mine")
async def mine(user:dict=Depends(current_user)):
    q={} if user["role"]=="ADMIN" else {"user_id":user["_id"]}
    return [public_document(x) async for x in database.payments.find(q).sort("created_at",-1).limit(200)]
@router.patch("/{pid}/status")
async def status(pid:str,status:str,user:dict=Depends(require_roles("ADMIN"))):
    if status not in {"SUCCEEDED","FAILED","REFUNDED"}: raise HTTPException(400,"Invalid status")
    result=await database.payments.update_one({"_id":pid},{"$set":{"status":status,"updated_at":utc_now()}})
    if not result.matched_count: raise HTTPException(404,"Payment not found")
    p=await database.payments.find_one({"_id":pid})
    if status=="SUCCEEDED": await database.consultations.update_one({"_id":p["consultation_id"]},{"$set":{"payment_status":"PAID"}})
    return public_document(p)
