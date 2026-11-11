from typing import Dict, List, Optional, Tuple

from core.gherkin_json import (
    apply_feature_modifications,
    has_scenario_id_gaps,
    json_to_gherkin,
    renumber_scenario_ids,
    validate_gherkin_json,
)
from prompts.requirement_agent import SYSTEM_INSTRUCTION_CHAT_REFINEMENT_AGENT, SYSTEM_INSTRUCTION_REQ_AGENT
from prompts.ui_requirement_agent import SYSTEM_INSTRUCTION_UI_CHAT_REFINEMENT_AGENT, SYSTEM_INSTRUCTION_UI_REQ_AGENT

from .base_agent import BaseAgent


class RequirementAgent(BaseAgent):
    """Turns raw requirements into a Gherkin feature (as JSON) and refines it via chat."""

    def generate_api_feature_file(self, input_requirement: str) -> Dict:
        return self._generate(SYSTEM_INSTRUCTION_REQ_AGENT, input_requirement)

    def generate_ui_feature_file(self, input_requirement: str) -> Dict:
        return self._generate(SYSTEM_INSTRUCTION_UI_REQ_AGENT, input_requirement)

    def chat_refine_api_feature_file(self, current_feature_json, chat_messages, user_message, verification_output=""):
        return self._chat_refine(
            SYSTEM_INSTRUCTION_CHAT_REFINEMENT_AGENT, current_feature_json, chat_messages, user_message, verification_output
        )

    def chat_refine_ui_feature_file(self, current_feature_json, chat_messages, user_message, verification_output=""):
        return self._chat_refine(
            SYSTEM_INSTRUCTION_UI_CHAT_REFINEMENT_AGENT, current_feature_json, chat_messages, user_message, verification_output
        )

    def _generate(self, system_instruction: str, input_requirement: str) -> Dict:
        result = self._execute_prompt(system_instruction, {"INPUT_REQUIREMENTS": input_requirement})
        return _validated(self._parse_json_response(result))

    def _chat_refine(
        self,
        system_instruction: str,
        current_feature_json: Dict,
        chat_messages: List[Dict[str, str]],
        user_message: str,
        verification_output: str,
    ) -> Tuple[str, str, Optional[Dict]]:
        """Returns (intent, explanation, proposed_feature). proposed_feature is None for questions."""
        if verification_output:
            user_message = f"[Verification Agent Feedback]\n{verification_output}\n\n[User Feedback]\n{user_message}"

        result = self._execute_prompt(
            system_instruction,
            {
                "CURRENT_FEATURE": json_to_gherkin(current_feature_json),
                "CHAT_HISTORY": _format_chat_history(chat_messages) or "(No previous conversation)",
                "USER_MESSAGE": user_message,
            },
        )
        response = self._parse_json_response(result)
        intent = response.get("intent", "change")
        explanation = response.get("explanation", "I've processed your request.")
        proposed = response.get("proposed_feature")
        modifications = response.get("modifications", [])

        if intent == "question":
            return intent, explanation, None

        # Prefer targeted modifications over a full rewrite: unchanged scenarios stay byte-identical.
        if modifications:
            try:
                updated = apply_feature_modifications(current_feature_json, modifications)
                if has_scenario_id_gaps(updated):
                    updated, _ = renumber_scenario_ids(updated)
                return "change", explanation, _validated(updated)
            except Exception as e:
                print(f"Failed to apply modifications: {e}")

        if proposed is not None:
            return intent, explanation, _validated(proposed)
        return intent, explanation, None


def _validated(feature_json: Dict) -> Dict:
    is_valid, errors = validate_gherkin_json(feature_json)
    if not is_valid:
        print(f"Feature JSON validation warnings: {errors}")
    return feature_json


def _format_chat_history(messages: List[Dict[str, str]], max_messages: int = 6) -> str:
    return "\n\n".join(
        f"[{m.get('role', 'user').upper()}]: {m.get('content', '')}" for m in messages[-max_messages:]
    )
