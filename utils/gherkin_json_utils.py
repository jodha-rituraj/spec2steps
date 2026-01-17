"""
Utility functions for converting between JSON and Gherkin formats.
This module enables structured, surgical edits to test scenarios.
"""

import json
from typing import Dict, List, Optional, Any


def normalize_feature_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a feature JSON structure to ensure consistent format.
    Fixes common LLM output inconsistencies like:
    - description as list instead of string
    - examples as list instead of dict with headers/rows
    
    Args:
        json_data: Dictionary containing feature structure (may have inconsistencies)
        
    Returns:
        Normalized dictionary with consistent structure
    """
    if not isinstance(json_data, dict):
        return json_data
    
    normalized = json_data.copy()
    
    # Normalize feature section
    if "feature" in normalized and isinstance(normalized["feature"], dict):
        feature = normalized["feature"]
        
        # Ensure description is a string
        if "description" in feature:
            desc = feature["description"]
            if isinstance(desc, list):
                feature["description"] = "\n".join(str(item) for item in desc)
            elif not isinstance(desc, str):
                feature["description"] = str(desc) if desc else ""
        
        # Ensure tags is a list
        if "tags" in feature and not isinstance(feature["tags"], list):
            feature["tags"] = [feature["tags"]] if feature["tags"] else []
    
    # Normalize scenarios
    if "scenarios" in normalized and isinstance(normalized["scenarios"], list):
        for scenario in normalized["scenarios"]:
            if not isinstance(scenario, dict):
                continue
            
            # Ensure tags is a list
            if "tags" in scenario and not isinstance(scenario["tags"], list):
                scenario["tags"] = [scenario["tags"]] if scenario["tags"] else []
            
            # Normalize examples
            if "examples" in scenario:
                examples = scenario["examples"]
                
                if isinstance(examples, list):
                    # Convert list format to dict format
                    if examples and isinstance(examples[0], dict):
                        # List of dicts: [{"col1": "val1", "col2": "val2"}, ...]
                        headers = list(examples[0].keys())
                        rows = [[row.get(h, "") for h in headers] for row in examples]
                        scenario["examples"] = {"headers": headers, "rows": rows}
                    elif examples and isinstance(examples[0], list):
                        # List of lists: [["header1", "header2"], ["val1", "val2"], ...]
                        headers = examples[0] if len(examples) > 0 else []
                        rows = examples[1:] if len(examples) > 1 else []
                        scenario["examples"] = {"headers": headers, "rows": rows}
                elif isinstance(examples, dict):
                    # Already correct format, just ensure keys exist
                    if "headers" not in examples:
                        examples["headers"] = []
                    if "rows" not in examples:
                        examples["rows"] = []
    
    # Normalize background
    if "background" in normalized and isinstance(normalized["background"], dict):
        bg = normalized["background"]
        if "steps" not in bg:
            bg["steps"] = []
    
    return normalized


def json_to_gherkin(json_data: Dict[str, Any]) -> str:
    """
    Convert JSON structure to Gherkin feature file format.
    
    Args:
        json_data: Dictionary containing feature structure
        
    Returns:
        String containing properly formatted Gherkin feature file
    """
    # Normalize the JSON data first to handle LLM inconsistencies
    json_data = normalize_feature_json(json_data)
    
    lines = []
    
    # Feature header
    feature = json_data.get("feature", {})
    feature_name = feature.get("name", "Untitled Feature")
    
    # Add tags if present
    tags = feature.get("tags", [])
    if tags:
        lines.append(" ".join(tags))
    
    lines.append(f"Feature: {feature_name}")
    
    # Add feature description if present
    # Note: normalize_feature_json already converts description to string
    description = feature.get("description", "")
    if description:
        lines.append("")
        for line in str(description).split("\n"):
            lines.append(f"  {line}" if line.strip() else "")
    
    # Background section
    background = json_data.get("background")
    if background:
        lines.append("")
        lines.append("  Background:")
        steps = background.get("steps", [])
        for step in steps:
            step_type = step.get("type", "Given")
            step_text = step.get("text", "")
            lines.append(f"    {step_type} {step_text}")
    
    # Scenarios
    scenarios = json_data.get("scenarios", [])
    for scenario in scenarios:
        lines.append("")
        
        # Scenario tags
        scenario_tags = scenario.get("tags", [])
        if scenario_tags:
            lines.append(f"  {' '.join(scenario_tags)}")
        
        # Scenario type and name
        scenario_type = scenario.get("type", "Scenario")
        scenario_name = scenario.get("name", "Untitled Scenario")
        lines.append(f"  {scenario_type}: {scenario_name}")
        
        # Steps
        steps = scenario.get("steps", [])
        for step in steps:
            step_type = step.get("type", "Given")
            step_text = step.get("text", "")
            lines.append(f"    {step_type} {step_text}")
        
        # Examples (for Scenario Outline)
        # Note: normalize_feature_json already converts examples to standard format
        examples = scenario.get("examples")
        if examples and isinstance(examples, dict):
            lines.append("")
            lines.append("    Examples:")
            
            headers = examples.get("headers", [])
            if headers:
                header_line = " | ".join(str(h) for h in headers)
                lines.append(f"      | {header_line} |")
            
            rows = examples.get("rows", [])
            for row in rows:
                row_line = " | ".join(str(val) for val in row)
                lines.append(f"      | {row_line} |")
    
    return "\n".join(lines)


def gherkin_to_json(gherkin_text: str) -> Dict[str, Any]:
    """
    Convert Gherkin feature file to JSON structure.
    This is a basic parser for converting existing Gherkin to JSON.
    
    Args:
        gherkin_text: String containing Gherkin feature file
        
    Returns:
        Dictionary containing structured feature data
    """
    lines = gherkin_text.split("\n")
    json_data = {
        "feature": {},
        "scenarios": []
    }
    
    current_section = None
    current_scenario = None
    current_examples = None
    feature_tags = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Tags
        if line.startswith("@"):
            tags = line.split()
            if current_scenario is None:
                feature_tags = tags
            else:
                if "tags" not in current_scenario:
                    current_scenario["tags"] = []
                current_scenario["tags"].extend(tags)
            i += 1
            continue
        
        # Feature
        if line.startswith("Feature:"):
            feature_name = line.replace("Feature:", "").strip()
            json_data["feature"]["name"] = feature_name
            if feature_tags:
                json_data["feature"]["tags"] = feature_tags
            
            # Collect feature description
            description_lines = []
            i += 1
            while i < len(lines):
                desc_line = lines[i].strip()
                if desc_line and not desc_line.startswith("Background:") and not desc_line.startswith("Scenario"):
                    description_lines.append(desc_line)
                    i += 1
                else:
                    break
            
            if description_lines:
                json_data["feature"]["description"] = "\n".join(description_lines)
            continue
        
        # Background
        if line.startswith("Background:"):
            current_section = "background"
            json_data["background"] = {"steps": []}
            i += 1
            continue
        
        # Scenario or Scenario Outline
        if line.startswith("Scenario:") or line.startswith("Scenario Outline:"):
            current_section = "scenario"
            current_scenario = {
                "id": f"scenario_{len(json_data['scenarios']) + 1}",
                "type": "Scenario Outline" if "Outline" in line else "Scenario",
                "name": line.split(":", 1)[1].strip(),
                "steps": []
            }
            json_data["scenarios"].append(current_scenario)
            i += 1
            continue
        
        # Examples
        if line.startswith("Examples:"):
            current_section = "examples"
            current_examples = {"headers": [], "rows": []}
            current_scenario["examples"] = current_examples
            i += 1
            continue
        
        # Steps (Given, When, Then, And, But)
        step_keywords = ["Given", "When", "Then", "And", "But"]
        is_step = any(line.startswith(keyword) for keyword in step_keywords)
        
        if is_step:
            for keyword in step_keywords:
                if line.startswith(keyword):
                    step_text = line.replace(keyword, "", 1).strip()
                    step = {"type": keyword, "text": step_text}
                    
                    if current_section == "background":
                        json_data["background"]["steps"].append(step)
                    elif current_section == "scenario" and current_scenario:
                        current_scenario["steps"].append(step)
                    break
            i += 1
            continue
        
        # Example table rows
        if line.startswith("|") and current_section == "examples":
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if not current_examples["headers"]:
                current_examples["headers"] = cells
            else:
                current_examples["rows"].append(cells)
            i += 1
            continue
        
        i += 1
    
    return json_data


def validate_gherkin_json(json_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate JSON structure for Gherkin feature.
    
    Args:
        json_data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check feature
    if "feature" not in json_data:
        errors.append("Missing 'feature' key in JSON")
    else:
        feature = json_data["feature"]
        if "name" not in feature:
            errors.append("Feature must have a 'name'")
    
    # Check scenarios
    if "scenarios" not in json_data:
        errors.append("Missing 'scenarios' key in JSON")
    elif not isinstance(json_data["scenarios"], list):
        errors.append("'scenarios' must be a list")
    else:
        for idx, scenario in enumerate(json_data["scenarios"]):
            if "name" not in scenario:
                errors.append(f"Scenario {idx + 1} missing 'name'")
            if "steps" not in scenario:
                errors.append(f"Scenario {idx + 1} missing 'steps'")
            elif not isinstance(scenario["steps"], list):
                errors.append(f"Scenario {idx + 1} 'steps' must be a list")
            else:
                for step_idx, step in enumerate(scenario["steps"]):
                    if "type" not in step:
                        errors.append(f"Scenario {idx + 1}, step {step_idx + 1} missing 'type'")
                    if "text" not in step:
                        errors.append(f"Scenario {idx + 1}, step {step_idx + 1} missing 'text'")
    
    return len(errors) == 0, errors


# JSON Schema definition for reference
GHERKIN_JSON_SCHEMA = {
    "feature": {
        "name": "string (required)",
        "description": "string (optional)",
        "tags": ["@tag1", "@tag2"] # (optional)
    },
    "background": { # (optional)
        "steps": [
            {"type": "Given|When|Then|And|But", "text": "step text"}
        ]
    },
    "scenarios": [
        {
            "id": "unique_id (auto-generated)",
            "type": "Scenario|Scenario Outline",
            "name": "Scenario name (required)",
            "tags": ["@tag1"], # (optional)
            "steps": [
                {"type": "Given|When|Then|And|But", "text": "step text"}
            ],
            "examples": { # (optional, only for Scenario Outline)
                "headers": ["column1", "column2"],
                "rows": [
                    ["value1", "value2"],
                    ["value3", "value4"]
                ]
            }
        }
    ]
}
