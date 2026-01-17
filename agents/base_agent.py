"""
Base Agent class providing common LLM interaction functionality.
All specific agents inherit from this class.
"""

import json
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class BaseAgent:
    """
    Base class for all agents providing common LLM interaction methods.
    
    All agents should inherit from this class to get:
    - LLM instance management
    - JSON parsing with error handling
    - Prompt template execution
    - Output parsing
    """
    
    def __init__(self, llm: Optional[ChatGroq] = None):
        """
        Initialize the base agent.
        
        Args:
            llm: Optional ChatGroq instance. If None, will use the global llm from utils.
        """
        if llm is None:
            from utils.llm_config import get_llm
            try:
                self.llm = get_llm()
            except ValueError:
                self.llm = None
        else:
            self.llm = llm
    
    def update_llm(self, llm: ChatGroq):
        """
        Update the LLM instance.
        
        Args:
            llm: New ChatGroq instance
        """
        self.llm = llm
    
    def _execute_prompt(self, system_instruction: str, variables: Dict[str, Any]) -> str:
        """
        Execute a prompt with given system instruction and variables.
        
        Args:
            system_instruction: The system instruction/prompt template
            variables: Dictionary of variables to substitute in the prompt
        
        Returns:
            str: Raw string output from LLM
        
        Raises:
            ValueError: If LLM is not initialized
        """
        if self.llm is None:
            raise ValueError("LLM not initialized. Please provide a valid API key.")
        
        # Create prompt template with all variables
        template_vars = "\n\n".join([f"{{{key}}}" for key in variables.keys()])
        prompt = ChatPromptTemplate.from_template(
            f"{{SYSTEM_INSTRUCTION}}\n\n{template_vars}"
        )
        
        output_parser = StrOutputParser()
        chain = prompt | self.llm | output_parser
        
        # Add system instruction to variables
        all_vars = {"SYSTEM_INSTRUCTION": system_instruction, **variables}
        
        result = chain.invoke(all_vars)
        return result.strip()
    
    def _parse_json_response(self, response: str, fallback: Optional[Dict] = None) -> Dict:
        """
        Parse JSON response from LLM, handling common formatting issues.
        
        Args:
            response: Raw response string from LLM
            fallback: Optional fallback dictionary if parsing fails
        
        Returns:
            Dict: Parsed JSON data
        """
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        try:
            json_data = json.loads(response)
            return json_data
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from LLM: {e}")
            print(f"Raw result: {response[:200]}...")
            
            if fallback is not None:
                return fallback
            
            # Return minimal valid structure as default fallback
            return {
                "feature": {"name": "Error parsing response"},
                "scenarios": []
            }
    
    def _clean_code_blocks(self, text: str) -> str:
        """
        Remove markdown code block markers from text.
        
        Args:
            text: Text potentially containing code blocks
        
        Returns:
            str: Cleaned text
        """
        text = text.strip()
        
        # Remove language-specific code blocks
        for lang in ["java", "python", "javascript", "json", "gherkin"]:
            if text.startswith(f"```{lang}"):
                text = text[len(f"```{lang}"):]
                break
        
        # Remove generic code blocks
        if text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()
