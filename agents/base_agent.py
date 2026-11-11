import json
import re
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


class BaseAgent:
    """Shared LLM plumbing: prompt execution and output cleanup."""

    def __init__(self, llm: Optional[BaseChatModel] = None):
        if llm is None:
            from core.llm import get_llm
            try:
                llm = get_llm()
            except ValueError:
                llm = None
        self.llm = llm

    def update_llm(self, llm: BaseChatModel):
        self.llm = llm

    def _execute_prompt(self, system_instruction: str, variables: Dict[str, Any]) -> str:
        if self.llm is None:
            raise ValueError("LLM not initialized. Provide a valid API key.")
        placeholders = "\n\n".join(f"{{{key}}}" for key in variables)
        prompt = ChatPromptTemplate.from_template(f"{{SYSTEM_INSTRUCTION}}\n\n{placeholders}")
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"SYSTEM_INSTRUCTION": system_instruction, **variables}).strip()

    def _parse_json_response(self, response: str, fallback: Optional[Dict] = None) -> Dict:
        """Extract the outermost JSON object/array from an LLM reply."""
        text = _FENCE.sub("", response.strip())
        starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
        end = max(text.rfind("}"), text.rfind("]"))
        if starts and end > 0:
            text = text[min(starts):end + 1]
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from LLM: {e}\n{text[:300]}")
            if fallback is not None:
                return fallback
            return {"feature": {"name": "Error parsing response"}, "scenarios": []}

    def _clean_code_blocks(self, text: str) -> str:
        return _FENCE.sub("", text.strip()).strip()
