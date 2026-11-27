from fastapi import HTTPException
from openai import AsyncOpenAI
from app.config.settings import settings

async def synthesize_speech(text: str, voice: str = "alloy", instructions: str | None = None) -> bytes:
    if not settings.openai_api_key:
        raise HTTPException(503, "Text-to-speech is not configured. Set OPENAI_API_KEY in .env.")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.audio.speech.create(
            model=settings.tts_model,
            voice=voice,
            input=text,
            instructions=instructions,
            response_format="mp3",
        )
        return response.content
    except Exception as exc:
        raise HTTPException(502, "Text-to-speech provider request failed") from exc
    finally:
        await client.close()
