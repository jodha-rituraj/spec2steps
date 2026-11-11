import json
from typing import Dict, List, Optional, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from core.gherkin_json import json_to_gherkin
from core.java_json import apply_json_modification, java_to_json, json_to_java, merge_script_jsons, validate_script_json
from core.java_merger import JavaFileMerger
from core.scenario_parser import GherkinScenarioParser
from prompts.java_automation_feedback_agent import SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT
from prompts.java_automation_script_agent import SYSTEM_INSTRUCTION_AUTOMATION_AGENT_PER_SCENARIO
from prompts.java_json_script_prompts import (
    SYSTEM_INSTRUCTION_API_SCRIPT_JSON,
    SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON,
    SYSTEM_INSTRUCTION_COMPLEX_SCRIPT_MODIFICATION_JSON,
    SYSTEM_INSTRUCTION_UI_SCRIPT_JSON,
)
from prompts.ui_automation_script_agent import SYSTEM_INSTRUCTION_UI_AUTOMATION_AGENT_PER_SCENARIO

from .base_agent import BaseAgent

NO_INPUT = "(No additional user input provided)"


class AutomationScriptAgent(BaseAgent):
    """
    Generates Java step definitions per scenario and refines them via chat.

    Scripts are kept as a JSON intermediate representation (imports, fields, methods)
    so the LLM returns small modifications that are applied deterministically,
    instead of rewriting the whole Java file on every edit.
    """

    def generate_api_scripts_json_per_scenario(self, feature_json: Dict, user_additional_input: str = "") -> List[Dict]:
        return self._generate_script_jsons(
            feature_json, user_additional_input, SYSTEM_INSTRUCTION_API_SCRIPT_JSON, SYSTEM_INSTRUCTION_AUTOMATION_AGENT_PER_SCENARIO
        )

    def generate_ui_scripts_json_per_scenario(self, feature_json: Dict, user_additional_input: str = "") -> List[Dict]:
        return self._generate_script_jsons(
            feature_json, user_additional_input, SYSTEM_INSTRUCTION_UI_SCRIPT_JSON, SYSTEM_INSTRUCTION_UI_AUTOMATION_AGENT_PER_SCENARIO
        )

    def merge_script_jsons(self, script_jsons: List[Dict], merged_class_name: str = "GeneratedTests") -> Dict:
        return merge_script_jsons(script_jsons, merged_class_name)

    def merge_java_files(self, java_files: List[str], merged_class_name: str = "GeneratedTests") -> str:
        return JavaFileMerger(merged_class_name=merged_class_name).merge(java_files)

    def script_json_to_java(self, script_json: Dict) -> str:
        return json_to_java(script_json)

    def java_to_script_json(self, java_code: str) -> Dict:
        return java_to_json(java_code)

    def chat_refine_script_json(
        self, current_script_json: Dict, chat_messages: List[Dict], user_message: str
    ) -> Tuple[str, str, str, Optional[Dict]]:
        """Returns (intent, reasoning, explanation, proposed_script_json)."""
        self._require_llm()
        if isinstance(current_script_json, str):
            current_script_json = json.loads(current_script_json)

        # Filled with str.replace (the inserted script is JSON), so unescape the template's {{ }} first.
        instruction = (
            SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON.replace("{{", "{").replace("}}", "}")
            .replace("{CURRENT_SCRIPT_JSON}", json.dumps(current_script_json, indent=2))
            .replace("{CHAT_HISTORY}", _format_chat_history(chat_messages))
            .replace("{USER_MESSAGE}", user_message)
        )
        content, reasoning = self._invoke_with_reasoning(instruction)

        try:
            parsed = json.loads(_extract_json(content))
        except json.JSONDecodeError as e:
            print(f"Chat refinement returned invalid JSON ({e}); falling back to full rewrite")
            return self._complex_script_modification_json(current_script_json, user_message)

        intent = parsed.get("intent", "change")
        explanation = parsed.get("explanation", "I've processed your request.")
        modifications = parsed.get("modifications", [])
        proposed = parsed.get("proposed_script_json") or parsed.get("proposed_script")

        if intent == "question" or not modifications:
            if intent == "regenerate" and proposed is not None:
                return intent, reasoning, explanation, _validated(proposed)
            return intent, reasoning, explanation, None

        modified = current_script_json
        for mod in modifications:
            try:
                modified = apply_json_modification(modified, mod)
            except Exception as e:
                print(f"Skipping modification {mod}: {e}")
        return "change", reasoning, explanation, _validated(modified)

    def chat_refine_script(self, current_script: str, chat_messages: List[Dict], user_message: str) -> Tuple[str, str, Optional[str]]:
        """Plain-text fallback used when no script JSON is available. Returns (intent, explanation, proposed_java)."""
        self._require_llm()
        result = self._run(
            SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT.format(
                CURRENT_SCRIPT=current_script,
                CHAT_HISTORY=_format_chat_history(chat_messages),
                USER_MESSAGE=user_message,
            )
        )
        try:
            parsed = json.loads(_extract_json(result))
        except json.JSONDecodeError as e:
            print(f"Chat refinement returned invalid JSON: {e}")
            return "change", "I couldn't parse the response. Please try rephrasing.", None

        proposed = parsed.get("proposed_script")
        return (
            parsed.get("intent", "change"),
            parsed.get("explanation", "I've processed your request."),
            self._clean_code_blocks(proposed) if proposed else None,
        )

    def _generate_script_jsons(self, feature_json, user_input, json_instruction, java_instruction) -> List[Dict]:
        self._require_llm()
        user_input = user_input if user_input.strip() else NO_INPUT
        scenarios = GherkinScenarioParser().parse(json_to_gherkin(feature_json))

        script_jsons = []
        for i, scenario in enumerate(scenarios, 1):
            result = self._run(json_instruction.format(FEATURE_FILE=scenario, USER_ADDITIONAL_INPUT=user_input))
            script_json = self._parse_script_json(result)
            if script_json is None:
                # The model occasionally returns Java instead of JSON; generate Java and parse it.
                print(f"Scenario {i}: JSON generation failed, falling back to Java")
                prompt = java_instruction.replace("{FEATURE_FILE}", scenario).replace("{USER_ADDITIONAL_INPUT}", user_input)
                java = self._clean_code_blocks(self._run(prompt))
                script_json = java_to_json(java)
            script_jsons.append(script_json)
        return script_jsons

    def _complex_script_modification_json(self, current_script_json: Dict, user_request: str):
        content, reasoning = self._invoke_with_reasoning(
            SYSTEM_INSTRUCTION_COMPLEX_SCRIPT_MODIFICATION_JSON.format(
                CURRENT_SCRIPT_JSON=json.dumps(current_script_json, indent=2),
                USER_REQUEST=user_request,
            )
        )
        modified = self._parse_script_json(content)
        if modified is None:
            return "change", reasoning, "I couldn't apply that change. Please try rephrasing.", None
        return "change", reasoning, "I've applied the requested changes to the script.", modified

    def _run(self, text: str) -> str:
        chain = ChatPromptTemplate.from_template("{TEXT}") | self.llm | StrOutputParser()
        return chain.invoke({"TEXT": text})

    def _invoke_with_reasoning(self, text: str) -> Tuple[str, str]:
        """Returns (content, reasoning). Reasoning models on Groq expose their trace in additional_kwargs."""
        self._require_llm()
        message = (ChatPromptTemplate.from_template("{TEXT}") | self.llm).invoke({"TEXT": text})
        return message.content, message.additional_kwargs.get("reasoning_content", "")

    def _parse_script_json(self, response: str) -> Optional[Dict]:
        try:
            return _validated(json.loads(_extract_json(response)))
        except json.JSONDecodeError as e:
            print(f"Failed to parse script JSON: {e}")
            return None

    def _require_llm(self):
        if self.llm is None:
            raise ValueError("LLM not initialized. Provide a valid API key.")


def _extract_json(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    end = max(text.rfind("}"), text.rfind("]"))
    if starts and end > 0:
        text = text[min(starts):end + 1]
    return text


def _validated(script_json: Dict) -> Dict:
    is_valid, errors = validate_script_json(script_json)
    if not is_valid:
        print(f"Script JSON validation warnings: {errors}")
    return script_json


def _format_chat_history(messages: List[Dict]) -> str:
    if not messages:
        return "(No previous conversation)"
    return "\n\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}" for m in messages[-6:]
    )
