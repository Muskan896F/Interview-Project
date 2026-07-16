import base64
import httpx
from app.config.settings import settings
from app.utils.logger import logger

class STTService:
    """Manages audio speech-to-text transcribing using Deepgram API or local mock."""

    def __init__(self) -> None:
        self.api_key = settings.DEEPGRAM_API_KEY
        self.is_mock = not self.api_key or self.api_key == "your-deepgram-api-key"
        
        if self.is_mock:
            logger.warning("Deepgram API Key not set. STT running in mock mode.")
        else:
            logger.info("Deepgram STT initialized.")

    def transcribe(self, audio_bytes: bytes, content_type: str = "audio/wav") -> str:
        """Call Deepgram v1/listen to transcribe raw audio."""
        if self.is_mock:
            return self._mock_transcription(audio_bytes)

        try:
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": content_type
            }
            params = {
                "model": "nova-2",
                "smart_format": "true"
            }
            url = "https://api.deepgram.com/v1/listen"
            
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, content=audio_bytes, headers=headers, params=params)
                res.raise_for_status()
                data = res.json()
                
                transcription = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                logger.info(f"Deepgram transcribed output: '{transcription}'")
                return transcription
        except Exception as e:
            logger.error("Deepgram transcription failed: %s. Falling back to mock.", e)
            return self._mock_transcription(audio_bytes)

    def transcribe_base64(self, base64_audio: str) -> str:
        """Decode base64 string and transcribe."""
        if not base64_audio:
            return ""
        try:
            # Strip data URL header if present (e.g. data:audio/wav;base64,...)
            if "," in base64_audio:
                base64_audio = base64_audio.split(",")[1]
            audio_bytes = base64.b64decode(base64_audio)
            return self.transcribe(audio_bytes)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            return ""

    def _mock_transcription(self, audio_bytes: bytes) -> str:
        """Helper to return mock user simulation when active."""
        # Just return default text or simulate dialogue turns based on status
        logger.info("Mock STT: returning default transcription.")
        return "yes, I am interested in booking a site visit for this Saturday morning"

stt_service = STTService()
