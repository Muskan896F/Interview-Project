import unittest
from app.services.llm_service import llm_service
from app.services.prompt_builder import prompt_builder
from app.services.knowledge_service import knowledge_service

class TestServices(unittest.TestCase):
    """Checks parsing, formatting, and mock engine defaults."""

    def test_prompt_formatting(self):
        """Verifies placeholder formatting checks."""
        raw = prompt_builder.build_prompt("greeting_prompt.txt", lead_name="Amit")
        self.assertIn("Amit", raw)

    def test_mock_llm(self):
        """Validates rule-based generation patterns when api keys are absent."""
        was_mock = llm_service.is_mock
        llm_service.is_mock = True
        try:
            greeting = llm_service.generate("introduce yourself", "Hello")
            self.assertIn("Patel Group", greeting)
        finally:
            llm_service.is_mock = was_mock


    def test_knowledge_retrieval(self):
        """Confirms search parameters filter matching JSON blocks."""
        ctx = knowledge_service.get_combined_context("What is the price of 3 BHK?")
        self.assertIn("3 BHK", ctx)
        self.assertIn("Lakhs", ctx)

    def test_tts_preprocessing(self):
        """Validates that BHK configurations are correctly formatted and prefixed with 'flat'."""
        from app.services.tts_service import tts_service
        
        # Test basic cases
        self.assertEqual(tts_service.preprocess_text("2 BHK"), "flat 2 Bedroom Hall Kitchen")
        self.assertEqual(tts_service.preprocess_text("3BHK"), "flat 3 Bedroom Hall Kitchen")
        self.assertEqual(tts_service.preprocess_text("two BHK"), "flat two Bedroom Hall Kitchen")
        self.assertEqual(tts_service.preprocess_text("flat 3 BHK"), "flat 3 Bedroom Hall Kitchen")
        
        # Test complex sentence
        complex_text = "We offer 2 BHK, 3 BHK, and 4 BHK luxury apartments."
        expected = "We offer flat 2 Bedroom Hall Kitchen, flat 3 Bedroom Hall Kitchen, and flat 4 Bedroom Hall Kitchen luxury apartments."
        self.assertEqual(tts_service.preprocess_text(complex_text), expected)

        # Test weekday transliteration
        self.assertEqual(tts_service.preprocess_text("Visit us on Saturday or Sunday.", "gu-IN"), "Visit us on सैटरडे or संडे.")
        self.assertEqual(tts_service.preprocess_text("Aap Saturday ya Sunday aana.", "hi-IN"), "Aap सैटरडे ya संडे aana.")
        self.assertEqual(tts_service.preprocess_text("Visit on Saturday or Sunday.", "en-IN"), "Visit on सैटरडे or संडे.")

if __name__ == "__main__":
    unittest.main()
