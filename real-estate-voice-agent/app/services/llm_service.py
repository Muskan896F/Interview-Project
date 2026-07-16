import os
from app.config.settings import settings
from app.utils.logger import logger

class LLMService:
    """Interfaces with the LLM API (OpenAI/Gemini) or a mock generator."""

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER.lower()
        self.openai_key = settings.OPENAI_API_KEY
        self.google_key = settings.GOOGLE_API_KEY
        self.is_mock = True
        self.model = None

        if self.provider == "openai" and self.openai_key and self.openai_key != "your-openai-api-key":
            try:
                from langchain_openai import ChatOpenAI
                kwargs = {
                    "api_key": self.openai_key,
                    "model": settings.OPENAI_MODEL,
                    "temperature": 0.3
                }
                if self.openai_key.startswith("sk-or-v1-"):
                    kwargs["base_url"] = "https://openrouter.ai/api/v1"
                    logger.info("OpenRouter key format detected. Configuring base_url to OpenRouter API.")
                
                self.model = ChatOpenAI(**kwargs)
                self.is_mock = False
                logger.info("LLM initialized with OpenAI/OpenRouter %s", settings.OPENAI_MODEL)
            except Exception as e:
                logger.error("Failed to load OpenAI model: %s", e)

        elif self.provider == "gemini" and self.google_key and self.google_key != "your-google-api-key":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.model = ChatGoogleGenerativeAI(
                    api_key=self.google_key,
                    model=settings.GEMINI_MODEL,
                    temperature=0.3
                )
                self.is_mock = False
                logger.info("LLM initialized with Gemini %s", settings.GEMINI_MODEL)
            except Exception as e:
                logger.error("Failed to load Gemini model: %s", e)
        
        if self.is_mock:
            logger.warning("LLM key missing or invalid. Operating in MOCK mode.")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM or mock generator to retrieve text response."""
        if self.is_mock or not self.model:
            return self._mock_generation(system_prompt, user_prompt)
        
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            res = self.model.invoke(messages)
            return str(res.content).strip()
        except Exception as e:
            logger.error("Error during LLM invocation: %s. Falling back to mock.", e)
            return self._mock_generation(system_prompt, user_prompt)

    def _mock_generation(self, system_prompt: str, user_prompt: str) -> str:
        """Rule-based local fallback responses matching the outbound voice flow in multiple languages."""
        up = user_prompt.lower()
        sp = system_prompt.lower()

        # Detect active language from the user_prompt context
        lang = "gujarati"
        if "current_language} is \"hindi\"" in user_prompt or "language: hindi" in up or "active language: hindi" in up:
            lang = "hindi"
        elif "current_language} is \"english\"" in user_prompt or "language: english" in up or "active language: english" in up:
            lang = "english"
        elif "hindi" in up and "current_language" in up:
            lang = "hindi"
        elif "english" in up and "current_language" in up:
            lang = "english"

        # Handle Summary node
        if "generate a json object with this exact structure" in sp:
            return """{
              "interested": true,
              "budget": "50 to 60 Lakhs",
              "preferred_location": "Shela",
              "property_type": "3 BHK",
              "purpose": "Self-Use",
              "timeline": "3 months",
              "questions_asked": ["possession date kyare chhe?", "bank loan malishe?"],
              "objections": [],
              "booking_status": "booked",
              "follow_up_status": "not_scheduled",
              "lead_score": 90,
              "summary_text": "Customer is highly interested in Shubh Residency 3 BHK luxury flats. Site visit is booked for Saturday morning."
            }"""

        # Outbound greeting (always starts in Gujarati)
        if "greeting_prompt" in up or "greet the customer warmly" in up or (("introduce yourself" in sp or "greeting" in up) and "never introduce yourself" not in sp):
            return "Hello! Hu Sarah bolu chhu, Patel Group Developers mathi. Tamari Shubh Residency ni inquiry mate call kari chhu — shuu hamare atyare thodi vaat thay shke?"


        # Professional farewell when customer is not available
        if "not available" in up or "warm, professional goodbye" in up:
            if lang == "hindi":
                return "Bilkul, koi baat nahi! Main aapko baad mein call karti hoon. Aapka din shubh rahe!"
            elif lang == "english":
                return "Of course, no problem at all! I'll reach out at a more convenient time. Have a wonderful day!"
            return "Bilkul, koi vaat nahi! Hu tamne baad ma call karis. Tamaro divas shubh rahe!"

        # Permission prompt
        if "permission" in up or "confirmed they are available" in up:
            if lang == "hindi":
                return "Bahut achha! Kya main aapse Shubh Residency ke baare mein kuch quick questions pooch sakti hoon?"
            elif lang == "english":
                return "Wonderful! May I ask you a few quick questions to help find the perfect property for you?"
            return "Khub saras! Hu tamare mate best property option find kari shaku e mate shu hu tamne thoda questions puchhi shaku?"

        # Qualification prompts
        if "qualification" in sp or "next field" in up:
            if lang == "hindi":
                if "budget" in up:
                    return "Aapka kya budget hai is property ke liye? Hamare paas flat 2 Bedroom Hall Kitchen 52 Lakhs se shuru hote hain."
                if "preferred_location" in up or "location" in up:
                    return "Aap kaun se area mein property dekhna chahte hain — Shela ya aas-paas ka koi aur area?"
                if "property_type" in up or "bhk" in up:
                    return "Aap kitne Bedroom Hall Kitchen ka flat chahte hain — flat 2 Bedroom Hall Kitchen, flat 3 Bedroom Hall Kitchen, ya flat 4 Bedroom Hall Kitchen?"
                if "purpose" in up:
                    return "Kya aap yeh property self-use ke liye le rahe hain ya investment ke liye?"
                if "timeline" in up:
                    return "Aap kitne time mein purchase karne ki planning kar rahe hain?"
            elif lang == "english":
                if "budget" in up:
                    return "What is your budget range for this property? Our flat 2 Bedroom Hall Kitchen units start from 52 Lakhs."
                if "preferred_location" in up or "location" in up:
                    return "Which area are you looking at — Shela or any nearby locality?"
                if "property_type" in up or "bhk" in up:
                    return "Are you looking for a flat 2 Bedroom Hall Kitchen, flat 3 Bedroom Hall Kitchen, or flat 4 Bedroom Hall Kitchen configuration?"
                if "purpose" in up:
                    return "Is this property for self-use or investment purposes?"
                if "timeline" in up:
                    return "When are you planning to make the purchase — within 3 months or later?"
            else:  # gujarati
                if "budget" in up:
                    return "Perfect! Tame property mate shu budget rakhi ne chalo cho? Ahiya flat 2 Bedroom Hall Kitchen 52 Lakhs thi start thai chhe."
                if "preferred_location" in up or "location" in up:
                    return "Saru, Shela area tamara mate preferred chhe ke aaju baaju no bijo koi area pan chalsho?"
                if "property_type" in up or "bhk" in up:
                    return "Tame ketla Bedroom Hall Kitchen flat shoho cho? flat 2 Bedroom Hall Kitchen, flat 3 Bedroom Hall Kitchen ke flat 4 Bedroom Hall Kitchen luxury option?"
                if "purpose" in up:
                    return "Aa property tame self-use mate buy karva mango cho ke investment purpose mate?"
                if "timeline" in up:
                    return "Tame ketla samay ma flat buy karva ni planning karo cho? 3 months ke ema thodo time chhe?"

        # Objection responses
        if "objection" in sp or "objection" in up:
            if lang == "hindi":
                if "busy" in up:
                    return "Bilkul samajh sakti hoon. Kya main aapko thodi der baad call kar sakti hoon? Kaun sa time aapke liye theek rahega?"
                return "Main samajhti hoon. Shubh Residency mein flexible payment options hain. Kya aap ek baar site visit kar sakte hain?"
            elif lang == "english":
                if "busy" in up:
                    return "I completely understand! When would be a better time for me to call you back?"
                return "I understand your concern. Shubh Residency offers very flexible payment options. Would you consider a quick site visit this weekend?"
            else:
                if "busy" in up:
                    return "Hu samji shaku chhu. To aapan thoda samay pachi vaat kariye? Tamne ketla vage callback karu?"
                return "Saru, hu samji shaku chhu. Amari pase flexible payment options chhe. Tame ek var site visit book karo?"

        # Booking prompts
        if "booking" in sp or "site visit" in up:
            if lang == "hindi":
                return "Bahut achha! Aap kab aana chahenge — Saturday ya Sunday? Aur kaun sa time aapke liye theek rahega?"
            elif lang == "english":
                return "That's great! Would you prefer to visit on Saturday or Sunday, and what time works best for you?"
            return "Khub saras! To tame site visit Saturday mate book karva mango cho ke Sunday mate?"

        # Followup prompts
        if "followup" in sp or "callback" in up:
            if lang == "hindi":
                return "Theek hai! Kab main aapko call karun — kaun sa din aur time aapke liye convenient rahega?"
            elif lang == "english":
                return "Sure! What day and time works best for me to call you back?"
            return "Saru, tame jyare free hovo tyare call schedule kari aapu. Tamara mate kayo divas ane time convenient raheshe?"

        # Generic fallback
        if lang == "hindi":
            return "Main samajhti hoon. Kya aap Shubh Residency ke baare mein aur jaanna chahenge?"
        elif lang == "english":
            return "I understand. Would you like to know more about Shubh Residency?"
        return "Saru, hu samji shaku chhu. Tamara mate site visit schedule kari aapu?"


llm_service = LLMService()
