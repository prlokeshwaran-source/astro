from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.config.database import database
from app.middleware.auth import current_user, require_roles
from app.models import new_id, public_document, utc_now
router=APIRouter(prefix="/complaints",tags=["complaints"])
class ComplaintBody(BaseModel):
    subject:str=Field(min_length=3,max_length=200)
    description:str=Field(min_length=10,max_length=5000)
@router.post("",status_code=201)
async def create(body:ComplaintBody,user:dict=Depends(current_user)):
    d={"_id":new_id(),"reporter_id":user["_id"],"reporter_name":user.get("name",""),"role":user["role"],**body.model_dump(),"status":"OPEN","created_at":utc_now(),"updated_at":utc_now()}
    await database.complaints.insert_one(d); return public_document(d)
@router.get("")
async def listing(user:dict=Depends(current_user)):
    q={} if user["role"]=="ADMIN" else {"reporter_id":user["_id"]}
    return [public_document(x) async for x in database.complaints.find(q).sort("created_at",-1).limit(200)]
@router.patch("/{cid}")
async def update(cid:str,status:str,notes:str="",user:dict=Depends(require_roles("ADMIN"))):
    if status not in {"INVESTIGATING","RESOLVED","REJECTED"}: raise HTTPException(400,"Invalid status")
    result=await database.complaints.update_one({"_id":cid},{"$set":{"status":status,"resolution_notes":notes,"updated_at":utc_now()}})
    if not result.matched_count: raise HTTPException(404,"Complaint not found")
    return public_document(await database.complaints.find_one({"_id":cid}))
