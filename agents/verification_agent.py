"""
Verification Agent - Validates feature files against requirements.
Provides feedback on coverage, quality, and completeness.
"""

from typing import Dict
from langchain_groq import ChatGroq
from utils.gherkin_json_utils import json_to_gherkin
from llm_prompts.verification_agent import SYSTEM_INSTRUCTION_VERIFICATION_AGENT
from .base_agent import BaseAgent


class VerificationAgent(BaseAgent):
    """
    Agent responsible for verifying feature files against original requirements.
    
    Capabilities:
    - Verify feature file completeness and correctness
    - Analyze coverage of requirements
    - Provide quality assessment feedback
    - Work with both API and UI feature files
    """
    
    def __init__(self, llm: ChatGroq = None):
        """
        Initialize the Verification Agent.
        
        Args:
            llm: Optional ChatGroq instance. If None, will use the global llm from utils.
        """
        super().__init__(llm)
    
    def verify_feature_file(self, input_requirement: str, feature_json: Dict) -> str:
        """
        Verify a feature file (as JSON) against original requirements.
        
        Args:
            input_requirement: Original requirements text
            feature_json: Feature file as JSON structure
        
        Returns:
            str: Verification output - either "PERFECT" or a list of issues/suggestions
        
        Raises:
            ValueError: If LLM is not initialized
        """
        # Convert JSON to Gherkin for better context
        feature_text = json_to_gherkin(feature_json)
        
        # Build the full prompt
        prompt_content = f"""ORIGINAL REQUIREMENTS:
{input_requirement}

JSON STRUCTURE:
{feature_json}

GHERKIN REPRESENTATION (for reference):
{feature_text}
"""
        
        # Execute verification prompt
        result = self._execute_prompt(
            system_instruction=SYSTEM_INSTRUCTION_VERIFICATION_AGENT,
            variables={"PROMPT_CONTENT": prompt_content}
        )
        
        return result.strip()
