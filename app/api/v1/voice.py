from fastapi import APIRouter, Depends
from fastapi.responses import Response
from app.middleware.auth import current_user
from app.schemas.voice import TextToSpeechRequest
from app.services.voice_service import synthesize_speech

LANGUAGE_NAMES = {"en": "English", "ta": "Tamil", "hi": "Hindi"}

router = APIRouter(prefix="/voice", tags=["voice"])

@router.post("/text-to-speech", responses={200: {"content": {"audio/mpeg": {}}}})
async def text_to_speech(body: TextToSpeechRequest, user: dict = Depends(current_user)):
    if body.voice not in body.supported_voices():
        from fastapi import HTTPException
        raise HTTPException(422, "Unsupported voice. Choose a supported voice such as alloy, nova, or shimmer.")
    language = user.get("preferred_language", "en")
    instructions = body.instructions or f"Speak clearly and naturally in {LANGUAGE_NAMES.get(language, 'English')}."
    audio = await synthesize_speech(body.text, body.voice, instructions)
    return Response(content=audio, media_type="audio/mpeg",
                    headers={"Content-Disposition": "attachment; filename=prediction.mp3"})
