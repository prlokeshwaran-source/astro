from io import BytesIO
import httpx
import logging
import asyncio
import ssl
from textwrap import wrap
from pathlib import Path
from fastapi import HTTPException
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from app.config.database import database
from app.config.settings import settings
from app.models import new_id, utc_now
import json

logger = logging.getLogger(__name__)

async def create_report(consultation_id: str, title: str, content: dict, pdf_url: str | None, actor_id: str, actor_role: str) -> dict:
    consultation = await database.consultations.find_one({"_id": consultation_id})
    if not consultation: raise HTTPException(404, "Consultation not found")
    astrologer = await database.astrologers.find_one({"_id": consultation["astrologer_id"]})
    assigned = actor_role == "ADMIN" or (actor_role == "ASTROLOGER" and astrologer and astrologer["user_id"] == actor_id)
    if not assigned: raise HTTPException(403, "Only the assigned astrologer can create a report")
    report = {"_id": new_id(), "consultation_id": consultation_id, "user_id": consultation["user_id"],
              "astrologer_id": consultation["astrologer_id"], "title": title, "content": content,
              "pdf_url": pdf_url, "created_at": utc_now()}
    await database.reports.insert_one(report)
    return report

def render_report_pdf(title: str, sections: dict, language: str = "en") -> bytes:
    """Render a branded, Unicode report PDF in the selected language."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font_name, bold_name = _pdf_fonts(language)
    page_number = 1
    left = 48
    content_width = width - (left * 2)
    y = height - 86

    def draw_brand():
        pdf.saveState()
        pdf.setFillColor(HexColor("#431407"))
        pdf.rect(0, height - 132, width, 132, fill=1, stroke=0)
        pdf.setStrokeColor(HexColor("#F4C542"))
        pdf.setLineWidth(1.5)
        pdf.circle(left + 13, height - 39, 12, stroke=1, fill=0)
        pdf.setStrokeColor(HexColor("#F97316"))
        pdf.ellipse(left + 1, height - 44, left + 25, height - 34, stroke=1, fill=0)
        pdf.setFillColor(HexColor("#F97316"))
        pdf.setStrokeColor(HexColor("#9A3412"))
        pdf.setLineWidth(0.7)
        points = [(left + 13, height - 29), (left + 16, height - 37), (left + 24, height - 39),
                  (left + 16, height - 42), (left + 13, height - 50), (left + 10, height - 42),
                  (left + 2, height - 39), (left + 10, height - 37)]
        path = pdf.beginPath()
        path.moveTo(*points[0])
        for point in points[1:]:
            path.lineTo(*point)
        path.close()
        pdf.drawPath(path, stroke=1, fill=1)
        pdf.setFillColor(HexColor("#FFF7ED"))
        pdf.setFont(bold_name, 12)
        pdf.drawString(left + 34, height - 43, "Astra", shaping=font_name != "Helvetica")
        pdf.restoreState()

    def draw_footer():
        pdf.saveState()
        pdf.setStrokeColor(HexColor("#FED7AA"))
        pdf.line(left, 38, width - left, 38)
        pdf.setFillColor(HexColor("#9A3412"))
        pdf.setFont(font_name, 8)
        pdf.drawString(left, 25, _pdf_text({"en": "Astra - Astrology consultation", "ta": "அஸ்ட்ரா - ஜோதிட ஆலோசனை", "hi": "अस्त्र - ज्योतिष परामर्श"}.get(language, "Astra - Astrology consultation"), font_name), shaping=font_name != "Helvetica")
        pdf.drawRightString(width - left, 25, str(page_number))
        pdf.restoreState()

    draw_brand()
    pdf.setTitle(title[:200])
    pdf.setAuthor("Astra")
    pdf.setFillColor(HexColor("#F4C542"))
    pdf.setFont(bold_name, 8)
    pdf.drawString(left, height - 69, "ASTRA  ·  PERSONAL INSIGHT")
    pdf.setFillColor(HexColor("#FFF7ED"))
    pdf.setFont(bold_name, 18)
    title_lines = wrap(title, width=66)[:2] or [title]
    for title_line in title_lines:
        pdf.drawString(left, y, _pdf_text(title_line, bold_name), shaping=bold_name != "Helvetica-Bold")
        y -= 22
    y = height - 146
    pdf.setStrokeColor(HexColor("#F97316"))
    pdf.setLineWidth(2)
    pdf.line(left, y, left + 54, y)
    y -= 26

    for heading, value in sections.items():
        heading_lines = wrap(str(heading), width=92) or [str(heading)]
        required_space = 30 + len(heading_lines) * 12
        if y < required_space + 48:
            draw_footer()
            pdf.showPage()
            page_number += 1
            y = height - 158
            draw_brand()
        heading_height = max(22, len(heading_lines) * 12 + 10)
        pdf.setFillColor(HexColor("#FFF7ED"))
        pdf.roundRect(left, y - heading_height + 3, content_width, heading_height, 5, fill=1, stroke=0)
        pdf.setFillColor(HexColor("#9A3412"))
        pdf.setFont(bold_name, 10)
        for heading_line in heading_lines:
            pdf.drawString(left + 9, y - 4, _pdf_text(heading_line, bold_name), shaping=bold_name != "Helvetica-Bold")
            y -= 12
        y -= 8
        pdf.setFillColor(HexColor("#431407"))
        pdf.setFont(font_name, 9.5)
        for paragraph in str(value).splitlines() or [""]:
            lines = wrap(paragraph, width=100) or [""]
            for line in lines:
                if y < 56:
                    draw_footer()
                    pdf.showPage()
                    page_number += 1
                    y = height - 158
                    draw_brand()
                    pdf.setFillColor(HexColor("#431407"))
                    pdf.setFont(font_name, 9.5)
                if font_name != "Helvetica":
                    pdf.drawString(left + 6, y, _pdf_text(line, font_name), shaping=True)
                else:
                    pdf.drawString(left + 6, y, _pdf_text(line, font_name)[:180])
                y -= 14
        y -= 9
    draw_footer()
    pdf.save()
    return buffer.getvalue()

_REGISTERED_UNICODE_FONTS: set[str] = set()

def _pdf_fonts(language: str) -> tuple[str, str]:
    candidates = []
    if language == "ta":
        candidates.extend([r"C:\Windows\Fonts\Nirmala.ttf", "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf"])
    elif language == "hi":
        candidates.extend([r"C:\Windows\Fonts\Nirmala.ttf", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"])
    candidates.extend(["/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for path in candidates:
        if not Path(path).is_file():
            continue
        name = f"AstroUnicode_{abs(hash(path))}"
        bold_path = str(Path(path).with_name(Path(path).stem + "-Bold" + Path(path).suffix))
        bold_name = f"{name}_Bold"
        try:
            if name not in _REGISTERED_UNICODE_FONTS:
                pdfmetrics.registerFont(TTFont(name, path, shapable=True))
                if Path(bold_path).is_file():
                    pdfmetrics.registerFont(TTFont(bold_name, bold_path, shapable=True))
                else:
                    bold_name = name
                _REGISTERED_UNICODE_FONTS.add(name)
            return name, bold_name
        except Exception:
            logger.debug("Could not register PDF font %s", path, exc_info=True)
    return "Helvetica", "Helvetica-Bold"

def _pdf_text(value: str, font_name: str) -> str:
    if font_name == "Helvetica":
        return value.encode("latin-1", "replace").decode("latin-1")
    return value

async def generate_astrology_prediction(chart: dict, topic: str, astrologer_notes: str | None = None, language: str = "en") -> str:
    dasha = chart.get("dasha") or {}
    current_bhukti = next(
        (
            {"mahadasha": major.get("lord"), "bhukti": subperiod.get("lord")}
            for major in dasha.get("mahadashas", [])
            for subperiod in major.get("bhuktis", [])
            if subperiod.get("is_current")
        ),
        None,
    )
    chart_data = {
        "lagna": chart.get("lagna"),
        "moon_sign": chart.get("rasi"),
        "nakshatra": chart.get("nakshatra"),
        "planets": [
            {key: planet.get(key) for key in ("name", "rasi", "longitude", "navamsa")}
            for planet in chart.get("planets", [])
        ],
        "navamsa_lagna": (chart.get("navamsa_chart") or {}).get("lagna"),
        "birth_mahadasha": (chart.get("dasha") or {}).get("birth_mahadasha"),
        "dasha_balance_years": (chart.get("dasha") or {}).get("balance_years_at_birth"),
        "current_dasha_bhukti": current_bhukti,
    }
    report_language = {"en": "English", "ta": "Tamil", "hi": "Hindi"}.get(language, "English")
    prompt = (
        "Write a client-friendly Vedic astrology consultation report based only on the chart data below. "
        "Treat astrology as a traditional interpretive practice, not a certainty. Avoid medical, legal, or guaranteed financial predictions. "
        "Give a concise overview and practical, non-deterministic guidance relevant to the requested topic. "
        f"Write the entire report in {report_language}, including headings. "
        "Return plain text with five clearly labeled sections for overview, chart factors, guidance, timing, and reflection. "
        "Do not invent placements or dates.\n\n"
        f"Requested topic: {topic}\n"
        f"Chart data: {json.dumps(chart_data, ensure_ascii=True)}\n"
        f"Astrologer notes: {(astrologer_notes or 'None supplied')[:4000]}"
    )
    provider = settings.ai_provider.strip().lower()
    if provider == "gemini":
        return await _generate_with_gemini(prompt)
    if provider != "openai":
        raise HTTPException(503, "Unsupported AI_PROVIDER. Choose gemini or openai.")
    if not settings.openai_api_key:
        raise HTTPException(503, "OpenAI reports are not configured. Set OPENAI_API_KEY in the backend .env.")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.responses.create(
            model=settings.report_ai_model,
            instructions="You assist a practicing astrologer by drafting a careful, readable interpretation for their review.",
            input=prompt,
        )
        prediction = response.output_text.strip()
        if not prediction:
            raise HTTPException(502, "AI report generation returned no content.")
        return prediction[:16000]
    except HTTPException:
        raise
    except AuthenticationError as exc:
        logger.warning("OpenAI rejected the report API key (authentication failure)")
        raise HTTPException(502, "OpenAI rejected the API key. Check OPENAI_API_KEY in the backend .env.") from exc
    except PermissionDeniedError as exc:
        logger.warning("OpenAI denied report generation for the configured key or model")
        raise HTTPException(502, "OpenAI denied access. Check the API project permissions and REPORT_AI_MODEL.") from exc
    except NotFoundError as exc:
        logger.warning("Configured report model was not found or is unavailable")
        raise HTTPException(502, "The configured AI report model is unavailable. Check REPORT_AI_MODEL in .env.") from exc
    except RateLimitError as exc:
        logger.warning("OpenAI report generation was rate limited or the project has no quota")
        raise HTTPException(502, "OpenAI rate limit or quota reached. Check the API project billing and limits.") from exc
    except APIConnectionError as exc:
        logger.warning("Could not connect to OpenAI while generating a report")
        raise HTTPException(502, "Could not connect to OpenAI. Check the backend network connection.") from exc
    except APIStatusError as exc:
        logger.error("OpenAI report generation returned HTTP %s", exc.status_code)
        raise HTTPException(502, f"OpenAI report request failed (HTTP {exc.status_code}). Check backend logs.") from exc
    except Exception as exc:
        logger.exception("Unexpected error during AI report generation")
        raise HTTPException(502, "Unexpected AI report error. Check the backend terminal for details.") from exc
    finally:
        await client.close()

async def _generate_with_gemini(prompt: str) -> str:
    if not settings.gemini_api_key:
        raise HTTPException(503, "Gemini reports are not configured. Set GEMINI_API_KEY in the backend .env.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{
            "text": "You assist a practicing astrologer by drafting a careful, readable interpretation for their review."
        }]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 900},
    }
    try:
        timeout = httpx.Timeout(35, connect=8)
        async with httpx.AsyncClient(timeout=timeout, verify=ssl.create_default_context()) as client:
            response = None
            for attempt in range(2):
                response = await client.post(
                    url, headers={"x-goog-api-key": settings.gemini_api_key}, json=payload
                )
                if response.status_code != 503 or attempt == 1:
                    break
                await asyncio.sleep(0.75)
        if response.is_error:
            logger.warning("Gemini report generation returned HTTP %s", response.status_code)
            if response.status_code in {401, 403}:
                detail = "Gemini rejected the key or project. Check GEMINI_API_KEY and Google AI Studio access."
            elif response.status_code == 404:
                detail = "Gemini model unavailable. Check GEMINI_MODEL in the backend .env."
            elif response.status_code == 429:
                detail = "Gemini quota or rate limit reached. Check the project's current API limits."
            elif response.status_code == 503:
                detail = "Gemini is temporarily overloaded. Please try generating this report again shortly."
            else:
                detail = f"Gemini report request failed (HTTP {response.status_code})."
            raise HTTPException(502, detail)
        data = response.json()
        candidates = data.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        prediction = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
        if not prediction:
            raise HTTPException(502, "Gemini returned no report text. Check the prompt or safety response.")
        return prediction[:16000]
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        logger.warning("Gemini report request timed out")
        raise HTTPException(504, "Gemini took too long to respond. Try the report again.") from exc
    except httpx.RequestError as exc:
        logger.warning("Could not connect to Gemini while generating a report")
        raise HTTPException(502, "Could not connect to Gemini. Check the backend network connection.") from exc


async def answer_astrology_question(chart: dict, question: str, language: str = "en") -> str:
    """Draft a concise, chart-aware answer to a user's astrology question."""
    chart_data = {
        "lagna": chart.get("lagna"),
        "moon_sign": chart.get("rasi"),
        "nakshatra": chart.get("nakshatra"),
        "planets": [
            {key: planet.get(key) for key in ("name", "rasi", "longitude", "navamsa")}
            for planet in chart.get("planets", [])
        ],
        "current_dasha": next((
            {"mahadasha": major.get("lord"), "bhukti": period.get("lord")}
            for major in (chart.get("dasha") or {}).get("mahadashas", [])
            for period in major.get("bhuktis", []) if period.get("is_current")
        ), None),
    }
    language_name = {"en": "English", "ta": "Tamil", "hi": "Hindi"}.get(language, "English")
    prompt = (
        "Answer the user's astrology question using only the supplied Vedic chart data. "
        "Keep the answer warm, direct, and suitable to be read aloud in about 3 to 5 sentences. "
        "Frame astrology as a traditional interpretive practice, not certainty. Do not give medical, legal, "
        "or guaranteed financial advice. Do not invent chart placements or dates. "
        f"Write the complete answer in {language_name}.\n\n"
        f"Question: {question}\nChart data: {json.dumps(chart_data, ensure_ascii=True)}"
    )
    provider = settings.ai_provider.strip().lower()
    if provider == "gemini":
        return (await _generate_with_gemini(prompt))[:2500]
    if provider != "openai":
        raise HTTPException(503, "Unsupported AI_PROVIDER. Choose gemini or openai.")
    if not settings.openai_api_key:
        raise HTTPException(503, "OpenAI question answering is not configured. Set OPENAI_API_KEY in the backend .env.")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.responses.create(
            model=settings.report_ai_model,
            instructions="Answer astrology questions carefully and concisely for a client.",
            input=prompt,
        )
        answer = response.output_text.strip()
        if not answer:
            raise HTTPException(502, "AI question answering returned no content.")
        return answer[:2500]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Astrology question answering failed")
        raise HTTPException(502, "Could not generate an astrology answer.") from exc
    finally:
        await client.close()
