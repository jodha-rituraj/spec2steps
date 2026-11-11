from typing import Dict

from core.gherkin_json import json_to_gherkin
from prompts.verification_agent import SYSTEM_INSTRUCTION_VERIFICATION_AGENT

from .base_agent import BaseAgent


class VerificationAgent(BaseAgent):
    """Reviews a generated feature against the original requirements."""

    def verify_feature_file(self, input_requirement: str, feature_json: Dict) -> str:
        """Returns "PERFECT" or a list of gaps and suggestions."""
        prompt_content = (
            f"ORIGINAL REQUIREMENTS:\n{input_requirement}\n\n"
            f"JSON STRUCTURE:\n{feature_json}\n\n"
            f"GHERKIN REPRESENTATION (for reference):\n{json_to_gherkin(feature_json)}\n"
        )
        return self._execute_prompt(
            SYSTEM_INSTRUCTION_VERIFICATION_AGENT, {"PROMPT_CONTENT": prompt_content}
        )
