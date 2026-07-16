import os
from app.config.constants import PROMPTS_DIR
from app.utils.logger import logger

class PromptBuilder:
    """Utility class to load and format prompts dynamically from disk."""

    @staticmethod
    def load_prompt(filename: str) -> str:
        """Load raw prompt template string from prompts directory."""
        path = os.path.join(PROMPTS_DIR, filename)
        if not os.path.exists(path):
            logger.error(f"Prompt template file '{filename}' not found at: {path}")
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading prompt file {path}: {e}")
            return ""

    @classmethod
    def build_prompt(cls, filename: str, **kwargs) -> str:
        """Loads a prompt template and injects formatting values."""
        template = cls.load_prompt(filename)
        if not template:
            return ""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"KeyError formatting prompt '{filename}': Missing key {e}. Returning unformatted template.")
            return template
        except Exception as e:
            logger.error(f"Error formatting prompt '{filename}': {e}")
            return template

prompt_builder = PromptBuilder()
