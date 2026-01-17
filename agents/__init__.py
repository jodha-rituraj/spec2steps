"""
Agents Package - Contains all AI agents for test automation generation.

This package provides a clean, class-based architecture for:
- Requirement processing and feature file generation
- Feature file verification and validation
- Automation script generation and refactoring

All agents inherit from BaseAgent for consistent LLM interaction.
"""

from .base_agent import BaseAgent
from .requirement_agent import RequirementAgent
from .verification_agent import VerificationAgent
from .automation_script_agent import AutomationScriptAgent

__all__ = [
    'BaseAgent',
    'RequirementAgent',
    'VerificationAgent',
    'AutomationScriptAgent',
]
