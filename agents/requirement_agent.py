"""
Requirement Agent - Handles feature file generation and refinement.
Converts requirements into structured Gherkin feature files.
"""

from typing import Dict, Optional, List, Tuple
from langchain_groq import ChatGroq
from utils.gherkin_json_utils import json_to_gherkin, gherkin_to_json, validate_gherkin_json
from llm_prompts.requirement_agent import (
    SYSTEM_INSTRUCTION_REQ_AGENT, 
    SYSTEM_INSTRUCTION_FEEDBACK_AGENT,
    SYSTEM_INSTRUCTION_CHAT_REFINEMENT_AGENT
)
from llm_prompts.ui_requirement_agent import (
    SYSTEM_INSTRUCTION_UI_REQ_AGENT, 
    SYSTEM_INSTRUCTION_UI_FEEDBACK_AGENT,
    SYSTEM_INSTRUCTION_UI_CHAT_REFINEMENT_AGENT
)
from .base_agent import BaseAgent


class RequirementAgent(BaseAgent):
    """
    Agent responsible for generating and refining feature files from requirements.
    
    Capabilities:
    - Generate API feature files from requirements
    - Generate UI feature files from requirements
    - Refine feature files based on feedback
    - Validate feature file JSON structures
    """
    
    def __init__(self, llm: Optional[ChatGroq] = None):
        """
        Initialize the Requirement Agent.
        
        Args:
            llm: Optional ChatGroq instance. If None, will use the global llm from utils.
        """
        super().__init__(llm)
    
    def generate_api_feature_file(self, input_requirement: str) -> Dict:
        """
        Generate API feature file as JSON structure from requirements.
        
        Args:
            input_requirement: Input requirements text describing API functionality
        
        Returns:
            Dict: JSON structure representing the API feature file
        
        Raises:
            ValueError: If LLM is not initialized
        """
        # Execute the prompt
        result = self._execute_prompt(
            system_instruction=SYSTEM_INSTRUCTION_REQ_AGENT,
            variables={"INPUT_REQUIREMENTS": input_requirement}
        )
        
        # Parse and validate JSON response
        json_data = self._parse_json_response(result)
        
        # Validate the structure
        is_valid, errors = validate_gherkin_json(json_data)
        if not is_valid:
            print(f"⚠️ JSON validation warnings: {errors}")
        
        return json_data
    
    def generate_ui_feature_file(self, input_requirement: str) -> Dict:
        """
        Generate UI feature file as JSON structure from requirements.
        
        Args:
            input_requirement: Input requirements text describing UI functionality
        
        Returns:
            Dict: JSON structure representing the UI feature file
        
        Raises:
            ValueError: If LLM is not initialized
        """
        # Execute the prompt
        result = self._execute_prompt(
            system_instruction=SYSTEM_INSTRUCTION_UI_REQ_AGENT,
            variables={"INPUT_REQUIREMENTS": input_requirement}
        )
        
        # Parse and validate JSON response
        json_data = self._parse_json_response(result)
        
        # Validate the structure
        is_valid, errors = validate_gherkin_json(json_data)
        if not is_valid:
            print(f"⚠️ JSON validation warnings: {errors}")
        
        return json_data
    
    def refine_api_feature_file(
        self,
        original_feature_json: Dict,
        verification_feedback: str = "",
        user_feedback: str = ""
    ) -> Dict:
        """
        Refine an existing API feature file based on feedback.
        
        Args:
            original_feature_json: Original feature file as JSON structure
            verification_feedback: Feedback from verification agent
            user_feedback: Direct user feedback
        
        Returns:
            Dict: Refined JSON structure representing the updated feature file
        
        Raises:
            ValueError: If LLM is not initialized
        """
        # Convert JSON to Gherkin for context
        original_feature_text = json_to_gherkin(original_feature_json)
        
        # Combine feedbacks
        combined_feedback = ""
        if verification_feedback:
            combined_feedback += f"VERIFICATION FEEDBACK:\n{verification_feedback}\n\n"
        if user_feedback:
            combined_feedback += f"USER FEEDBACK:\n{user_feedback}"
        
        # Execute refinement prompt
        result = self._execute_prompt(
            system_instruction=SYSTEM_INSTRUCTION_FEEDBACK_AGENT,
            variables={
                "ORIGINAL_FEATURE_JSON": json_to_gherkin(original_feature_json),
                "COMBINED_FEEDBACK": combined_feedback.strip()
            }
        )
        
        # Parse and validate JSON response
        json_data = self._parse_json_response(result, fallback=original_feature_json)
        
        # Validate the structure
        is_valid, errors = validate_gherkin_json(json_data)
        if not is_valid:
            print(f"⚠️ JSON validation warnings: {errors}")
        
        return json_data
    
    def refine_ui_feature_file(
        self,
        original_feature_json: Dict,
        verification_feedback: str = "",
        user_feedback: str = ""
    ) -> Dict:
        """
        Refine an existing UI feature file based on feedback.
        
        Args:
            original_feature_json: Original UI feature file as JSON structure
            verification_feedback: Feedback from verification agent
            user_feedback: Direct user feedback
        
        Returns:
            Dict: Refined JSON structure representing the updated UI feature file
        
        Raises:
            ValueError: If LLM is not initialized
        """
        # Convert JSON to Gherkin for context
        original_feature_text = json_to_gherkin(original_feature_json)
        
        # Combine feedbacks
        combined_feedback = ""
        if verification_feedback:
            combined_feedback += f"VERIFICATION FEEDBACK:\n{verification_feedback}\n\n"
        if user_feedback:
            combined_feedback += f"USER FEEDBACK:\n{user_feedback}"
        
        # Execute refinement prompt
        result = self._execute_prompt(
            system_instruction=SYSTEM_INSTRUCTION_UI_FEEDBACK_AGENT,
            variables={
                "ORIGINAL_FEATURE_JSON": json_to_gherkin(original_feature_json),
                "COMBINED_FEEDBACK": combined_feedback.strip()
            }
        )
        
        # Parse and validate JSON response
        json_data = self._parse_json_response(result, fallback=original_feature_json)
        
        # Validate the structure
        is_valid, errors = validate_gherkin_json(json_data)
        if not is_valid:
            print(f"⚠️ JSON validation warnings: {errors}")
        
        return json_data

    def _format_chat_history(self, chat_messages: List[Dict[str, str]], max_messages: int = 6) -> str:
        """
        Format chat history for the LLM prompt.
        
        Args:
            chat_messages: List of message dictionaries with 'role' and 'content' keys
            max_messages: Maximum number of recent messages to include
        
        Returns:
            str: Formatted chat history string
        """
        # Take only the last N messages
        recent_messages = chat_messages[-max_messages:] if len(chat_messages) > max_messages else chat_messages
        
        formatted = []
        for msg in recent_messages:
            role = msg.get('role', 'user').upper()
            content = msg.get('content', '')
            formatted.append(f"[{role}]: {content}")
        
        return "\n\n".join(formatted)

    def chat_refine_api_feature_file(
        self,
        current_feature_json: Dict,
        chat_messages: List[Dict[str, str]],
        user_message: str,
        verification_output: str = ""
    ) -> Tuple[str, str, Dict]:
        """
        Refine an API feature file through conversational chat.
        
        Args:
            current_feature_json: Current feature file as JSON structure
            chat_messages: List of previous chat messages [{role, content}, ...]
            user_message: The latest user message/feedback
            verification_output: Optional verification output to include
        
        Returns:
            Tuple[str, str, Dict]: (intent, explanation text, proposed feature JSON or None)
            - intent: "question" or "change"
            - explanation: Response text for the user
            - proposed_feature: Updated feature JSON (or None for questions)
        
        Raises:
            ValueError: If LLM is not initialized
        """
        # Format the current feature file
        current_feature_text = json_to_gherkin(current_feature_json)
        
        # Format chat history
        chat_history = self._format_chat_history(chat_messages)
        
        # Build the user message with optional verification
        full_user_message = user_message
        if verification_output:
            full_user_message = f"[Verification Agent Feedback]\n{verification_output}\n\n[User Feedback]\n{user_message}"
        
        # Execute chat refinement prompt
        result = self._execute_prompt(
            system_instruction=SYSTEM_INSTRUCTION_CHAT_REFINEMENT_AGENT,
            variables={
                "CURRENT_FEATURE": current_feature_text,
                "CHAT_HISTORY": chat_history if chat_history else "(No previous conversation)",
                "USER_MESSAGE": full_user_message
            }
        )
        
        # Parse the response which should have intent, explanation and proposed_feature
        response_data = self._parse_json_response(result)
        
        intent = response_data.get("intent", "change")  # Default to change for backwards compatibility
        explanation = response_data.get("explanation", "I've processed your request.")
        proposed_feature = response_data.get("proposed_feature")
        
        # Only validate if there's a proposed feature (not a question)
        if proposed_feature is not None and intent == "change":
            is_valid, errors = validate_gherkin_json(proposed_feature)
            if not is_valid:
                print(f"⚠️ JSON validation warnings: {errors}")
        
        return intent, explanation, proposed_feature

    def chat_refine_ui_feature_file(
        self,
        current_feature_json: Dict,
        chat_messages: List[Dict[str, str]],
        user_message: str,
        verification_output: str = ""
    ) -> Tuple[str, str, Dict]:
        """
        Refine a UI feature file through conversational chat.
        
        Args:
            current_feature_json: Current feature file as JSON structure
            chat_messages: List of previous chat messages [{role, content}, ...]
            user_message: The latest user message/feedback
            verification_output: Optional verification output to include
        
        Returns:
            Tuple[str, str, Dict]: (intent, explanation text, proposed feature JSON or None)
            - intent: "question" or "change"
            - explanation: Response text for the user
            - proposed_feature: Updated feature JSON (or None for questions)
        
        Raises:
            ValueError: If LLM is not initialized
        """
        # Format the current feature file
        current_feature_text = json_to_gherkin(current_feature_json)
        
        # Format chat history
        chat_history = self._format_chat_history(chat_messages)
        
        # Build the user message with optional verification
        full_user_message = user_message
        if verification_output:
            full_user_message = f"[Verification Agent Feedback]\n{verification_output}\n\n[User Feedback]\n{user_message}"
        
        # Execute chat refinement prompt
        result = self._execute_prompt(
            system_instruction=SYSTEM_INSTRUCTION_UI_CHAT_REFINEMENT_AGENT,
            variables={
                "CURRENT_FEATURE": current_feature_text,
                "CHAT_HISTORY": chat_history if chat_history else "(No previous conversation)",
                "USER_MESSAGE": full_user_message
            }
        )
        
        # Parse the response which should have intent, explanation and proposed_feature
        response_data = self._parse_json_response(result)
        
        intent = response_data.get("intent", "change")  # Default to change for backwards compatibility
        explanation = response_data.get("explanation", "I've processed your request.")
        proposed_feature = response_data.get("proposed_feature")
        
        # Only validate if there's a proposed feature (not a question)
        if proposed_feature is not None and intent == "change":
            is_valid, errors = validate_gherkin_json(proposed_feature)
            if not is_valid:
                print(f"⚠️ JSON validation warnings: {errors}")
        
        return intent, explanation, proposed_feature