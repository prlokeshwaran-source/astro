from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.config.database import database
from app.middleware.auth import current_user
from app.models import new_id, public_document, utc_now
from app.schemas.astrology import AstrologyChartRequest
from app.services.astrology_service import generate_chart
from app.services.report_service import generate_astrology_prediction, render_report_pdf
from app.utils.i18n import LanguageCode, validate_language

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportBody(BaseModel):
    consultation_id: str
    title: str = Field(min_length=2, max_length=200)
    content: dict
    pdf_url: str | None = None


class GenerateReportBody(BaseModel):
    consultation_id: str
    birth_datetime: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    topic: str = Field(min_length=3, max_length=200)
    astrologer_notes: str | None = Field(default=None, max_length=4000)
    language: LanguageCode | None = None


def _report_document(report: dict) -> dict:
    result = public_document(report)
    result.pop("pdf_data", None)
    return result


@router.post("", status_code=201)
async def create(body: ReportBody, user: dict = Depends(current_user)):
    consultation = await database.consultations.find_one({"_id": body.consultation_id})
    if not consultation:
        raise HTTPException(404, "Consultation not found")
    astrologer = await database.astrologers.find_one({"_id": consultation["astrologer_id"]})
    assigned = user["role"] == "ADMIN" or (
        user["role"] == "ASTROLOGER" and astrologer and astrologer["user_id"] == user["_id"]
    )
    if not assigned:
        raise HTTPException(403, "Only the assigned astrologer can create reports")
    report = {
        "_id": new_id(), "consultation_id": consultation["_id"],
        "user_id": consultation["user_id"], "astrologer_id": consultation["astrologer_id"],
        **body.model_dump(), "created_at": utc_now(),
    }
    await database.reports.insert_one(report)
    return _report_document(report)


@router.post("/generate", status_code=201)
async def generate(body: GenerateReportBody, user: dict = Depends(current_user)):
    if user["role"] != "ASTROLOGER":
        raise HTTPException(403, "Only astrologers can generate consultation reports")
    consultation = await database.consultations.find_one({
        "_id": body.consultation_id, "status": "COMPLETED",
    })
    if not consultation:
        raise HTTPException(404, "Completed consultation not found")
    astrologer = await database.astrologers.find_one({
        "_id": consultation["astrologer_id"], "user_id": user["_id"],
    })
    if not astrologer:
        raise HTTPException(403, "Only the assigned astrologer can generate this report")
    chart_request = AstrologyChartRequest(
        birth_datetime=body.birth_datetime,
        latitude=body.latitude,
        longitude=body.longitude,
    )
    language = validate_language(body.language or user.get("preferred_language", "en"))
    chart = await generate_chart(chart_request, language)
    prediction = await generate_astrology_prediction(chart, body.topic, body.astrologer_notes, language)
    report_id = new_id()
    title = {
        "en": f"Astrology consultation report: {body.topic}",
        "ta": f"ஜோதிட ஆலோசனை அறிக்கை: {body.topic}",
        "hi": f"ज्योतिष परामर्श रिपोर्ट: {body.topic}",
    }[language][:200]
    client = await database.users.find_one({"_id": consultation["user_id"]})
    planet_lines = "; ".join(
        f"{planet.get('name_display', planet['name'])}: {planet.get('rasi_display', planet['rasi'])}"
        for planet in chart.get("planets", [])
    )
    if language == "ta":
        dasha_lines = [
            f"{major.get('lord_display', major['lord'])} மகாதசை / {subperiod.get('lord_display', subperiod['lord'])} புத்தி: "
            f"{subperiod['start_at'][:10]} முதல் {subperiod['end_at'][:10]} ({subperiod['years']:.2f} ஆண்டுகள்)"
            for major in chart.get("dasha", {}).get("mahadashas", []) for subperiod in major.get("bhuktis", [])
        ]
    elif language == "hi":
        dasha_lines = [
            f"{major.get('lord_display', major['lord'])} महादशा / {subperiod.get('lord_display', subperiod['lord'])} भुक्ति: "
            f"{subperiod['start_at'][:10]} से {subperiod['end_at'][:10]} ({subperiod['years']:.2f} वर्ष)"
            for major in chart.get("dasha", {}).get("mahadashas", []) for subperiod in major.get("bhuktis", [])
        ]
    else:
        dasha_lines = [
            f"{major.get('lord_display', major['lord'])} Mahadasha / "
            f"{subperiod.get('lord_display', subperiod['lord'])} Bhukti: "
            f"{subperiod['start_at'][:10]} to {subperiod['end_at'][:10]} ({subperiod['years']:.2f} years)"
            for major in chart.get("dasha", {}).get("mahadashas", []) for subperiod in major.get("bhuktis", [])
        ]
    chart_summary_labels = {
        "en": ("Lagna", "Moon sign", "Nakshatra"),
        "ta": ("லக்னம்", "சந்திர ராசி", "நட்சத்திரம்"),
        "hi": ("लग्न", "चंद्र राशि", "नक्षत्र"),
    }[language]
    labels = {
        "en": ["Client", "Topic", "Birth chart", "Planet placements", "Vimshottari Dasha and Bhukti timeline (365.25-day year)", "AI astrology prediction", "Astrologer notes", "Review note"],
        "ta": ["வாடிக்கையாளர்", "தலைப்பு", "ஜாதகக் கட்டம்", "கிரக நிலைகள்", "விம்சோத்தரி தசை மற்றும் புத்தி கால அட்டவணை", "AI ஜோதிட கணிப்பு", "ஜோதிடர் குறிப்புகள்", "மதிப்பாய்வு குறிப்பு"],
        "hi": ["ग्राहक", "विषय", "जन्म कुंडली", "ग्रह स्थिति", "विंशोत्तरी महादशा और भुक्ति समयरेखा", "AI ज्योतिषीय भविष्यवाणी", "ज्योतिषी के नोट्स", "समीक्षा टिप्पणी"],
    }[language]
    pdf_data = render_report_pdf(title, {
        labels[0]: (client or {}).get("name", "Client"),
        labels[1]: body.topic,
        labels[2]: (
            f"{chart_summary_labels[0]}: {chart.get('lagna_display', chart.get('lagna'))}; "
            f"{chart_summary_labels[1]}: {chart.get('rasi_display', chart.get('rasi'))}; "
            f"{chart_summary_labels[2]}: {chart.get('nakshatra_display', chart.get('nakshatra'))}"
        ),
        labels[3]: planet_lines,
        labels[4]: "\n".join(dasha_lines),
        labels[5]: prediction,
        labels[6]: body.astrologer_notes or {"en": "None supplied", "ta": "வழங்கப்படவில்லை", "hi": "नहीं दिए गए"}[language],
        labels[7]: {"en": "AI-assisted draft prepared for review by the assigned astrologer.", "ta": "ஜோதிடரின் மதிப்பாய்வுக்காக AI உதவியுடன் தயாரிக்கப்பட்ட வரைவு.", "hi": "ज्योतिषी की समीक्षा के लिए AI की सहायता से तैयार मसौदा।"}[language],
    }, language)
    report = {
        "_id": report_id,
        "consultation_id": consultation["_id"],
        "user_id": consultation["user_id"],
        "astrologer_id": consultation["astrologer_id"],
        "title": title,
        "topic": body.topic,
        "content": {"summary": prediction, "chart": chart, "astrologer_notes": body.astrologer_notes},
        "pdf_url": f"/api/v1/reports/{report_id}/pdf",
        "pdf_data": pdf_data,
        "status": "DRAFT",
        "language": language,
        "created_at": utc_now(),
    }
    await database.reports.insert_one(report)
    return _report_document(report)


