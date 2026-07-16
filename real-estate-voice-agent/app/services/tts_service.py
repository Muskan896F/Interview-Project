import httpx
from app.config.settings import settings
from app.utils.logger import logger

class TTSService:
    """Manages audio text-to-speech synthesis using Sarvam Bulbul API or local mock."""

    def __init__(self) -> None:
        self.api_key = settings.SARVAM_API_KEY
        self.is_mock = not self.api_key or self.api_key == "your-sarvam-api-key"
        
        if self.is_mock:
            logger.warning("Sarvam API Key not set. TTS running in mock mode.")
        else:
            logger.info("Sarvam TTS initialized.")

    def text_to_speech(self, text: str, language_code: str = "gu-IN") -> str:
        """
        Synthesize text to speech using Sarvam Bulbul.
        Returns base64 encoded audio string.
        """
        if self.is_mock or not text:
            return self._mock_speech()

        text = self.preprocess_text(text, language_code)


        # Map language strings to Sarvam supported codes
        mapped_lang = "gu-IN"
        lang_lower = language_code.lower()
        if "hi" in lang_lower:
            mapped_lang = "hi-IN"
        elif "en" in lang_lower:
            mapped_lang = "en-IN"

        try:
            url = "https://api.sarvam.ai/text-to-speech"
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            body = {
                "inputs": [text],
                "voice": "bulbul:in-f", # Bulbul female voice
                "language_code": mapped_lang,
                "target_type": "base64"
            }
            
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=body, headers=headers)
                res.raise_for_status()
                data = res.json()
                # Sarvam returns audio in base64 format under 'audios' key list
                audio_base64 = data["audios"][0]
                logger.info(f"Sarvam speech synthesis completed for: '{text[:30]}...'")
                return audio_base64
        except Exception as e:
            logger.error("Sarvam TTS failed: %s. Falling back to mock audio.", e)
            return self._mock_speech()

    def preprocess_text(self, text: str, language_code: str = "gu-IN") -> str:
        """Normalizes and prepares text for TTS synthesis (e.g. BHK pronunciation, weekdays).
        
        Expands 'BHK' to the full form 'Bedroom Hall Kitchen' so TTS engines
        can pronounce it naturally in any language mode.
        Transliterates English weekdays to phonetic forms for Hindi/Gujarati modes.
        """
        if not text:
            return ""
        import re

        # Convert English weekdays to phonetic Devanagari script (सैटरडे, संडे) 
        # so the Indian TTS engine pronounces them perfectly.
        text = re.sub(r'(?i)\bSaturday\b', 'सैटरडे', text)
        text = re.sub(r'(?i)\bSunday\b', 'संडे', text)

        # Normalize all forms of B.H.K / B H K / B-H-K / BHK / Bee Aich Kay (case-insensitive)
        # to the full form "Bedroom Hall Kitchen"
        text = re.sub(r'(?i)(?<![a-zA-Z])B[\.\-]?\s*H[\.\-]?\s*K\.?\b', 'Bedroom Hall Kitchen', text)
        text = re.sub(r'(?i)\bBee Aich Kay\b', 'Bedroom Hall Kitchen', text)
        
        # Prefix with "flat" if we see configurations like "2 Bedroom Hall Kitchen", etc.
        # and "flat" is not already before it
        pattern = r'(?i)\b(flat\s+)?(\d+|one|two|three|four|five)\s*Bedroom Hall Kitchen'
        def replacer(match):
            flat_prefix = match.group(1)
            num = match.group(2)
            if flat_prefix:
                return f"{flat_prefix.lower()}{num} Bedroom Hall Kitchen"
            else:
                return f"flat {num} Bedroom Hall Kitchen"
        text = re.sub(pattern, replacer, text)
        return text

    def _mock_speech(self) -> str:
        """Return a small dummy MP3/WAV base64 to prevent frontend execution lockouts."""
        # Clean mock 1-second silence
        return (
            "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGFtZTMuMTAwAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAA//uwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

tts_service = TTSService()
