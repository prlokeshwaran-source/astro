from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.config.database import database
from app.middleware.auth import require_roles
from app.models import new_id, public_document, utc_now
router=APIRouter(prefix="/reviews",tags=["reviews"])
class ReviewBody(BaseModel):
    consultation_id:str
    rating:int=Field(ge=1,le=5)
    comment:str=Field(default="",max_length=3000)
@router.post("",status_code=201)
async def create(body:ReviewBody,user:dict=Depends(require_roles("USER"))):
    c=await database.consultations.find_one({"_id":body.consultation_id,"user_id":user["_id"],"status":"COMPLETED"})
    if not c: raise HTTPException(400,"A completed consultation is required")
    d={"_id":new_id(),"consultation_id":c["_id"],"user_id":user["_id"],"astrologer_id":c["astrologer_id"],**body.model_dump(),"created_at":utc_now()}
    await database.reviews.insert_one(d); await database.astrologers.update_one({"_id":c["astrologer_id"]},{"$inc":{"rating_total":body.rating,"review_count":1}})
    return public_document(d)
@router.get("/{aid}")
async def list_reviews(aid:str):
    return [public_document(r) async for r in database.reviews.find({"astrologer_id":aid}).sort("created_at",-1).limit(100)]
