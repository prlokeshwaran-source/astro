import base64
import logging

import httpx
from fastapi import HTTPException

from app.config.settings import settings

logger = logging.getLogger(__name__)


async def synthesize_speech(
    text: str,
    voice: str = "Kore",
    instructions: str | None = None,
) -> bytes:
    """Generate WAV speech with Gemini's low-latency TTS model."""
    if not settings.gemini_api_key:
        raise HTTPException(503, "Gemini TTS is not configured. Set GEMINI_API_KEY in the backend .env.")

    payload = {
        "model": settings.gemini_tts_model,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": instructions or "Speak clearly and naturally.",
                }],
            }],
        }],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"

    try:
        timeout = httpx.Timeout(45, connect=8)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                headers={"x-goog-api-key": settings.gemini_api_key},
                json=payload,
            )
        if response.is_error:
            logger.warning("Gemini TTS returned HTTP %s", response.status_code)
            if response.status_code in {401, 403}:
                detail = "Gemini rejected the key or project. Check GEMINI_API_KEY and Google AI Studio access."
            elif response.status_code == 404:
                detail = "Gemini TTS model unavailable. Check GEMINI_TTS_MODEL in the backend .env."
            elif response.status_code == 429:
                detail = "Gemini TTS quota or rate limit reached. Check project limits."
            elif response.status_code == 503:
                detail = "Gemini TTS is temporarily overloaded. Please try again shortly."
            else:
                detail = f"Gemini TTS request failed (HTTP {response.status_code})."
            raise HTTPException(502, detail)

        data = response.json()
        audio_data = (data.get("output_audio") or {}).get("data")
        if not audio_data:
            audio_parts = [
                part.get("data")
                for step in data.get("steps", [])
                if step.get("type") == "model_output"
                for part in step.get("content", [])
                if part.get("type") == "audio" and part.get("data")
            ]
            audio_data = audio_parts[-1] if audio_parts else None
        if not audio_data:
            raise HTTPException(502, "Gemini TTS returned no audio data.")
        return base64.b64decode(audio_data)
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        logger.warning("Gemini TTS request timed out")
        raise HTTPException(504, "Gemini TTS took too long to respond. Please try again.") from exc
    except httpx.RequestError as exc:
        logger.warning("Could not connect to Gemini TTS")
        raise HTTPException(502, "Could not connect to Gemini. Check the backend network connection.") from exc
    except (ValueError, KeyError) as exc:
        logger.exception("Gemini TTS returned an invalid response")
        raise HTTPException(502, "Gemini TTS returned an invalid audio response.") from exc
