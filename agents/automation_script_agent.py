"""
Automation Script Agent - Generates and refactors automation scripts.
Handles both API and UI test script generation with feedback-driven refinement.

Supports two modes:
1. Legacy mode: Direct Java code generation (for backward compatibility)
2. JSON IR mode: Structured JSON intermediate representation (recommended for deterministic refinement)
"""

import re
import json
import difflib
from typing import Dict, List, Tuple, Optional, Union
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.gherkin_json_utils import json_to_gherkin
from utils.java_json_utils import (
    json_to_java, 
    java_to_json, 
    merge_script_jsons, 
    apply_json_modification,
    get_json_diff,
    validate_script_json
)
from features.parser import GherkinScenarioParser
from features.merger import JavaFileMerger
from llm_prompts.java_automation_script_agent import (
    SYSTEM_INSTRUCTION_AUTOMATION_AGENT_PER_SCENARIO
)
from llm_prompts.ui_automation_script_agent import (
    SYSTEM_INSTRUCTION_UI_AUTOMATION_AGENT_PER_SCENARIO
)
from llm_prompts.java_automation_feedback_agent import (
    SYSTEM_INSTRUCTION_INTENT_EXTRACTION,
    SYSTEM_INSTRUCTION_FALLBACK_REFACTORING,
    SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT
)
from llm_prompts.java_json_script_prompts import (
    SYSTEM_INSTRUCTION_API_SCRIPT_JSON,
    SYSTEM_INSTRUCTION_UI_SCRIPT_JSON,
    SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON,
    SYSTEM_INSTRUCTION_COMPLEX_SCRIPT_MODIFICATION_JSON
)
from .base_agent import BaseAgent