@router.get("")
async def listing(user: dict = Depends(current_user)):
    if user["role"] == "ADMIN":
        query = {}
    elif user["role"] == "USER":
        query = {
            "user_id": user["_id"],
            "$or": [{"status": "SHARED"}, {"status": {"$exists": False}}],
        }
    else:
        profile = await database.astrologers.find_one({"user_id": user["_id"]})
        query = {"astrologer_id": profile["_id"] if profile else ""}
    return [
        _report_document(report)
        async for report in database.reports.find(query).sort("created_at", -1).limit(100)
    ]


@router.post("/{report_id}/share")
async def share_report(report_id: str, user: dict = Depends(current_user)):
    report = await database.reports.find_one({"_id": report_id})
    if not report:
        raise HTTPException(404, "Report not found")
    if user["role"] == "ASTROLOGER":
        profile = await database.astrologers.find_one({"user_id": user["_id"]})
        allowed = bool(profile and report.get("astrologer_id") == profile["_id"])
    else:
        allowed = user["role"] == "ADMIN"
    if not allowed:
        raise HTTPException(403, "Only the assigned astrologer can share this report")
    await database.reports.update_one(
        {"_id": report_id}, {"$set": {"status": "SHARED", "shared_at": utc_now()}}
    )
    return _report_document(await database.reports.find_one({"_id": report_id}))


@router.get("/{report_id}/pdf")
async def download_pdf(report_id: str, user: dict = Depends(current_user)):
    report = await database.reports.find_one({"_id": report_id})
    if not report:
        raise HTTPException(404, "Report not found")
    if user["role"] == "USER":
        allowed = report.get("user_id") == user["_id"] and report.get("status") in {None, "SHARED"}
    elif user["role"] == "ASTROLOGER":
        profile = await database.astrologers.find_one({"user_id": user["_id"]})
        allowed = bool(profile and report.get("astrologer_id") == profile["_id"])
    else:
        allowed = user["role"] == "ADMIN"
    if not allowed:
        raise HTTPException(403, "You cannot access this report")
    pdf_data = report.get("pdf_data")
    if not pdf_data:
        raise HTTPException(404, "PDF is not available for this report")
    return Response(
        content=bytes(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="astrology-report-{report_id}.pdf"'},
    )
