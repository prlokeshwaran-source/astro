import logging
from fastapi import HTTPException
from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)

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
    except AuthenticationError as exc:
        logger.warning("OpenAI rejected the TTS API key (authentication failure)")
        raise HTTPException(502, "OpenAI rejected the API key. Check OPENAI_API_KEY in the backend .env.") from exc
    except PermissionDeniedError as exc:
        logger.warning("OpenAI denied TTS access for the configured project or model")
        raise HTTPException(502, "OpenAI denied text-to-speech access. Check project permissions and TTS_MODEL.") from exc
    except NotFoundError as exc:
        logger.warning("Configured TTS model was not found or is unavailable")
        raise HTTPException(502, "The configured text-to-speech model is unavailable. Check TTS_MODEL in .env.") from exc
    except RateLimitError as exc:
        logger.warning("OpenAI TTS was rate limited or the project has no quota")
        raise HTTPException(502, "OpenAI text-to-speech quota or rate limit reached. Check project billing and limits.") from exc
    except APIConnectionError as exc:
        logger.warning("Could not connect to OpenAI while synthesizing speech")
        raise HTTPException(502, "Could not connect to OpenAI. Check the backend network connection.") from exc
    except APIStatusError as exc:
        logger.error("OpenAI TTS request returned HTTP %s", exc.status_code)
        raise HTTPException(502, f"OpenAI text-to-speech request failed (HTTP {exc.status_code}). Check backend logs.") from exc
    except Exception as exc:
        logger.exception("Unexpected error while synthesizing speech")
        raise HTTPException(502, "Unexpected text-to-speech error. Check the backend terminal for details.") from exc
    finally:
        await client.close()
