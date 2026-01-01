import streamlit as st

import os, groq, langchain_groq, json, re, tempfile
from dotenv import load_dotenv
from utils.llm_config import get_llm

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import difflib
from typing import List, Set, Dict, Tuple

from llm_prompts.requirement_agent import SYSTEM_INSTRUCTION_REQ_AGENT, SYSTEM_INSTRUCTION_FEEDBACK_AGENT
from llm_prompts.verification_agent import SYSTEM_INSTRUCTION_VERIFICATION_AGENT
from llm_prompts.java_automation_script_agent import SYSTEM_INSTRUCTION_AUTOMATION_AGENT, SYSTEM_INSTRUCTION_AUTOMATION_AGENT_PER_SCENARIO
from llm_prompts.java_automation_feedback_agent import SYSTEM_INSTRUCTION_INTENT_EXTRACTION, SYSTEM_INSTRUCTION_FALLBACK_REFACTORING

from features.parser import GherkinScenarioParser, extractScenarioOulines
from features.merger import JavaFileMerger

# Initialize LLM - will be updated when API key changes
llm = get_llm()

def generateFeatureFile(inputRequirement: str) -> str:
    
    prompt = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{INPUT_REQUIREMENTS}"
    )

    outputParser = StrOutputParser()

    chain = prompt | llm | outputParser

    result = chain.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_REQ_AGENT,
    "INPUT_REQUIREMENTS": inputRequirement})

    return result

def refineFeatureFileWithFeedback(
    original_feature_file: str,
    verification_feedback: str = "",
    user_feedback: str = ""
) -> str:
    """Refine existing feature file based on feedback"""
    
    # Construct feedback context
    feedback_parts = []
    
    if verification_feedback.strip():
        feedback_parts.append(f"VERIFICATION FEEDBACK:\n{verification_feedback}")
    
    if user_feedback.strip():
        feedback_parts.append(f"USER FEEDBACK:\n{user_feedback}")
    
    combined_feedback = "\n\n".join(feedback_parts)
    
    prompt = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}\n\n"
        "ORIGINAL FEATURE FILE:\n{ORIGINAL_FEATURE_FILE}\n\n"
        "{FEEDBACK}"
    )
    
    outputParser = StrOutputParser()
    chain = prompt | llm | outputParser
    
    result = chain.invoke({
        "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_FEEDBACK_AGENT,
        "ORIGINAL_FEATURE_FILE": original_feature_file,
        "FEEDBACK": combined_feedback
    })
    
    return result

def generateVerificationOutput(inputRequirement: str, featureFile: str) -> str:
    promptVerificationAgent = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n {INPUT_REQUIREMENTS} GENERATED FEATURE FILE:\n {FEATURE_FILE}"
    )
    outputParser = StrOutputParser()
    verificationChain = promptVerificationAgent | llm | outputParser
    
    verificationResult = verificationChain.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_VERIFICATION_AGENT,
    "INPUT_REQUIREMENTS": inputRequirement,
    "FEATURE_FILE": featureFile})

    return verificationResult

def generateAutomationScripts(featureFile: str) -> str:
    promptAutomationScript = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}"
    )
    outputParser = StrOutputParser()
    chainAutomation = promptAutomationScript | llm | outputParser

    automationScript = chainAutomation.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT,
    "FEATURE_FILE": featureFile})

    return automationScript

def generateAutomationScriptsPerScenario(featureFileScenarios: str, userAdditionalInput: str = "") -> List[str]:
    promptAutomationScript = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}\n\n{USER_ADDITIONAL_INPUT}"
    )
    outputParser = StrOutputParser()
    chainAutomation = promptAutomationScript | llm | outputParser

    javaCodeFiles = []

    for i, scenario in enumerate(featureFileScenarios):
        print(f"#-------------------- Generating Java Code for Scenario {i + 1} -------------------#")
        javaCode = chainAutomation.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT_PER_SCENARIO,
            "FEATURE_FILE": scenario,
            "USER_ADDITIONAL_INPUT": userAdditionalInput if userAdditionalInput.strip() else "(No additional user input provided)"})
        javaCodeFiles.append(javaCode)

    return javaCodeFiles

def refactorAutomationScriptWithFeedback(generatedJavaClass: str, userFeedback: str) -> Tuple[str, str]:
    """
    Refactor generated Java automation script based on user feedback using hybrid approach.
    
    Workflow:
    1. Extract intent from feedback (LLM call)
    2. Apply targeted changes using pattern matching (deterministic)
    3. Generate accurate diff using Python difflib
    4. Return diff and refactored code
    
    Args:
        generatedJavaClass: Original Java code
        userFeedback: User's refactoring request
        
    Returns:
        Tuple[str, str]: (diff_output, refactored_java_code)
    """
    try:
        # Step 1: Extract intent from feedback
        intent = extract_refactoring_intent(userFeedback, generatedJavaClass)
        
        # Step 2: Apply changes based on intent
        if intent.get("type") == "multiple":
            # Handle multiple changes
            refactored_code = generatedJavaClass
            for change in intent.get("changes", []):
                refactored_code = apply_refactoring_change(refactored_code, change)
        else:
            # Handle single change
            refactored_code = apply_refactoring_change(generatedJavaClass, intent)
        
        # Step 3: Generate accurate diff
        diff_output = generate_unified_diff(generatedJavaClass, refactored_code)
        
        return (diff_output, refactored_code)
        
    except Exception as e:
        # Fallback to direct LLM refactoring if pattern matching fails
        print(f"Pattern-based refactoring failed: {e}. Falling back to LLM refactoring.")
        return fallback_llm_refactoring(generatedJavaClass, userFeedback)


