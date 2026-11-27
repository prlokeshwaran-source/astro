from fastapi import HTTPException
from app.config.database import database
from app.models import new_id, utc_now

ALLOWED_PAYMENT_STATES = {"PENDING", "SUCCEEDED", "FAILED", "REFUNDED"}

async def create_payment(consultation_id: str, user_id: str, provider: str, provider_reference: str | None = None) -> dict:
    consultation = await database.consultations.find_one({"_id": consultation_id, "user_id": user_id})
    if not consultation: raise HTTPException(404, "Consultation not found")
    if consultation.get("payment_status") == "PAID": raise HTTPException(409, "Consultation has already been paid")
    astro = await database.astrologers.find_one({"_id": consultation["astrologer_id"]})
    payment = {"_id": new_id(), "consultation_id": consultation_id, "user_id": user_id,
               "amount": float((astro or {}).get("consultation_price", 0)), "currency": "INR",
               "provider": provider, "provider_reference": provider_reference,
               "status": "PENDING", "created_at": utc_now()}
    await database.payments.insert_one(payment)
    return payment

async def update_payment_status(payment_id: str, status: str) -> dict:
    status = status.upper()
    if status not in ALLOWED_PAYMENT_STATES - {"PENDING"}: raise HTTPException(422, "Invalid final payment status")
    payment = await database.payments.find_one({"_id": payment_id})
    if not payment: raise HTTPException(404, "Payment not found")
    if payment["status"] != "PENDING": raise HTTPException(409, "Payment is already finalized")
    await database.payments.update_one({"_id": payment_id, "status": "PENDING"}, {"$set": {"status": status, "updated_at": utc_now()}})
    if status == "SUCCEEDED":
        await database.consultations.update_one({"_id": payment["consultation_id"]}, {"$set": {"payment_status": "PAID"}})
    payment.update({"status": status, "updated_at": utc_now()})
    return payment
