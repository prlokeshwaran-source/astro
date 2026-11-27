from pydantic import BaseModel, Field
from app.schemas.astrology import AstrologyChartRequest
from app.utils.i18n import LanguageCode

class TextToSpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    voice: str = Field(default="Kore", description="Gemini prebuilt voice name, such as Kore, Puck, or Aoede")
    instructions: str | None = Field(default=None, max_length=1000)

    @classmethod
    def supported_voices(cls) -> set[str]:
        return {"Kore", "Puck", "Charon", "Aoede", "Zephyr", "Leda", "Orus", "Callirrhoe", "Achird", "Sulafat"}


class AstrologyVoiceQuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    chart: AstrologyChartRequest
    voice: str = Field(default="Kore", description="Gemini prebuilt voice name, such as Kore, Puck, or Aoede")
    language: LanguageCode | None = None

    @classmethod
    def supported_voices(cls) -> set[str]:
        return TextToSpeechRequest.supported_voices()


class AstrologyVoiceAnswerResponse(BaseModel):
    question: str
    answer: str
    language: LanguageCode
    audio_wav_base64: str = Field(description="Base64-encoded 24 kHz mono WAV audio of the answer")
