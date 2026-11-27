from pydantic import BaseModel, Field
from app.schemas.astrology import AstrologyChartRequest
from app.utils.i18n import LanguageCode

class TextToSpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    voice: str = "alloy"
    instructions: str | None = Field(default=None, max_length=1000)

    @classmethod
    def supported_voices(cls) -> set[str]:
        return {"alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse", "marin", "cedar"}


class AstrologyVoiceQuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    chart: AstrologyChartRequest
    voice: str = "alloy"
    language: LanguageCode | None = None

    @classmethod
    def supported_voices(cls) -> set[str]:
        return TextToSpeechRequest.supported_voices()


class AstrologyVoiceAnswerResponse(BaseModel):
    question: str
    answer: str
    language: LanguageCode
    audio_mpeg_base64: str = Field(description="Base64-encoded MP3 audio of the answer")
