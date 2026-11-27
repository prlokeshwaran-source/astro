from pydantic import BaseModel, Field

class TextToSpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    voice: str = "alloy"
    instructions: str | None = Field(default=None, max_length=1000)

    @classmethod
    def supported_voices(cls) -> set[str]:
        return {"alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse", "marin", "cedar"}
