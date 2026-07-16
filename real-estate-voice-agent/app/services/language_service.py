from app.services.llm_service import llm_service
from app.services.prompt_builder import prompt_builder
from app.utils.logger import logger

class LanguageService:
    """Class to detect customer language dynamically."""

    def detect_language(self, user_input: str, current_language: str = "gujarati") -> str:
        """
        Determines if the customer is speaking gujarati, hindi, or english.
        Defaults to preserving the current active language to avoid false switches.
        """
        if not user_input or len(user_input.strip()) < 2:
            return current_language

        input_lower = user_input.lower().strip()

        # ── Priority 1: Strong Gujarati markers ──
        gujarati_words = [
            "kem cho", "tame", "mate", "karva", "nathi", "cho", "chhu", "chhe",
            "tamne", "aavi", "javsho", "karso", "malse", "kyare", "shu", "shubh",
            "hu", "avar", "saras", "bahu", "ane", "pan", "pachi", "vaat", "thay",
            "haa", "na", "aaje", "kal", "weekend", "tamari", "mari"
        ]
        if any(word in input_lower for word in gujarati_words):
            return "gujarati"

        # ── Priority 2: Strong Hindi markers ──
        hindi_words = [
            "kya", "hai", "aap", "bol rahe", "mujhe", "karne", "hoon", "karunga",
            "bilkul", "theek", "main", "nahi", "haan", "abhi", "bahut", "achha",
            "samajh", "baat", "karenge", "dekhte", "chahiye", "suniye", "jee"
        ]
        if any(word in input_lower for word in hindi_words):
            return "hindi"

        # ── Priority 3: Clear English-only sentences ──
        # Only classify as English if there are multiple English words forming a sentence.
        # Single words like "yes", "no", "hello", "ok", "busy" do NOT count — keep current language.
        # Short / ambiguous inputs that must NOT trigger a language switch.
        # This includes common single-word qualification answers (city names, numbers etc.)
        ambiguous_single_words = {
            "yes", "no", "ok", "okay", "hello", "hi", "bye", "sure", "fine",
            "busy", "later", "good", "wait", "right", "thanks", "thank you",
            "call", "not now", "correct", "please", "yeah", "yep", "nope",
            # Common city/area names that look like proper nouns
            "ahmedabad", "shela", "bopal", "satellite", "prahlad nagar",
            "vejalpur", "maninagar", "naranpura", "vastrapur", "thaltej",
            "gandhinagar", "surat", "vadodara", "rajkot", "anand",
            # Number-only answers (budget, timeline)
            "40", "50", "60", "70", "80", "90",
        }
        words_in_input = set(input_lower.split())
        # Also treat input as ambiguous if it is a single-word proper noun (starts with capital in original)
        is_single_word = len(user_input.strip().split()) == 1
        first_word_original = user_input.strip().split()[0] if user_input.strip() else ""
        is_proper_noun = is_single_word and first_word_original and first_word_original[0].isupper()

        if words_in_input.issubset(ambiguous_single_words) or is_proper_noun:
            # Ambiguous short response — preserve current language
            logger.info(f"Ambiguous/proper-noun input '{user_input}' — preserving language: '{current_language}'")
            return current_language

        # Check if it looks like a full English sentence
        english_sentence_markers = [
            "i am", "i'm", "i want", "i need", "i think", "can you", "could you",
            "what is", "how much", "is there", "do you", "tell me", "when will",
            "please", "looking for", "interested in", "not interested", "let me"
        ]
        if any(marker in input_lower for marker in english_sentence_markers):
            return "english"

        # ── Priority 4: LLM fallback for ambiguous multi-word input ──
        try:
            system_prompt = "You are a language detection utility. Respond with exactly one word: gujarati, hindi, or english."
            user_prompt = prompt_builder.build_prompt("language_prompt.txt", user_input=user_input)
            detected = llm_service.generate(system_prompt, user_prompt).strip().lower()
            if detected in ["gujarati", "hindi", "english"]:
                logger.info(f"LLM detected language: '{detected}' for input: '{user_input[:30]}'")
                return detected
        except Exception as e:
            logger.error(f"Language detection LLM error: {e}")

        # ── Fallback: preserve current language (don't default-reset to gujarati) ──
        return current_language

language_service = LanguageService()