def extract_refactoring_intent(userFeedback: str, javaCode: str) -> Dict:
    """
    Extract structured intent from user feedback using LLM.
    
    Args:
        userFeedback: User's feedback text
        javaCode: The Java code being refactored (for context)
        
    Returns:
        Dict with structure: {"type": "...", "old_value": "...", "new_value": "...", "context": "..."}
    """
    promptIntentExtraction = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}\n\n"
        "USER FEEDBACK:\n{USER_FEEDBACK}\n\n"
        "JAVA CODE CONTEXT (first 50 lines):\n{JAVA_CODE_CONTEXT}"
    )
    
    outputParser = StrOutputParser()
    intentChain = promptIntentExtraction | llm | outputParser
    
    # Provide limited context to avoid token overflow
    code_context = "\n".join(javaCode.split("\n")[:50])
    
    result = intentChain.invoke({
        "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_INTENT_EXTRACTION,
        "USER_FEEDBACK": userFeedback,
        "JAVA_CODE_CONTEXT": code_context
    })
    
    # Parse JSON response
    result = result.strip()
    
    # Remove markdown code blocks if present
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    result = result.strip()
    
    try:
        intent = json.loads(result)
        return intent
    except json.JSONDecodeError as e:
        print(f"Failed to parse intent JSON: {e}")
        print(f"Raw result: {result}")
        # Return a generic update_string intent as fallback
        return {
            "type": "update_string",
            "old_value": "",
            "new_value": "",
            "context": userFeedback
        }


def apply_refactoring_change(javaCode: str, change: Dict) -> str:
    """
    Apply a single refactoring change to Java code using pattern matching.
    
    Args:
        javaCode: The Java code to refactor
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
        return apply_rename_class(javaCode, old_value, new_value)
    
    elif change_type == "rename_method":
        return apply_rename_method(javaCode, old_value, new_value)
    
    elif change_type == "rename_variable":
        return apply_rename_variable(javaCode, old_value, new_value)
    
    elif change_type == "remove_code":
        return apply_remove_code(javaCode, old_value)
    
    elif change_type == "add_import":
        return apply_add_import(javaCode, new_value)
    
    elif change_type == "remove_import":
        return apply_remove_import(javaCode, old_value)
    
    elif change_type == "snake_to_camel":
        return apply_snake_to_camel_case(javaCode)
    
    elif change_type == "camel_to_snake":
        return apply_camel_to_snake_case(javaCode)
    
    elif change_type == "update_string":
        # Generic string replacement
        if old_value:
            return javaCode.replace(old_value, new_value)
        return javaCode
    
    elif change_type == "complex":
        # Explicitly marked as complex - raise exception to trigger LLM fallback
        raise ValueError(f"Complex refactoring detected. Using LLM fallback.")
    
    else:
        # Unknown type - raise exception to trigger fallback
        raise ValueError(f"Unknown change type: {change_type}. Falling back to LLM refactoring.")


def apply_rename_class(code: str, old_name: str, new_name: str) -> str:
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


def apply_rename_method(code: str, old_name: str, new_name: str) -> str:
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


def apply_rename_variable(code: str, old_name: str, new_name: str) -> str:
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


def apply_remove_code(code: str, code_to_remove: str) -> str:
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


def apply_add_import(code: str, import_statement: str) -> str:
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


def apply_remove_import(code: str, import_to_remove: str) -> str:
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


def apply_snake_to_camel_case(code: str) -> str:
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


def apply_camel_to_snake_case(code: str) -> str:
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


def fallback_llm_refactoring(generatedJavaClass: str, userFeedback: str) -> Tuple[str, str]:
    """
    Fallback to direct LLM refactoring when pattern-based approach fails.
    
    Returns:
        Tuple[str, str]: (diff_output, refactored_code)
    """
    promptFallback = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}\n\n"
        "ORIGINAL CLASS:\n{ORIGINAL_JAVA_CLASS}\n\n"
        "USER FEEDBACK:\n{USER_FEEDBACK}"
    )
    
    outputParser = StrOutputParser()
    fallbackChain = promptFallback | llm | outputParser
    
    refactored_code = fallbackChain.invoke({
        "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_FALLBACK_REFACTORING,
        "ORIGINAL_JAVA_CLASS": generatedJavaClass,
        "USER_FEEDBACK": userFeedback
    })
    
    # Clean up output
    refactored_code = refactored_code.strip()
    if refactored_code.startswith("```java"):
        refactored_code = refactored_code[7:]
    if refactored_code.startswith("```"):
        refactored_code = refactored_code[3:]
    if refactored_code.endswith("```"):
        refactored_code = refactored_code[:-3]
    refactored_code = refactored_code.strip()
    
    # Generate diff
    diff_output = generate_unified_diff(generatedJavaClass, refactored_code)
    
    return (diff_output, refactored_code)


def generate_unified_diff(original: str, modified: str, filename: str = "JavaClass.java") -> str:
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


