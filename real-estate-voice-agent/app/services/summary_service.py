import json
from app.services.llm_service import llm_service
from app.services.prompt_builder import prompt_builder
from app.utils.helpers import safe_json_loads
from app.utils.logger import logger

class SummaryService:
    """Service to generate structured summaries and lead scores from conversation logs."""

    def generate_summary(self, session_id: str, lead_name: str, phone: str, state_data: dict, messages_list: list) -> dict:
        """Call LLM with summary template to extract structured data."""
        # Formulate chat history text
        history_lines = []
        for m in messages_list:
            role = m.get("role", "user").upper()
            content = m.get("content", "")
            history_lines.append(f"{role}: {content}")
        
        chat_history = "\n".join(history_lines)
        
        # Compile collected variables
        state_vars = (
            f"Lead Name: {lead_name}\n"
            f"Phone: {phone}\n"
            f"Budget: {state_data.get('budget')}\n"
            f"Preferred Location: {state_data.get('preferred_location')}\n"
            f"Property Type: {state_data.get('property_type')}\n"
            f"Purpose: {state_data.get('purpose')}\n"
            f"Timeline: {state_data.get('timeline')}\n"
            f"Booking Status: {state_data.get('booking_status')}\n"
            f"Follow-up Date: {state_data.get('followup_date')} {state_data.get('followup_time')}"
        )

        try:
            # Build and send prompt
            system_prompt = "You are a real estate summary extractor. Output raw JSON only."
            user_prompt = prompt_builder.build_prompt(
                "summary_prompt.txt",
                chat_history=chat_history,
                state_variables=state_vars
            )
            
            response = llm_service.generate(system_prompt, user_prompt)
            
            # Clean possible markdown block wraps
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = safe_json_loads(cleaned)
            if isinstance(parsed, dict):
                logger.info(f"Summary generated successfully for session: {session_id}")
                return parsed
        except Exception as e:
            logger.error(f"Error during summary extraction LLM run: {e}")

        # Return fallback dictionary if JSON extraction fails
        return {
            "interested": bool(state_data.get("booking_status") == "booked"),
            "budget": state_data.get("budget"),
            "preferred_location": state_data.get("preferred_location"),
            "property_type": state_data.get("property_type"),
            "purpose": state_data.get("purpose"),
            "timeline": state_data.get("timeline"),
            "questions_asked": [],
            "objections": [],
            "booking_status": state_data.get("booking_status", "not_scheduled"),
            "follow_up_status": "scheduled" if state_data.get("followup_date") else "not_scheduled",
            "lead_score": 50,
            "summary_text": "Outbound conversation ended. Summarized using rules fallback."
        }

summary_service = SummaryService()