class AutomationScriptAgent(BaseAgent):
    """
    Agent responsible for generating and refactoring automation scripts.
    
    Capabilities:
    - Generate API automation scripts (RestAssured)
    - Generate UI automation scripts (Selenium)
    - Refactor scripts based on user feedback
    - Extract refactoring intent from feedback
    - Apply targeted code transformations
    - Generate code diffs
    
    Supports two modes:
    - Legacy mode: Direct Java code strings
    - JSON IR mode: Structured JSON for deterministic modifications
    """
    
    def __init__(self, llm: Optional[ChatGroq] = None):
        """
        Initialize the Automation Script Agent.
        
        Args:
            llm: Optional ChatGroq instance. If None, will use the global llm from utils.
        """
        super().__init__(llm)
    
    def generate_api_scripts_per_scenario(
        self,
        feature_json: Dict,
        user_additional_input: str = ""
    ) -> List[str]:
        """
        Generate API automation scripts for each scenario.
        
        Args:
            feature_json: JSON structure representing the feature file
            user_additional_input: Additional user instructions/context
        
        Returns:
            List[str]: List of Java code files, one per scenario
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        # Convert JSON to Gherkin
        feature_file = json_to_gherkin(feature_json)
        
        # Extract scenarios using parser (handles both Scenario and Scenario Outline)
        parser = GherkinScenarioParser()
        feature_file_scenarios = parser.parse(feature_file)
        
        prompt_automation_script = ChatPromptTemplate.from_template(
            "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}\n\n{USER_ADDITIONAL_INPUT}"
        )
        output_parser = StrOutputParser()
        chain_automation = prompt_automation_script | self.llm | output_parser
        
        java_code_files = []
        
        for i, scenario in enumerate(feature_file_scenarios):
            print(f"#-------------------- Generating Java Code for Scenario {i + 1} -------------------#")
            java_code = chain_automation.invoke({
                "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT_PER_SCENARIO,
                "FEATURE_FILE": scenario,
                "USER_ADDITIONAL_INPUT": user_additional_input if user_additional_input.strip() else "(No additional user input provided)"
            })
            # Clean code blocks
            java_code = self._clean_code_blocks(java_code)
            java_code_files.append(java_code)
        
        return java_code_files
    
    def generate_ui_scripts_per_scenario(
        self,
        feature_json: Dict,
        user_additional_input: str = ""
    ) -> List[str]:
        """
        Generate UI automation scripts (Selenium) for each scenario.
        
        Args:
            feature_json: JSON structure representing the feature file
            user_additional_input: Additional user instructions/context
        
        Returns:
            List[str]: List of Java code files, one per scenario
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        # Convert JSON to Gherkin
        feature_file = json_to_gherkin(feature_json)
        
        # Extract scenarios using parser (handles both Scenario and Scenario Outline)
        parser = GherkinScenarioParser()
        feature_file_scenarios = parser.parse(feature_file)
        
        prompt_automation_script = ChatPromptTemplate.from_template(
            "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}\n\n{USER_ADDITIONAL_INPUT}"
        )
        output_parser = StrOutputParser()
        chain_automation = prompt_automation_script | self.llm | output_parser
        
        java_code_files = []
        
        for i, scenario in enumerate(feature_file_scenarios):
            print(f"#-------------------- Generating UI Java Code for Scenario {i + 1} -------------------#")
            java_code = chain_automation.invoke({
                "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_UI_AUTOMATION_AGENT_PER_SCENARIO,
                "FEATURE_FILE": scenario,
                "USER_ADDITIONAL_INPUT": user_additional_input if user_additional_input.strip() else "(No additional user input provided)"
            })
            # Clean code blocks
            java_code = self._clean_code_blocks(java_code)
            java_code_files.append(java_code)
        
        return java_code_files
    
    def merge_java_files(
        self,
        java_files: List[str],
        merged_class_name: str = "GeneratedTests"
    ) -> str:
        """
        Merge multiple Java files into a single class.
        
        Args:
            java_files: List of Java code strings to merge
            merged_class_name: Name for the merged class
        
        Returns:
            str: Merged Java code
        """
        merger = JavaFileMerger(merged_class_name=merged_class_name)
        return merger.merge(java_files)
    
    # ==================== JSON IR Based Methods (Recommended) ====================
    
    def generate_api_scripts_json_per_scenario(
        self,
        feature_json: Dict,
        user_additional_input: str = ""
    ) -> List[Dict]:
        """
        Generate API automation scripts as JSON IR for each scenario.
        
        This is the recommended method for new implementations as it
        returns structured JSON that can be deterministically modified.
        
        Args:
            feature_json: JSON structure representing the feature file
            user_additional_input: Additional user instructions/context
        
        Returns:
            List[Dict]: List of script JSON objects, one per scenario
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        # Convert JSON to Gherkin
        feature_file = json_to_gherkin(feature_json)
        
        # Extract scenarios
        parser = GherkinScenarioParser()
        feature_file_scenarios = parser.parse(feature_file)
        
        prompt = ChatPromptTemplate.from_template("{SYSTEM_INSTRUCTION}")
        output_parser = StrOutputParser()
        chain = prompt | self.llm | output_parser
        
        script_jsons = []
        
        for i, scenario in enumerate(feature_file_scenarios):
            print(f"#-------------------- Generating JSON IR for API Scenario {i + 1} -------------------#")
            
            result = chain.invoke({
                "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_API_SCRIPT_JSON.format(
                    FEATURE_FILE=scenario,
                    USER_ADDITIONAL_INPUT=user_additional_input if user_additional_input.strip() else "(No additional user input provided)"
                )
            })
            
            # Parse JSON response
            script_json = self._parse_script_json_response(result)
            if script_json:
                script_jsons.append(script_json)
            else:
                # Fallback: generate Java and convert to JSON
                print(f"  Warning: JSON parse failed, using fallback for scenario {i + 1}")
                java_code = self._generate_api_script_legacy(scenario, user_additional_input)
                script_json = java_to_json(java_code)
                script_jsons.append(script_json)
        
        return script_jsons
    
    def generate_ui_scripts_json_per_scenario(
        self,
        feature_json: Dict,
        user_additional_input: str = ""
    ) -> List[Dict]:
        """
        Generate UI automation scripts as JSON IR for each scenario.
        
        This is the recommended method for new implementations as it
        returns structured JSON that can be deterministically modified.
        
        Args:
            feature_json: JSON structure representing the feature file
            user_additional_input: Additional user instructions/context
        
        Returns:
            List[Dict]: List of script JSON objects, one per scenario
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        # Convert JSON to Gherkin
        feature_file = json_to_gherkin(feature_json)
        
        # Extract scenarios
        parser = GherkinScenarioParser()
        feature_file_scenarios = parser.parse(feature_file)
        
        prompt = ChatPromptTemplate.from_template("{SYSTEM_INSTRUCTION}")
        output_parser = StrOutputParser()
        chain = prompt | self.llm | output_parser
        
        script_jsons = []
        
        for i, scenario in enumerate(feature_file_scenarios):
            print(f"#-------------------- Generating JSON IR for UI Scenario {i + 1} -------------------#")
            
            result = chain.invoke({
                "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_UI_SCRIPT_JSON.format(
                    FEATURE_FILE=scenario,
                    USER_ADDITIONAL_INPUT=user_additional_input if user_additional_input.strip() else "(No additional user input provided)"
                )
            })
            
            # Parse JSON response
            script_json = self._parse_script_json_response(result)
            if script_json:
                script_jsons.append(script_json)
            else:
                # Fallback: generate Java and convert to JSON
                print(f"  Warning: JSON parse failed, using fallback for scenario {i + 1}")
                java_code = self._generate_ui_script_legacy(scenario, user_additional_input)
                script_json = java_to_json(java_code)
                script_jsons.append(script_json)
        
        return script_jsons
    
    def merge_script_jsons(
        self,
        script_jsons: List[Dict],
        merged_class_name: str = "GeneratedTests"
    ) -> Dict:
        """
        Merge multiple script JSONs into a single script JSON.
        
        This is a deterministic merge operation that:
        - Combines all imports (deduplicated)
        - Combines all fields (deduplicated by name)
        - Combines all methods
        
        Args:
            script_jsons: List of script JSON dictionaries
            merged_class_name: Name for the merged class
        
        Returns:
            Dict: Merged script JSON
        """
        return merge_script_jsons(script_jsons, merged_class_name)
    
    def script_json_to_java(self, script_json: Dict) -> str:
        """
        Convert a script JSON to Java code.
        
        Args:
            script_json: The script JSON to convert
            
        Returns:
            str: Formatted Java code
        """
        return json_to_java(script_json)
    
    def java_to_script_json(self, java_code: str) -> Dict:
        """
        Convert Java code to script JSON.
        
        Args:
            java_code: The Java code to parse
            
        Returns:
            Dict: Script JSON representation
        """
        return java_to_json(java_code)
    
    def chat_refine_script_json(
        self,
        current_script_json: Dict,
        chat_messages: List[Dict],
        user_message: str
    ) -> Tuple[str, str, str, Optional[Dict]]:
        """
        Chat-based refinement for automation scripts using JSON IR.
        
        This method uses deterministic JSON modifications when possible,
        falling back to LLM-based changes only for complex requests.
        
        Args:
            current_script_json: The current script as JSON
            chat_messages: List of previous chat messages for context
            user_message: The user's current message/request
        
        Returns:
            Tuple of (intent, reasoning, explanation, proposed_script_json):
            - intent: "question" or "change"
            - reasoning: LLM's thinking/reasoning tokens (from GPT-OSS)
            - explanation: Human-readable response
            - proposed_script_json: Updated JSON (None if question)
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        # Format chat history
        chat_history = self._format_script_chat_history(chat_messages)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template("{SYSTEM_INSTRUCTION}")
        
        # Use chain without StrOutputParser to preserve AIMessage with reasoning
        chain = prompt | self.llm
        
        # Invoke LLM to get modifications
        ai_message = chain.invoke({
            "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON.format(
                CURRENT_SCRIPT_JSON=json.dumps(current_script_json, indent=2),
                CHAT_HISTORY=chat_history,
                USER_MESSAGE=user_message
            )
        })
        
        # Extract content and reasoning from AIMessage
        result = ai_message.content
        reasoning = ai_message.additional_kwargs.get("reasoning_content", "")
        
        # Parse the JSON response
        try:
            result = self._clean_json_response(result)
            parsed = json.loads(result)
            
            intent = parsed.get("intent", "change")
            explanation = parsed.get("explanation", "I've processed your request.")
            modifications = parsed.get("modifications", [])
            
            if intent == "question" or not modifications:
                return (intent, reasoning, explanation, None)
            
            # Apply modifications deterministically
            modified_json = current_script_json
            for mod in modifications:
                try:
                    modified_json = apply_json_modification(modified_json, mod)
                except Exception as e:
                    print(f"Warning: Failed to apply modification {mod}: {e}")
            
            return ("change", reasoning, explanation, modified_json)
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error in chat_refine_script_json: {e}")
            print(f"Raw response: {result[:500]}...")
            
            # Fallback to complex modification
            return self._complex_script_modification_json(
                current_script_json, user_message
            )
    
    def _complex_script_modification_json(
        self,
        current_script_json: Dict,
        user_request: str
    ) -> Tuple[str, str, str, Optional[Dict]]:
        """
        Handle complex script modifications that can't be done deterministically.
        
        Uses LLM to generate the complete modified JSON.
        
        Returns:
            Tuple of (intent, reasoning, explanation, proposed_script_json)
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        prompt = ChatPromptTemplate.from_template("{SYSTEM_INSTRUCTION}")
        
        # Use chain without StrOutputParser to preserve AIMessage with reasoning
        chain = prompt | self.llm
        
        ai_message = chain.invoke({
            "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_COMPLEX_SCRIPT_MODIFICATION_JSON.format(
                CURRENT_SCRIPT_JSON=json.dumps(current_script_json, indent=2),
                USER_REQUEST=user_request
            )
        })
        
        # Extract content and reasoning
        result = ai_message.content
        reasoning = ai_message.additional_kwargs.get("reasoning_content", "")
        
        # Parse the result
        modified_json = self._parse_script_json_response(result)
        
        if modified_json:
            return (
                "change",
                reasoning,
                "I've made the requested complex modifications to the script.",
                modified_json
            )
        else:
            return (
                "change",
                reasoning,
                "I attempted to make the changes but encountered an issue. Please try rephrasing your request.",
                None
            )
    
    def _parse_script_json_response(self, response: str) -> Optional[Dict]:
        """Parse a JSON response from LLM, handling various formats."""
        try:
            response = self._clean_json_response(response)
            parsed = json.loads(response)
            
            # Validate the structure
            is_valid, errors = validate_script_json(parsed)
            if not is_valid:
                print(f"Script JSON validation errors: {errors}")
                # Still return it, might be usable
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse script JSON: {e}")
            print(f"Response: {response[:500]}...")
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """Clean a JSON response by removing markdown code blocks."""
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith("```"):
            response = re.sub(r'^```(?:json)?\s*', '', response)
            response = re.sub(r'\s*```$', '', response)
        
        return response.strip()
    
    def _generate_api_script_legacy(self, scenario: str, user_input: str) -> str:
        """Legacy method to generate API script as Java code."""
        prompt = ChatPromptTemplate.from_template(
            "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}\n\n{USER_ADDITIONAL_INPUT}"
        )
        output_parser = StrOutputParser()
        chain = prompt | self.llm | output_parser
        
        java_code = chain.invoke({
            "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT_PER_SCENARIO,
            "FEATURE_FILE": scenario,
            "USER_ADDITIONAL_INPUT": user_input if user_input.strip() else "(No additional user input provided)"
        })
        return self._clean_code_blocks(java_code)
    
    def _generate_ui_script_legacy(self, scenario: str, user_input: str) -> str:
        """Legacy method to generate UI script as Java code."""
        prompt = ChatPromptTemplate.from_template(
            "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}\n\n{USER_ADDITIONAL_INPUT}"
        )
        output_parser = StrOutputParser()
        chain = prompt | self.llm | output_parser
        
        java_code = chain.invoke({
            "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_UI_AUTOMATION_AGENT_PER_SCENARIO,
            "FEATURE_FILE": scenario,
            "USER_ADDITIONAL_INPUT": user_input if user_input.strip() else "(No additional user input provided)"
        })
        return self._clean_code_blocks(java_code)

    # ==================== Legacy Methods (Backward Compatibility) ====================
    
    def _format_script_chat_history(self, chat_messages: List[Dict]) -> str:
        """Format chat history for prompt context (last 5-6 messages)."""
        if not chat_messages:
            return "(No previous conversation)"
        
        # Take last 5-6 messages for context
        recent_messages = chat_messages[-6:]
        formatted = []
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n\n".join(formatted)
    
    def chat_refine_script(
        self,
        current_script: str,
        chat_messages: List[Dict],
        user_message: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Chat-based refinement for automation scripts (Legacy method).
        
        Provides a conversational interface for script modifications.
        User can ask questions about the script or request changes.
        
        Args:
            current_script: The current Java automation script
            chat_messages: List of previous chat messages for context
            user_message: The user's current message/request
        
        Returns:
            Tuple of (intent, explanation, proposed_script):
            - intent: "question" or "change"
            - explanation: Human-readable response
            - proposed_script: Complete updated Java code (None if question)
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        # Format chat history
        chat_history = self._format_script_chat_history(chat_messages)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(
            "{SYSTEM_INSTRUCTION}"
        )
        
        output_parser = StrOutputParser()
        chain = prompt | self.llm | output_parser
        
        # Invoke LLM
        result = chain.invoke({
            "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT.format(
                CURRENT_SCRIPT=current_script,
                CHAT_HISTORY=chat_history,
                USER_MESSAGE=user_message
            )
        })
        
        # Parse the JSON response
        try:
            # Clean up response
            result = result.strip()
            
            # Handle markdown code blocks
            if result.startswith("```"):
                # Remove ```json or ``` at start
                result = re.sub(r'^```(?:json)?\s*', '', result)
                # Remove ``` at end
                result = re.sub(r'\s*```$', '', result)
            
            parsed = json.loads(result)
            
            intent = parsed.get("intent", "change")
            explanation = parsed.get("explanation", "I've processed your request.")
            proposed_script = parsed.get("proposed_script")
            
            # Clean code blocks from proposed script if present
            if proposed_script:
                proposed_script = self._clean_code_blocks(proposed_script)
            
            return (intent, explanation, proposed_script)
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to extract information
            print(f"JSON parse error in chat_refine_script: {e}")
            print(f"Raw response: {result[:500]}...")
            
            # Default to treating as a change with the raw response
            return (
                "change",
                "I've attempted to process your request, but encountered a formatting issue. Please try rephrasing.",
                None
            )

    def refactor_script_with_feedback(
        self,
        generated_java_class: str,
        user_feedback: str
    ) -> Tuple[str, str]:
        """
        Refactor generated Java automation script based on user feedback using hybrid approach.
        
        Workflow:
        1. Extract intent from feedback (LLM call)
        2. Apply targeted changes using pattern matching (deterministic)
        3. Generate accurate diff using Python difflib
        4. Return diff and refactored code
        
        Args:
            generated_java_class: Original Java code
            user_feedback: User's refactoring request
        
        Returns:
            Tuple[str, str]: (diff_output, refactored_java_code)
        """
        try:
            # Step 1: Extract intent from feedback
            intent = self.extract_refactoring_intent(user_feedback, generated_java_class)
            
            # Step 2: Apply changes based on intent
            if intent.get("type") == "multiple":
                # Handle multiple changes
                refactored_code = generated_java_class
                for change in intent.get("changes", []):
                    refactored_code = self._apply_refactoring_change(refactored_code, change)
            else:
                # Handle single change
                refactored_code = self._apply_refactoring_change(generated_java_class, intent)
            
            # Step 3: Generate accurate diff
            diff_output = self.generate_unified_diff(generated_java_class, refactored_code)
            
            return (diff_output, refactored_code)
        
        except Exception as e:
            # Fallback to direct LLM refactoring if pattern matching fails
            print(f"Pattern-based refactoring failed: {e}. Falling back to LLM refactoring.")
            return self._fallback_llm_refactoring(generated_java_class, user_feedback)
    
    def extract_refactoring_intent(self, user_feedback: str, java_code: str) -> Dict:
        """
        Extract structured intent from user feedback using LLM.
        
        Args:
            user_feedback: User's feedback text
            java_code: The Java code being refactored (for context)
        
        Returns:
            Dict with structure: {"type": "...", "old_value": "...", "new_value": "...", "context": "..."}
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        prompt_intent_extraction = ChatPromptTemplate.from_template(
            "{SYSTEM_INSTRUCTION}\n\n"
            "USER FEEDBACK:\n{USER_FEEDBACK}\n\n"
            "JAVA CODE CONTEXT (first 50 lines):\n{JAVA_CODE_CONTEXT}"
        )
        
        output_parser = StrOutputParser()
        intent_chain = prompt_intent_extraction | self.llm | output_parser
        
        # Provide limited context to avoid token overflow
        code_context = "\n".join(java_code.split("\n")[:50])
        
        result = intent_chain.invoke({
            "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_INTENT_EXTRACTION,
            "USER_FEEDBACK": user_feedback,
            "JAVA_CODE_CONTEXT": code_context
        })
        
        # Parse JSON response
        intent = self._parse_json_response(
            result,
            fallback={
                "type": "update_string",
                "old_value": "",
                "new_value": "",
                "context": user_feedback
            }
        )
        
        return intent
    
    def generate_unified_diff(
        self,
        original: str,
        modified: str,
        filename: str = "JavaClass.java"
    ) -> str:
        """
        Generate a unified diff between original and modified code.
        
        Args:
            original: Original code string
            modified: Modified code string
            filename: Name to use in diff header
        
        Returns:
            Formatted unified diff string
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        diff_text = ''.join(diff)
        
        # If no changes, return a message
        if not diff_text:
            return "No changes detected."
        
        return diff_text
    
    # ==================== Private Helper Methods ====================
    
    def _apply_refactoring_change(self, java_code: str, change: Dict) -> str:
        """
        Apply a single refactoring change to Java code using pattern matching.
        
        Args:
            java_code: The Java code to refactor
            change: Dict with change details (type, old_value, new_value, context)
        
        Returns:
            str: Refactored Java code
        
        Raises:
            ValueError: If change type is unknown (triggers fallback)
        """
        change_type = change.get("type", "")
        old_value = change.get("old_value", "")
        new_value = change.get("new_value", "")
        
        if change_type == "rename_class":
            return self._apply_rename_class(java_code, old_value, new_value)
        
        elif change_type == "rename_method":
            return self._apply_rename_method(java_code, old_value, new_value)
        
        elif change_type == "rename_variable":
            return self._apply_rename_variable(java_code, old_value, new_value)
        
        elif change_type == "remove_code":
            return self._apply_remove_code(java_code, old_value)
        
        elif change_type == "add_import":
            return self._apply_add_import(java_code, new_value)
        
        elif change_type == "remove_import":
            return self._apply_remove_import(java_code, old_value)
        
        elif change_type == "snake_to_camel":
            return self._apply_snake_to_camel_case(java_code)
        
        elif change_type == "camel_to_snake":
            return self._apply_camel_to_snake_case(java_code)
        
        elif change_type == "update_string":
            # Generic string replacement
            if old_value:
                return java_code.replace(old_value, new_value)
            return java_code
        
        elif change_type == "complex":
            # Explicitly marked as complex - raise exception to trigger LLM fallback
            raise ValueError(f"Complex refactoring detected. Using LLM fallback.")
        
        else:
            # Unknown type - raise exception to trigger fallback
            raise ValueError(f"Unknown change type: {change_type}. Falling back to LLM refactoring.")
    
    def _apply_rename_class(self, code: str, old_name: str, new_name: str) -> str:
        """Rename Java class and all its references."""
        if not old_name or not new_name:
            return code
        
        # Replace class declaration
        code = re.sub(
            rf'\bpublic\s+class\s+{re.escape(old_name)}\s*\{{',
            f'public class {new_name} {{',
            code
        )
        
        # Replace constructor
        code = re.sub(
            rf'\bpublic\s+{re.escape(old_name)}\s*\(',
            f'public {new_name}(',
            code
        )
        
        # Replace logger reference
        code = re.sub(
            rf'getLogger\s*\(\s*{re.escape(old_name)}\.class\s*\)',
            f'getLogger({new_name}.class)',
            code
        )
        
        # Replace any other references (static calls, etc.)
        code = re.sub(
            rf'\b{re.escape(old_name)}\.',
            f'{new_name}.',
            code
        )
        
        return code
    
    def _apply_rename_method(self, code: str, old_name: str, new_name: str) -> str:
        """Rename a Java method."""
        if not old_name or not new_name:
            return code
        
        # Replace method declaration (handles various access modifiers)
        code = re.sub(
            rf'\b(public|private|protected|static|\s)+\s+\w+\s+{re.escape(old_name)}\s*\(',
            lambda m: m.group(0).replace(old_name, new_name),
            code
        )
        
        # Replace method calls
        code = re.sub(
            rf'\b{re.escape(old_name)}\s*\(',
            f'{new_name}(',
            code
        )
        
        return code
    
    def _apply_rename_variable(self, code: str, old_name: str, new_name: str) -> str:
        """Rename a Java variable or field."""
        if not old_name or not new_name:
            return code
        
        # Replace variable declarations and usages (word boundary aware)
        code = re.sub(
            rf'\b{re.escape(old_name)}\b',
            new_name,
            code
        )
        
        return code
    
    def _apply_remove_code(self, code: str, code_to_remove: str) -> str:
        """Remove specific code from Java file."""
        if not code_to_remove:
            return code
        
        # Try exact match first
        if code_to_remove in code:
            return code.replace(code_to_remove, '')
        
        # Try removing leading/trailing whitespace variations
        lines = code.split('\n')
        filtered_lines = [line for line in lines if code_to_remove.strip() not in line]
        
        return '\n'.join(filtered_lines)
    
    def _apply_add_import(self, code: str, import_statement: str) -> str:
        """Add import statement to Java file."""
        if not import_statement:
            return code
        
        # Ensure import starts with 'import' and ends with ';'
        if not import_statement.startswith('import'):
            import_statement = f'import {import_statement}'
        if not import_statement.endswith(';'):
            import_statement = f'{import_statement};'
        
        # Find the last import statement
        lines = code.split('\n')
        last_import_idx = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                last_import_idx = i
        
        # Insert after last import
        if last_import_idx >= 0:
            lines.insert(last_import_idx + 1, import_statement)
        else:
            # No imports found, add after package declaration
            for i, line in enumerate(lines):
                if line.strip().startswith('package '):
                    lines.insert(i + 1, '\n' + import_statement)
                    break
        
        return '\n'.join(lines)
    
    def _apply_remove_import(self, code: str, import_to_remove: str) -> str:
        """Remove import statement from Java file."""
        if not import_to_remove:
            return code
        
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Skip lines that contain the import to remove
            if 'import' in line and import_to_remove in line:
                continue
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _apply_snake_to_camel_case(self, code: str) -> str:
        """Convert all snake_case identifiers to camelCase in Java code."""
        
        def snake_to_camel(match):
            """Convert a snake_case match to camelCase."""
            snake_str = match.group(0)
            # Split by underscore and capitalize each word except first
            components = snake_str.split('_')
            # Keep first component lowercase, capitalize rest
            return components[0] + ''.join(x.capitalize() for x in components[1:])
        
        # Pattern to match snake_case identifiers (variable names, method names, etc.)
        # Matches: word_word, word_word_word, etc.
        # Avoids matching: CONSTANTS (all caps), package names, imports
        pattern = r'\b([a-z][a-z0-9]*_[a-z0-9_]+)\b'
        
        # Convert all snake_case to camelCase
        converted_code = re.sub(pattern, snake_to_camel, code)
        
        return converted_code
    
    def _apply_camel_to_snake_case(self, code: str) -> str:
        """Convert all camelCase identifiers to snake_case in Java code."""
        
        def camel_to_snake(match):
            """Convert a camelCase match to snake_case."""
            camel_str = match.group(0)
            # Insert underscore before uppercase letters and convert to lowercase
            snake_str = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
            return snake_str
        
        # Pattern to match camelCase identifiers
        # Matches: camelCase, camelCaseWord, etc.
        # Avoids matching: ClassName (PascalCase), CONSTANTS
        pattern = r'\b([a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*)\b'
        
        # Convert all camelCase to snake_case
        converted_code = re.sub(pattern, camel_to_snake, code)
        
        return converted_code
    
    def _fallback_llm_refactoring(
        self,
        generated_java_class: str,
        user_feedback: str
    ) -> Tuple[str, str]:
        """
        Fallback to direct LLM refactoring when pattern-based approach fails.
        
        Returns:
            Tuple[str, str]: (diff_output, refactored_code)
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        prompt_fallback = ChatPromptTemplate.from_template(
            "{SYSTEM_INSTRUCTION}\n\n"
            "ORIGINAL CLASS:\n{ORIGINAL_JAVA_CLASS}\n\n"
            "USER FEEDBACK:\n{USER_FEEDBACK}"
        )
        
        output_parser = StrOutputParser()
        fallback_chain = prompt_fallback | self.llm | output_parser
        
        refactored_code = fallback_chain.invoke({
            "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_FALLBACK_REFACTORING,
            "ORIGINAL_JAVA_CLASS": generated_java_class,
            "USER_FEEDBACK": user_feedback
        })
        
        # Clean up output
        refactored_code = self._clean_code_blocks(refactored_code)
        
        # Generate diff
        diff_output = self.generate_unified_diff(generated_java_class, refactored_code)
        
        return (diff_output, refactored_code)
