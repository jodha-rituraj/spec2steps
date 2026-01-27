"""
Utility functions for converting between JSON and Gherkin formats.
This module enables structured, surgical edits to test scenarios.
"""

import json
from copy import deepcopy
from typing import Dict, List, Optional, Any, Tuple


def renumber_scenario_ids(feature_json: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Renumber scenario IDs to be sequential (scenario_1, scenario_2, ...).
    Useful after deletions or when LLM generates inconsistent IDs.
    
    Args:
        feature_json: Feature JSON structure with scenarios
        
    Returns:
        Tuple of (updated_feature_json, id_mapping)
        - updated_feature_json: Feature JSON with renumbered scenario IDs
        - id_mapping: Dict mapping old_id -> new_id for script updates
    """
    updated = deepcopy(feature_json)
    id_mapping = {}
    
    scenarios = updated.get("scenarios", [])
    for i, scenario in enumerate(scenarios, 1):
        old_id = scenario.get("id", f"scenario_{i}")
        new_id = f"scenario_{i}"
        
        if old_id != new_id:
            id_mapping[old_id] = new_id
            scenario["id"] = new_id
    
    return updated, id_mapping


def has_scenario_id_gaps(feature_json: Dict[str, Any]) -> bool:
    """
    Check if there are gaps in scenario ID numbering.
    
    Args:
        feature_json: Feature JSON structure
        
    Returns:
        True if gaps exist (e.g., scenario_1, scenario_3, scenario_5)
    """
    scenarios = feature_json.get("scenarios", [])
    expected_ids = {f"scenario_{i}" for i in range(1, len(scenarios) + 1)}
    actual_ids = {s.get("id", "") for s in scenarios}
    
    return expected_ids != actual_ids


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


def _resolve_path(root: Any, path: str) -> Any:
    """Resolve a slash-delimited path (JSON Pointer style without leading slash).

    Supports list indices and dict keys. Returns the parent container and final key/index.
    Raises KeyError/IndexError/TypeError on invalid paths so callers can handle gracefully.
    """
    if path.startswith("/"):
        path = path[1:]
    parts = [p for p in path.split("/") if p != ""]

    parent = root
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        
        # Special case: "-" means "append to end" for lists, but only as the LAST segment
        if part == "-" and isinstance(parent, list) and is_last:
            return parent, "-"

        # Attempt integer index when working with lists
        if isinstance(parent, list):
            try:
                idx = int(part)
                if is_last:
                    return parent, idx
                parent = parent[idx]
            except ValueError:
                 raise TypeError(f"List index must be integer, got '{part}'")
        elif isinstance(parent, dict):
            if is_last:
                return parent, part
            parent = parent[part]
        else:
            raise TypeError(f"Cannot traverse into non-container at '{part}'")
    # If path empty, point to root
    return None, None


def apply_feature_modifications(current_feature_json: Dict[str, Any], modifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply a list of surgical modifications to a feature JSON structure.

    Supported ops (minimal set):
      - add:     {"op": "add", "path": "feature/description", "value": "..."}
      - replace: {"op": "replace", "path": "scenarios/0/steps/2/text", "value": "..."}
      - remove:  {"op": "remove", "path": "scenarios/1/tags/0"}

    Paths are slash-delimited (similar to JSON Pointer without the leading slash).
    Lists use numeric indices. The operation order is preserved.
    """
    updated = deepcopy(current_feature_json)

    for mod in modifications or []:
        op = mod.get("op")
        path = mod.get("path", "")

        if not op or not path:
            print(f"⚠️ Skipping modification without op/path: {mod}")
            continue

        try:
            container, key = _resolve_path(updated, path)
        except Exception as e:
            print(f"⚠️ Failed to resolve path '{path}' for op '{op}': {e}")
            continue

        # If container is None, it means path was empty; skip
        if container is None:
            print(f"⚠️ Skipping modification with empty path: {mod}")
            continue

        if op == "add":
            value = mod.get("value")
            if isinstance(container, list):
                if key == "-":
                    container.append(value)
                else:
                    idx = int(key)
                    if idx >= 0 and idx <= len(container):
                        container.insert(idx, value)
                    else:
                        print(f"⚠️ Add index out of range for path '{path}': {idx}")
            else:
                container[key] = value

        elif op == "replace":
            value = mod.get("value")
            if isinstance(container, list):
                # Replace doesn't support append via "-", so we expect int
                idx = int(key)
                if 0 <= idx < len(container):
                    container[idx] = value
                else:
                    print(f"⚠️ Replace index out of range for path '{path}': {idx}")
            else:
                container[key] = value

        elif op == "remove":
            if isinstance(container, list):
                idx = int(key)
                if 0 <= idx < len(container):
                    container.pop(idx)
                else:
                    print(f"⚠️ Remove index out of range for path '{path}': {idx}")
            else:
                container.pop(key, None)

        else:
            print(f"⚠️ Unknown op '{op}' - skipping")

    return updated


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
