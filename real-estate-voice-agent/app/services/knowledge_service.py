import json
import os
from app.config import constants
from app.utils.logger import logger

class KnowledgeService:
    """Service to load and match real estate project details from JSON knowledge bases."""

    def __init__(self) -> None:
        self.project_path = os.path.join(constants.KNOWLEDGE_DIR, "project.json")
        self.pricing_path = os.path.join(constants.KNOWLEDGE_DIR, "pricing.json")
        self.faq_path = os.path.join(constants.KNOWLEDGE_DIR, "faq.json")
        self.amenities_path = os.path.join(constants.KNOWLEDGE_DIR, "amenities.json")
        self.offers_path = os.path.join(constants.KNOWLEDGE_DIR, "offers.json")
        self.builder_path = os.path.join(constants.KNOWLEDGE_DIR, "builder_information.json")

    def _load_json(self, file_path: str):
        if not os.path.exists(file_path):
            logger.error(f"Knowledge JSON file not found at: {file_path}")
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return {}

    def get_combined_context(self, user_query: str) -> str:
        """Determines what category the question targets and extracts the context."""
        query_lower = user_query.lower()
        
        # Load files
        project = self._load_json(self.project_path)
        pricing = self._load_json(self.pricing_path)
        faq_list = self._load_json(self.faq_path)
        amenities = self._load_json(self.amenities_path)
        offers = self._load_json(self.offers_path)
        builder = self._load_json(self.builder_path)

        context_blocks = []

        # 1. Search FAQ lists first
        faq_matches = []
        if isinstance(faq_list, list):
            for item in faq_list:
                q = item.get("question", "").lower()
                # If query matches any significant keywords
                words = [w for w in query_lower.split() if len(w) > 3]
                if any(word in q for word in words) or (query_lower in q):
                    faq_matches.append(f"Q: {item.get('question')}\nA: {item.get('answer')}")
        
        if faq_matches:
            context_blocks.append("### FAQ Matches:\n" + "\n\n".join(faq_matches))

        # 2. Match pricing / configuration keywords
        if any(w in query_lower for w in ["price", "cost", "lakh", "bhk", "configuration", "emi", "payment", "down payment", "bhado", "installment", "budget"]):
            config_desc = []
            if pricing.get("configurations"):
                for c in pricing.get("configurations", []):
                    config_desc.append(f"- {c.get('type')}: {c.get('carpet_area_sqft')} sqft, base price: {c.get('base_price_lakh')} Lakhs (all-inclusive: {c.get('all_inclusive_price_lakh')} Lakhs)")
            
            plans_desc = []
            if pricing.get("payment_plans"):
                for p in pricing.get("payment_plans", []):
                    plans_desc.append(f"- {p.get('name')}: {p.get('description')}")

            banks = ", ".join(pricing.get("bank_approvals", []))

            pricing_summary = (
                "### Pricing & Configuration Context:\n" +
                "\n".join(config_desc) + "\n\n" +
                "**Payment Plans:**\n" + "\n".join(plans_desc) + "\n\n" +
                f"**Pre-approved banks for loan:** {banks}"
            )
            context_blocks.append(pricing_summary)

        # 3. Match amenities / location keywords
        if any(w in query_lower for w in ["amenit", "pool", "gym", "garden", "security", "school", "hospital", "landmark", "location", "shela", "area"]):
            facility_summary = ""
            if amenities.get("amenities"):
                list_items = "\n".join([f"- {a}" for a in amenities.get("amenities", [])])
                facility_summary += f"**Amenities:**\n{list_items}\n\n"
            
            nf = amenities.get("nearby_facilities", {})
            if nf:
                schools = ", ".join(nf.get("schools", []))
                hospitals = ", ".join(nf.get("hospitals", []))
                facility_summary += f"**Nearby Schools:** {schools}\n**Nearby Hospitals:** {hospitals}\n"

            loc = project.get("location", {})
            loc_str = f"Location Area: {loc.get('area')}, Landmark: {loc.get('landmark')}"

            context_blocks.append(f"### Location & Amenities Context:\n{loc_str}\n\n{facility_summary}")

        # 4. Match offers / discounts keywords
        if any(w in query_lower for w in ["offer", "discount", "gift", "scheme", "deal", "promo"]):
            offer_desc = []
            if offers.get("active_offers"):
                for o in offers.get("active_offers", []):
                    offer_desc.append(f"- {o.get('title')}: {o.get('description')} (Valid until: {o.get('valid_until')})")
            context_blocks.append("### Active Offers Context:\n" + "\n".join(offer_desc))

        # 5. Match builder credibility keywords
        if any(w in query_lower for w in ["builder", "developer", "experience", "patel group", "completed", "history"]):
            builder_summary = (
                f"### Builder Context:\n"
                f"Name: {builder.get('builder_name')}\n"
                f"Experience: {builder.get('experience_years')} years\n"
                f"Completed Projects: {builder.get('completed_projects')}\n"
                f"Track Record: {builder.get('reputation')}"
            )
            context_blocks.append(builder_summary)

        # Always append general project overview if context is light
        if not context_blocks:
            context_blocks.append(
                f"### Project Overview:\n"
                f"Name: {project.get('name')}\n"
                f"Developer: {project.get('developer')}\n"
                f"Overview: {project.get('overview')}\n"
                f"Possession: {project.get('possession_date')}\n"
                f"Construction Status: {project.get('construction_status')}"
            )

        return "\n\n".join(context_blocks)

knowledge_service = KnowledgeService()
