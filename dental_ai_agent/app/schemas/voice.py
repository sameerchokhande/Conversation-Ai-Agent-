from pydantic import BaseModel

class VoiceRequest(BaseModel):
    transcript: str
