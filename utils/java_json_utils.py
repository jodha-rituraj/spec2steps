"""
Java JSON Utilities - Convert between Java code and structured JSON IR.

This module provides utilities for working with Java test scripts in a 
structured JSON format (Intermediate Representation), enabling deterministic
modifications and easier manipulation of code structure.

JSON IR Schema:
{
    "package": "com.example.tests",
    "imports": ["import1", "import2", ...],
    "className": "ClassName",
    "classAnnotations": [{"name": "...", "value": "..."}],
    "fields": [
        {
            "id": "field_1",
            "modifiers": ["private", "static"],
            "type": "Type",
            "name": "fieldName",
            "initializer": "value or expression"
        }
    ],
    "methods": [
        {
            "id": "method_1",
            "scenarioId": "scenario_1",
            "annotations": [{"name": "Given", "value": "step text"}],
            "modifiers": ["public"],
            "returnType": "void",
            "name": "methodName",
            "parameters": [{"type": "String", "name": "param"}],
            "body": ["line1;", "line2;"]
        }
    ]
}
"""

import re
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple


def generate_id(prefix: str = "id") -> str:
    """Generate a unique ID for JSON elements."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def json_to_java(script_json: Dict) -> str:
    """
    Convert a structured JSON IR to Java code.
    
    Args:
        script_json: Dictionary containing the structured script representation
        
    Returns:
        str: Formatted Java code
    """
    lines = []
    
    # Package declaration
    package = script_json.get("package", "")
    if package:
        lines.append(f"package {package};")
        lines.append("")
    
    # Import statements (sorted for consistency)
    imports = script_json.get("imports", [])
    if imports:
        sorted_imports = sorted(set(imports))
        for imp in sorted_imports:
            # Ensure proper format
            if not imp.startswith("import "):
                imp = f"import {imp}"
            if not imp.endswith(";"):
                imp = f"{imp};"
            lines.append(imp)
        lines.append("")
    
    # Class annotations
    class_annotations = script_json.get("classAnnotations", [])
    for annotation in class_annotations:
        lines.append(_format_annotation(annotation))
    
    # Class declaration
    class_name = script_json.get("className", "GeneratedTests")
    lines.append(f"public class {class_name} {{")
    lines.append("")
    
    # Fields
    fields = script_json.get("fields", [])
    for field in fields:
        field_line = _format_field(field)
        lines.append(f"    {field_line}")
    
    if fields:
        lines.append("")
    
    # Methods
    methods = script_json.get("methods", [])
    for i, method in enumerate(methods):
        method_lines = _format_method(method)
        for line in method_lines:
            lines.append(f"    {line}" if line else "")
        
        # Add blank line between methods
        if i < len(methods) - 1:
            lines.append("")
    
    # Close class
    lines.append("}")
    
    return "\n".join(lines)


def java_to_json(java_code: str) -> Dict:
    """
    Parse Java code into structured JSON IR.
    
    Args:
        java_code: String containing Java source code
        
    Returns:
        Dict: Structured JSON representation of the Java code
    """
    result = {
        "package": "",
        "imports": [],
        "className": "GeneratedTests",
        "classAnnotations": [],
        "fields": [],
        "methods": []
    }
    
    # Extract package
    package_match = re.search(r'package\s+([\w.]+)\s*;', java_code)
    if package_match:
        result["package"] = package_match.group(1)
    
    # Extract imports
    import_matches = re.findall(r'import\s+(?:static\s+)?([\w.*]+)\s*;', java_code)
    result["imports"] = list(set(import_matches))
    
    # Extract class name and annotations
    class_annotations, class_name = _extract_class_info(java_code)
    result["classAnnotations"] = class_annotations
    if class_name:
        result["className"] = class_name
    
    # Extract class body
    class_body = _extract_class_body(java_code)
    if class_body:
        # Extract fields and methods
        result["fields"] = _extract_fields(class_body)
        result["methods"] = _extract_methods(class_body)
    
    return result


def merge_script_jsons(script_jsons: List[Dict], merged_class_name: str = "GeneratedTests") -> Dict:
    """
    Merge multiple script JSONs into a single script JSON.
    
    This is a deterministic merge operation that:
    - Combines all imports (deduplicated)
    - Combines all fields (deduplicated by name)
    - Combines all methods
    - Uses the first package found
    
    Args:
        script_jsons: List of script JSON dictionaries
        merged_class_name: Name for the merged class
        
    Returns:
        Dict: Merged script JSON
    """
    if not script_jsons:
        return {
            "package": "",
            "imports": [],
            "className": merged_class_name,
            "classAnnotations": [],
            "fields": [],
            "methods": []
        }
    
    merged = {
        "package": "",
        "imports": [],
        "className": merged_class_name,
        "classAnnotations": [],
        "fields": [],
        "methods": []
    }
    
    seen_imports = set()
    seen_fields = {}  # key: (type, name) -> field
    field_counter = 1
    method_counter = 1
    
    for script in script_jsons:
        # Package - use first non-empty
        if not merged["package"] and script.get("package"):
            merged["package"] = script["package"]
        
        # Imports - deduplicate
        for imp in script.get("imports", []):
            if imp not in seen_imports:
                seen_imports.add(imp)
                merged["imports"].append(imp)
        
        # Class annotations - use first non-empty set
        if not merged["classAnnotations"] and script.get("classAnnotations"):
            merged["classAnnotations"] = script["classAnnotations"]
        
        # Fields - deduplicate by (type, name)
        for field in script.get("fields", []):
            field_key = (field.get("type", ""), field.get("name", ""))
            if field_key not in seen_fields:
                # Assign new ID
                field_copy = field.copy()
                field_copy["id"] = f"field_{field_counter}"
                field_counter += 1
                seen_fields[field_key] = field_copy
                merged["fields"].append(field_copy)
        
        # Methods - add all with new IDs
        for method in script.get("methods", []):
            method_copy = method.copy()
            method_copy["id"] = f"method_{method_counter}"
            method_counter += 1
            merged["methods"].append(method_copy)
    
    # Sort imports for consistency
    merged["imports"] = sorted(merged["imports"])
    
    return merged


def apply_json_modification(script_json: Dict, modification: Dict) -> Dict:
    """
    Apply a deterministic modification to a script JSON.
    
    Modification types:
    - rename_class: {"action": "rename_class", "new_name": "NewClassName"}
    - rename_method: {"action": "rename_method", "method_id": "...", "new_name": "..."}
    - rename_field: {"action": "rename_field", "field_id": "...", "new_name": "..."}
    - add_import: {"action": "add_import", "import": "com.example.Class"}
    - remove_import: {"action": "remove_import", "import": "com.example.Class"}
    - add_field: {"action": "add_field", "field": {...}}
    - remove_field: {"action": "remove_field", "field_id": "..."}
    - update_method_body: {"action": "update_method_body", "method_id": "...", "body": [...]}
    - add_annotation: {"action": "add_annotation", "method_id": "...", "annotation": {...}}
    - update_package: {"action": "update_package", "package": "com.new.package"}
    
    Args:
        script_json: The script JSON to modify
        modification: The modification to apply
        
    Returns:
        Dict: Modified script JSON (new copy)
    """
    import copy
    result = copy.deepcopy(script_json)
    
    action = modification.get("action", "")
    
    if action == "rename_class":
        result["className"] = modification.get("new_name", result["className"])
    
    elif action == "rename_method":
        method_id = modification.get("method_id")
        new_name = modification.get("new_name")
        for method in result["methods"]:
            if method.get("id") == method_id:
                method["name"] = new_name
                break
    
    elif action == "rename_field":
        field_id = modification.get("field_id")
        new_name = modification.get("new_name")
        for field in result["fields"]:
            if field.get("id") == field_id:
                field["name"] = new_name
                break
    
    elif action == "add_import":
        new_import = modification.get("import", "")
        if new_import and new_import not in result["imports"]:
            result["imports"].append(new_import)
            result["imports"] = sorted(result["imports"])
    
    elif action == "remove_import":
        import_to_remove = modification.get("import", "")
        result["imports"] = [i for i in result["imports"] if i != import_to_remove]
    
    elif action == "add_field":
        new_field = modification.get("field", {})
        if new_field:
            if "id" not in new_field:
                new_field["id"] = generate_id("field")
            result["fields"].append(new_field)
    
    elif action == "remove_field":
        field_id = modification.get("field_id")
        result["fields"] = [f for f in result["fields"] if f.get("id") != field_id]
    
    elif action == "update_method_body":
        method_id = modification.get("method_id")
        new_body = modification.get("body", [])
        for method in result["methods"]:
            if method.get("id") == method_id:
                method["body"] = new_body
                break
    
    elif action == "add_method":
        new_method = modification.get("method", {})
        if new_method:
            if "id" not in new_method:
                new_method["id"] = generate_id("method")
            result["methods"].append(new_method)
    
    elif action == "remove_method":
        method_id = modification.get("method_id")
        result["methods"] = [m for m in result["methods"] if m.get("id") != method_id]
    
    elif action == "add_annotation":
        method_id = modification.get("method_id")
        annotation = modification.get("annotation", {})
        for method in result["methods"]:
            if method.get("id") == method_id:
                if "annotations" not in method:
                    method["annotations"] = []
                method["annotations"].append(annotation)
                break
    
    elif action == "update_package":
        result["package"] = modification.get("package", result["package"])
    
    elif action == "update_field_initializer":
        field_id = modification.get("field_id")
        new_initializer = modification.get("initializer")
        for field in result["fields"]:
            if field.get("id") == field_id:
                field["initializer"] = new_initializer
                break
    
    elif action == "update_method_parameters":
        method_id = modification.get("method_id")
        new_params = modification.get("parameters", [])
        for method in result["methods"]:
            if method.get("id") == method_id:
                method["parameters"] = new_params
                break
    
    elif action == "update_method_scenario_id":
        method_id = modification.get("method_id")
        new_scenario_id = modification.get("new_scenario_id")
        for method in result["methods"]:
            if method.get("id") == method_id:
                method["scenarioId"] = new_scenario_id
                break
    
    return result


def update_script_scenario_references(script_json: Dict, id_mapping: Dict[str, str]) -> Dict:
    """
    Update all method scenarioId references in a script JSON based on ID mapping.
    
    Useful when feature file scenarios are renumbered - this updates the script
    to maintain consistency.
    
    Args:
        script_json: Script JSON structure
        id_mapping: Dict mapping old_scenario_id -> new_scenario_id
        
    Returns:
        Updated script JSON with corrected scenarioId references
    """
    import copy
    result = copy.deepcopy(script_json)
    
    for method in result.get("methods", []):
        old_scenario_id = method.get("scenarioId")
        if old_scenario_id and old_scenario_id in id_mapping:
            method["scenarioId"] = id_mapping[old_scenario_id]
    
    return result


def find_orphaned_methods(script_json: Dict, valid_scenario_ids: List[str]) -> List[Dict]:
    """
    Find methods in script that reference non-existent scenarios.
    
    Args:
        script_json: Script JSON structure
        valid_scenario_ids: List of valid scenario IDs from feature file
        
    Returns:
        List of method objects that have invalid scenarioId references
    """
    valid_ids_set = set(valid_scenario_ids)
    orphaned = []
    
    for method in script_json.get("methods", []):
        scenario_id = method.get("scenarioId")
        if scenario_id and scenario_id not in valid_ids_set:
            orphaned.append(method)
    
    return orphaned


def validate_scenario_script_consistency(
    feature_json: Dict, 
    script_json: Dict
) -> Tuple[bool, List[str]]:
    """
    Validate that script methods and feature scenarios are consistent.
    
    Checks for:
    - Orphaned methods (referencing deleted scenarios)
    - Missing implementations (scenarios without methods)
    - Scenario ID numbering gaps
    
    Args:
        feature_json: Feature file JSON structure
        script_json: Script JSON structure
        
    Returns:
        Tuple of (is_valid, warnings)
        - is_valid: True if no critical issues found
        - warnings: List of warning/error messages
    """
    warnings = []
    is_valid = True
    
    # Get valid scenario IDs from feature
    scenarios = feature_json.get("scenarios", [])
    valid_scenario_ids = {s.get("id") for s in scenarios if s.get("id")}
    
    # Check for gaps in scenario numbering
    expected_ids = {f"scenario_{i}" for i in range(1, len(scenarios) + 1)}
    if valid_scenario_ids != expected_ids:
        warnings.append(
            f"⚠️ Scenario ID numbering has gaps. Expected {sorted(expected_ids)}, "
            f"but found {sorted(valid_scenario_ids)}"
        )
        is_valid = False
    
    # Find orphaned methods
    orphaned = find_orphaned_methods(script_json, list(valid_scenario_ids))
    if orphaned:
        for method in orphaned:
            warnings.append(
                f"⚠️ Method '{method.get('name')}' (id: {method.get('id')}) "
                f"references deleted scenario '{method.get('scenarioId')}'"
            )
        is_valid = False
    
    # Find scenarios without implementations
    methods = script_json.get("methods", [])
    implemented_scenarios = {m.get("scenarioId") for m in methods if m.get("scenarioId")}
    missing_implementations = valid_scenario_ids - implemented_scenarios
    
    if missing_implementations:
        for scenario_id in sorted(missing_implementations):
            # Find scenario name
            scenario_name = next(
                (s.get("name", "Unknown") for s in scenarios if s.get("id") == scenario_id),
                "Unknown"
            )
            warnings.append(
                f"ℹ️ Scenario '{scenario_id}' ({scenario_name}) has no corresponding "
                f"methods in the script"
            )
    
    return is_valid, warnings


def get_json_diff(old_json: Dict, new_json: Dict) -> Dict:
    """
    Generate a diff between two script JSONs.
    
    Returns a structured diff showing what changed.
    
    Args:
        old_json: Original script JSON
        new_json: Modified script JSON
        
    Returns:
        Dict: Structured diff with changes
    """
    diff = {
        "package_changed": old_json.get("package") != new_json.get("package"),
        "class_name_changed": old_json.get("className") != new_json.get("className"),
        "imports_added": [],
        "imports_removed": [],
        "fields_added": [],
        "fields_removed": [],
        "fields_modified": [],
        "methods_added": [],
        "methods_removed": [],
        "methods_modified": []
    }
    
    # Compare imports
    old_imports = set(old_json.get("imports", []))
    new_imports = set(new_json.get("imports", []))
    diff["imports_added"] = list(new_imports - old_imports)
    diff["imports_removed"] = list(old_imports - new_imports)
    
    # Compare fields
    old_fields = {f.get("id"): f for f in old_json.get("fields", [])}
    new_fields = {f.get("id"): f for f in new_json.get("fields", [])}
    
    diff["fields_added"] = [f for fid, f in new_fields.items() if fid not in old_fields]
    diff["fields_removed"] = [f for fid, f in old_fields.items() if fid not in new_fields]
    
    for fid in old_fields:
        if fid in new_fields and old_fields[fid] != new_fields[fid]:
            diff["fields_modified"].append({
                "id": fid,
                "old": old_fields[fid],
                "new": new_fields[fid]
            })
    
    # Compare methods
    old_methods = {m.get("id"): m for m in old_json.get("methods", [])}
    new_methods = {m.get("id"): m for m in new_json.get("methods", [])}
    
    diff["methods_added"] = [m for mid, m in new_methods.items() if mid not in old_methods]
    diff["methods_removed"] = [m for mid, m in old_methods.items() if mid not in new_methods]
    
    for mid in old_methods:
        if mid in new_methods and old_methods[mid] != new_methods[mid]:
            diff["methods_modified"].append({
                "id": mid,
                "old": old_methods[mid],
                "new": new_methods[mid]
            })
    
    return diff


# ==================== Private Helper Functions ====================

def _format_annotation(annotation: Dict) -> str:
    """Format an annotation dictionary to Java annotation string."""
    name = annotation.get("name", "")
    value = annotation.get("value")
    
    if value is not None:
        # Handle different value types
        if isinstance(value, str):
            return f'@{name}("{value}")'
        elif isinstance(value, dict):
            # Complex annotation with multiple attributes
            attrs = ", ".join(f'{k} = "{v}"' if isinstance(v, str) else f'{k} = {v}' 
                            for k, v in value.items())
            return f'@{name}({attrs})'
        else:
            return f'@{name}({value})'
    else:
        return f'@{name}'


def _format_field(field: Dict) -> str:
    """Format a field dictionary to Java field declaration."""
    modifiers = field.get("modifiers", [])
    field_type = field.get("type", "Object")
    name = field.get("name", "field")
    initializer = field.get("initializer")
    
    parts = []
    if modifiers:
        parts.append(" ".join(modifiers))
    parts.append(field_type)
    parts.append(name)
    
    declaration = " ".join(parts)
    
    if initializer:
        declaration += f" = {initializer}"
    
    return declaration + ";"


def _format_method(method: Dict) -> List[str]:
    """Format a method dictionary to Java method lines."""
    lines = []
    
    # Annotations
    for annotation in method.get("annotations", []):
        lines.append(_format_annotation(annotation))
    
    # Method signature
    modifiers = method.get("modifiers", ["public"])
    return_type = method.get("returnType", "void")
    name = method.get("name", "method")
    parameters = method.get("parameters", [])
    
    # Format parameters
    param_str = ", ".join(f'{p.get("type", "Object")} {p.get("name", "param")}' 
                          for p in parameters)
    
    signature = f'{" ".join(modifiers)} {return_type} {name}({param_str}) {{'
    lines.append(signature)
    
    # Method body
    body = method.get("body", [])
    for body_line in body:
        # Preserve indentation if present, otherwise add standard indentation
        if body_line.strip():
            lines.append(f"    {body_line}")
        else:
            lines.append("")
    
    lines.append("}")
    
    return lines


def _extract_class_info(java_code: str) -> Tuple[List[Dict], str]:
    """Extract class annotations and name from Java code."""
    annotations = []
    class_name = "GeneratedTests"
    
    # Find class declaration with potential annotations before it
    class_pattern = r'((?:@\w+(?:\([^)]*\))?\s*)*)\s*public\s+class\s+(\w+)'
    match = re.search(class_pattern, java_code)
    
    if match:
        annotation_block = match.group(1)
        class_name = match.group(2)
        
        # Parse annotations
        annotation_pattern = r'@(\w+)(?:\(([^)]*)\))?'
        for ann_match in re.finditer(annotation_pattern, annotation_block):
            ann_name = ann_match.group(1)
            ann_value = ann_match.group(2)
            
            if ann_value:
                # Remove quotes from string values
                ann_value = ann_value.strip('"\'')
                annotations.append({"name": ann_name, "value": ann_value})
            else:
                annotations.append({"name": ann_name})
    
    return annotations, class_name


def _extract_class_body(java_code: str) -> str:
    """Extract the class body content from Java code."""
    # Find class opening brace
    class_match = re.search(r'public\s+class\s+\w+[^{]*\{', java_code)
    if not class_match:
        return ""
    
    start = class_match.end()
    
    # Find matching closing brace
    brace_count = 1
    end = start
    
    for i, char in enumerate(java_code[start:], start):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i
                break
    
    return java_code[start:end]


def _extract_fields(class_body: str) -> List[Dict]:
    """Extract field declarations from class body."""
    fields = []
    field_counter = 1
    
    # Pattern to match field declarations (not inside methods)
    # This is a simplified extraction - handles common patterns
    lines = class_body.split('\n')
    
    in_method = False
    brace_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Track if we're inside a method
        brace_count += line.count('{') - line.count('}')
        
        # Skip if we're inside a method body
        if brace_count > 0 and '{' in line:
            in_method = True
        if brace_count == 0:
            in_method = False
        
        if in_method:
            continue
        
        # Check if this looks like a field declaration
        # Pattern: [modifiers] Type name [= initializer];
        if stripped and stripped.endswith(';') and not stripped.startswith('//'):
            # Skip method calls and statements
            if '(' in stripped and ')' in stripped and '=' not in stripped.split('(')[0]:
                continue
            
            field = _parse_field_declaration(stripped)
            if field:
                field["id"] = f"field_{field_counter}"
                field_counter += 1
                fields.append(field)
    
    return fields


def _parse_field_declaration(line: str) -> Optional[Dict]:
    """Parse a single field declaration line."""
    # Remove trailing semicolon
    line = line.rstrip(';').strip()
    
    # Pattern: [modifiers] Type name [= initializer]
    # Modifiers: public, private, protected, static, final, volatile, transient
    modifier_pattern = r'^((?:(?:public|private|protected|static|final|volatile|transient)\s+)*)'
    
    match = re.match(modifier_pattern, line)
    if not match:
        return None
    
    modifiers_str = match.group(1).strip()
    rest = line[match.end():].strip()
    
    if not rest:
        return None
    
    # Extract modifiers list
    modifiers = modifiers_str.split() if modifiers_str else []
    
    # Parse type and name with optional initializer
    # Handle generic types like List<String>
    init_match = re.match(r'([\w<>,\s\[\]]+?)\s+(\w+)\s*(?:=\s*(.+))?$', rest)
    
    if not init_match:
        return None
    
    field_type = init_match.group(1).strip()
    field_name = init_match.group(2).strip()
    initializer = init_match.group(3).strip() if init_match.group(3) else None
    
    # Skip if it looks like a method (has parentheses in type)
    if '(' in field_type:
        return None
    
    return {
        "modifiers": modifiers,
        "type": field_type,
        "name": field_name,
        "initializer": initializer
    }


def _extract_methods(class_body: str) -> List[Dict]:
    """Extract method definitions from class body."""
    methods = []
    method_counter = 1
    
    # Split into potential method blocks
    lines = class_body.split('\n')
    
    current_annotations = []
    current_method_lines = []
    in_method = False
    brace_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Collect annotations
        if stripped.startswith('@') and not in_method:
            current_annotations.append(stripped)
            continue
        
        # Check for method start
        if not in_method and _is_method_signature(stripped):
            in_method = True
            current_method_lines = [line]
            brace_count = line.count('{') - line.count('}')
            
            # If method is single line (e.g., abstract method)
            if brace_count == 0 and '{' in line:
                method = _parse_method(current_annotations, current_method_lines)
                if method:
                    method["id"] = f"method_{method_counter}"
                    method_counter += 1
                    methods.append(method)
                current_annotations = []
                current_method_lines = []
                in_method = False
            continue
        
        # Inside a method
        if in_method:
            current_method_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            
            # Method complete
            if brace_count == 0:
                method = _parse_method(current_annotations, current_method_lines)
                if method:
                    method["id"] = f"method_{method_counter}"
                    method_counter += 1
                    methods.append(method)
                current_annotations = []
                current_method_lines = []
                in_method = False
        else:
            # Reset annotations if we hit a non-annotation, non-method line
            if stripped and not stripped.startswith('@'):
                current_annotations = []
    
    return methods


def _is_method_signature(line: str) -> bool:
    """Check if a line is a method signature."""
    # Method pattern: [modifiers] returnType methodName(params) {
    method_pattern = r'^(?:(?:public|private|protected|static|final|synchronized|abstract)\s+)*\w+(?:<[^>]+>)?\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{?'
    return bool(re.match(method_pattern, line.strip()))


def _parse_method(annotations: List[str], method_lines: List[str]) -> Optional[Dict]:
    """Parse a method from its annotation and body lines."""
    if not method_lines:
        return None
    
    # Parse annotations
    parsed_annotations = []
    for ann in annotations:
        ann_match = re.match(r'@(\w+)(?:\(([^)]*)\))?', ann)
        if ann_match:
            ann_name = ann_match.group(1)
            ann_value = ann_match.group(2)
            if ann_value:
                ann_value = ann_value.strip('"\'')
                parsed_annotations.append({"name": ann_name, "value": ann_value})
            else:
                parsed_annotations.append({"name": ann_name})
    
    # Parse method signature (first line)
    first_line = method_lines[0].strip()
    
    # Extract signature components
    sig_pattern = r'^((?:(?:public|private|protected|static|final|synchronized)\s+)*)(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
    sig_match = re.match(sig_pattern, first_line)
    
    if not sig_match:
        return None
    
    modifiers_str = sig_match.group(1).strip()
    return_type = sig_match.group(2)
    method_name = sig_match.group(3)
    params_str = sig_match.group(4)
    
    # Parse modifiers
    modifiers = modifiers_str.split() if modifiers_str else ["public"]
    
    # Parse parameters
    parameters = []
    if params_str.strip():
        for param in params_str.split(','):
            param = param.strip()
            if param:
                parts = param.rsplit(' ', 1)
                if len(parts) == 2:
                    parameters.append({"type": parts[0], "name": parts[1]})
    
    # Extract method body
    body = []
    if len(method_lines) > 1:
        # Skip first line (signature) and last line (closing brace)
        body_lines = method_lines[1:-1] if method_lines[-1].strip() == '}' else method_lines[1:]
        
        for line in body_lines:
            # Remove one level of indentation (4 spaces or 1 tab)
            if line.startswith('        '):
                body.append(line[8:])
            elif line.startswith('    '):
                body.append(line[4:])
            elif line.startswith('\t\t'):
                body.append(line[2:])
            elif line.startswith('\t'):
                body.append(line[1:])
            else:
                body.append(line)
    
    return {
        "annotations": parsed_annotations,
        "modifiers": modifiers,
        "returnType": return_type,
        "name": method_name,
        "parameters": parameters,
        "body": body
    }


# ==================== Validation Functions ====================

def validate_script_json(script_json: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a script JSON against the expected schema.
    
    Args:
        script_json: The script JSON to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check required top-level keys
    required_keys = ["className", "methods"]
    for key in required_keys:
        if key not in script_json:
            errors.append(f"Missing required key: {key}")
    
    # Validate className
    if "className" in script_json:
        if not isinstance(script_json["className"], str) or not script_json["className"]:
            errors.append("className must be a non-empty string")
    
    # Validate imports
    if "imports" in script_json:
        if not isinstance(script_json["imports"], list):
            errors.append("imports must be a list")
    
    # Validate fields
    if "fields" in script_json:
        if not isinstance(script_json["fields"], list):
            errors.append("fields must be a list")
        else:
            for i, field in enumerate(script_json["fields"]):
                if not isinstance(field, dict):
                    errors.append(f"fields[{i}] must be a dictionary")
                elif "name" not in field or "type" not in field:
                    errors.append(f"fields[{i}] missing required keys: name, type")
    
    # Validate methods
    if "methods" in script_json:
        if not isinstance(script_json["methods"], list):
            errors.append("methods must be a list")
        else:
            for i, method in enumerate(script_json["methods"]):
                if not isinstance(method, dict):
                    errors.append(f"methods[{i}] must be a dictionary")
                elif "name" not in method:
                    errors.append(f"methods[{i}] missing required key: name")
    
    return (len(errors) == 0, errors)


if __name__ == "__main__":
    # Test the module
    test_java = '''
package com.example.tests;

import io.restassured.RestAssured;
import org.testng.annotations.Test;
import io.cucumber.java.en.Given;

public class TestClass {
    private static Logger logger = LogManager.getLogger(TestClass.class);
    private ApiClient apiClient = new ApiClient();

    @Given("I have a valid API endpoint")
    public void iHaveValidApiEndpoint() {
        String baseUrl = "https://api.example.com";
        RestAssured.baseURI = baseUrl;
    }

    @When("I send a GET request to {string}")
    public void iSendGetRequest(String endpoint) {
        response = RestAssured.given()
            .when()
            .get(endpoint);
    }
}
'''
    
    # Test java_to_json
    print("=== Testing java_to_json ===")
    script_json = java_to_json(test_java)
    print(json.dumps(script_json, indent=2))
    
    print("\n=== Testing json_to_java ===")
    regenerated_java = json_to_java(script_json)
    print(regenerated_java)
    
    print("\n=== Testing apply_json_modification ===")
    modified = apply_json_modification(script_json, {
        "action": "rename_class",
        "new_name": "RenamedTestClass"
    })
    print(f"New class name: {modified['className']}")
    
    print("\n=== Testing validation ===")
    is_valid, errors = validate_script_json(script_json)
    print(f"Valid: {is_valid}, Errors: {errors}")
