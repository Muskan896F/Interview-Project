import unittest
from app.graph.graph import agent_workflow
from app.config import constants

class TestGraphWorkflow(unittest.TestCase):
    """Verifies LangGraph assembly compiles and transitions."""

    def test_greeting_generation(self):
        """Checks if the entry node correctly generates a sales greeting in Gujarati."""
        state = {
            "lead_name": "Dev",
            "phone": "9876543210",
            "language": "gujarati",
            "db_lead_id": 1,
            "messages": [],
            "last_message": "",
            "agent_response": "",
            "budget": "",
            "preferred_location": "",
            "property_type": "",
            "purpose": "",
            "timeline": "",
            "interested": False,
            "booking_status": "not_scheduled",
            "booking_date": "",
            "booking_time": "",
            "followup_date": "",
            "followup_time": "",
            "objection_count": 0,
            "current_node": constants.Node.GREETING,
            "summary": {}
        }
        
        # Invoke workflow
        output = agent_workflow.invoke(state)
        
        self.assertIn("agent_response", output)
        self.assertEqual(output["current_node"], constants.Node.GREETING)
        self.assertGreater(len(output["agent_response"]), 10)

if __name__ == "__main__":
    unittest.main()
