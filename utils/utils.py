"""
Utility functions for the AI Test Automation Generator.

⚠️ DEPRECATION NOTICE ⚠️

This module previously contained all agent-related functions. These have been refactored
into a clean, class-based architecture in the agents/ package:

- RequirementAgent: Feature file generation and refinement (API & UI)
- VerificationAgent: Feature file verification and validation
- AutomationScriptAgent: Script generation, refactoring, and code transformations

Usage:
    from agents import RequirementAgent, VerificationAgent, AutomationScriptAgent
    
    # Initialize agents
    req_agent = RequirementAgent()
    ver_agent = VerificationAgent()
    auto_agent = AutomationScriptAgent()
    
    # Use agent methods
    feature_json = req_agent.generate_api_feature_file(requirements)
    verification = ver_agent.verify_feature_file(requirements, feature_json)
    scripts = auto_agent.generate_api_scripts_per_scenario(feature_json)

This file is kept for backward compatibility but should not be used in new code.
All agent functions have been moved to the agents/ package.
"""

# No functions in this module anymore - all functionality moved to agents/
__all__ = []
