import os
from io import BytesIO
from fastapi import UploadFile

try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None

class AudioAdapter:
    def __init__(self) -> None:
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai = OpenAI(api_key=self.openai_key) if (OpenAI and self.openai_key) else None

    async def transcribe(self, file: UploadFile) -> str:
        data = await file.read()
        if not data:
            return "(empty file)"
        if not self.openai:
            return "[error] OPENAI_API_KEY not configured"
        bio = BytesIO(data)
        bio.name = getattr(file, "filename", "audio.wav")
        try:
            resp = self.openai.audio.transcriptions.create(
                model="whisper-1",
                file=bio,
            )
            return getattr(resp, "text", str(resp))
        except Exception as e:
            return f"[error] {e}"