import base64
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.middleware.auth import current_user
from app.schemas.voice import AstrologyVoiceAnswerResponse, AstrologyVoiceQuestionRequest, TextToSpeechRequest
from app.services.astrology_service import generate_chart
from app.services.report_service import answer_astrology_question
from app.services.voice_service import synthesize_speech

LANGUAGE_NAMES = {"en": "English", "ta": "Tamil", "hi": "Hindi"}

router = APIRouter(prefix="/voice", tags=["voice"])

@router.post("/text-to-speech", responses={200: {"content": {"audio/wav": {}}}})
async def text_to_speech(body: TextToSpeechRequest, user: dict = Depends(current_user)):
    if body.voice not in body.supported_voices():
        raise HTTPException(422, "Unsupported Gemini voice. Choose Kore, Puck, Charon, Aoede, Zephyr, or another supported voice.")
    language = user.get("preferred_language", "en")
    instructions = body.instructions or f"Speak clearly and naturally in {LANGUAGE_NAMES.get(language, 'English')}."
    audio = await synthesize_speech(body.text, body.voice, instructions)
    return Response(content=audio, media_type="audio/wav",
                    headers={"Content-Disposition": "attachment; filename=prediction.wav"})


@router.post("/astrology-answer", response_model=AstrologyVoiceAnswerResponse, summary="Answer an astrology question with spoken audio")
async def astrology_answer(body: AstrologyVoiceQuestionRequest, user: dict = Depends(current_user)):
    """Generate a chart-based answer and speech audio in the selected profile language."""
    if body.voice not in body.supported_voices():
        raise HTTPException(422, "Unsupported Gemini voice. Choose Kore, Puck, Charon, Aoede, Zephyr, or another supported voice.")
    language = body.language or user.get("preferred_language", "en")
    chart = await generate_chart(body.chart, language)
    answer = await answer_astrology_question(chart, body.question, language)
    audio = await synthesize_speech(
        answer,
        body.voice,
        f"Speak clearly and naturally in {LANGUAGE_NAMES.get(language, 'English')}.",
    )
    return {
        "question": body.question,
        "answer": answer,
        "language": language,
        "audio_wav_base64": base64.b64encode(audio).decode("ascii"),
    }
