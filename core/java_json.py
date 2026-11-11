"""
Java step-definition classes <-> JSON intermediate representation.

The LLM edits scripts by emitting small modifications against this structure
(see apply_json_modification), so unchanged code is never rewritten.

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

import copy
import re
import uuid
from typing import Dict, List, Optional, Any, Tuple


def generate_id(prefix: str = "id") -> str:
    """Generate a unique ID for JSON elements."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def json_to_java(script_json: Dict) -> str:
    """Convert a structured JSON IR to Java code."""
    lines = []

    package = script_json.get("package", "")
    if package:
        lines.append(f"package {package};")
        lines.append("")

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

    class_annotations = script_json.get("classAnnotations", [])
    for annotation in class_annotations:
        lines.append(_format_annotation(annotation))

    class_name = script_json.get("className", "GeneratedTests")
    lines.append(f"public class {class_name} {{")
    lines.append("")

    fields = script_json.get("fields", [])
    for field in fields:
        field_line = _format_field(field)
        lines.append(f"    {field_line}")

    if fields:
        lines.append("")

    methods = script_json.get("methods", [])
    for i, method in enumerate(methods):
        method_lines = _format_method(method)
        for line in method_lines:
            lines.append(f"    {line}" if line else "")

        if i < len(methods) - 1:
            lines.append("")

    lines.append("}")

    return "\n".join(lines)


def java_to_json(java_code: str) -> Dict:
    """Parse Java code into structured JSON IR."""
    result = {
        "package": "",
        "imports": [],
        "className": "GeneratedTests",
        "classAnnotations": [],
        "fields": [],
        "methods": []
    }

    package_match = re.search(r'package\s+([\w.]+)\s*;', java_code)
    if package_match:
        result["package"] = package_match.group(1)

    import_matches = re.findall(r'import\s+(?:static\s+)?([\w.*]+)\s*;', java_code)
    result["imports"] = list(set(import_matches))

    class_annotations, class_name = _extract_class_info(java_code)
    result["classAnnotations"] = class_annotations
    if class_name:
        result["className"] = class_name

    class_body = _extract_class_body(java_code)
    if class_body:
        result["fields"] = _extract_fields(class_body)
        result["methods"] = _extract_methods(class_body)

    return result


def merge_script_jsons(script_jsons: List[Dict], merged_class_name: str = "GeneratedTests") -> Dict:
    """
    Deterministic merge: imports and fields are de-duplicated, methods are
    concatenated and re-numbered, the first package and class annotations win.
    """
    merged = {
        "package": "",
        "imports": [],
        "className": merged_class_name,
        "classAnnotations": [],
        "fields": [],
        "methods": []
    }

    seen_imports = set()
    seen_fields = {}
    field_counter = 1
    method_counter = 1

    for script in script_jsons:
        if not merged["package"] and script.get("package"):
            merged["package"] = script["package"]

        for imp in script.get("imports", []):
            if imp not in seen_imports:
                seen_imports.add(imp)
                merged["imports"].append(imp)

        if not merged["classAnnotations"] and script.get("classAnnotations"):
            merged["classAnnotations"] = script["classAnnotations"]

        for field in script.get("fields", []):
            field_key = (field.get("type", ""), field.get("name", ""))
            if field_key not in seen_fields:
                field_copy = field.copy()
                field_copy["id"] = f"field_{field_counter}"
                field_counter += 1
                seen_fields[field_key] = field_copy
                merged["fields"].append(field_copy)

        for method in script.get("methods", []):
            method_copy = method.copy()
            method_copy["id"] = f"method_{method_counter}"
            method_counter += 1
            merged["methods"].append(method_copy)

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
    """
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


def _format_annotation(annotation: Dict) -> str:
    """Format an annotation dictionary to Java annotation string."""
    name = annotation.get("name", "")
    value = annotation.get("value")

    if value is not None:
        if isinstance(value, str):
            return f'@{name}("{value}")'
        elif isinstance(value, dict):
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

    for annotation in method.get("annotations", []):
        lines.append(_format_annotation(annotation))

    modifiers = method.get("modifiers", ["public"])
    return_type = method.get("returnType", "void")
    name = method.get("name", "method")
    parameters = method.get("parameters", [])

    param_str = ", ".join(f'{p.get("type", "Object")} {p.get("name", "param")}'
                          for p in parameters)

    signature = f'{" ".join(modifiers)} {return_type} {name}({param_str}) {{'
    lines.append(signature)

    body = method.get("body", [])
    for body_line in body:
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

        annotation_pattern = r'@(\w+)(?:\(([^)]*)\))?'
        for ann_match in re.finditer(annotation_pattern, annotation_block):
            ann_name = ann_match.group(1)
            ann_value = ann_match.group(2)

            if ann_value:
                ann_value = ann_value.strip('"\'')
                annotations.append({"name": ann_name, "value": ann_value})
            else:
                annotations.append({"name": ann_name})

    return annotations, class_name


def _extract_class_body(java_code: str) -> str:
    """Extract the class body content from Java code."""
    class_match = re.search(r'public\s+class\s+\w+[^{]*\{', java_code)
    if not class_match:
        return ""

    start = class_match.end()

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

    lines = class_body.split('\n')

    in_method = False
    brace_count = 0

    for line in lines:
        stripped = line.strip()

        brace_count += line.count('{') - line.count('}')

        # Skip if we're inside a method body
        if brace_count > 0 and '{' in line:
            in_method = True
        if brace_count == 0:
            in_method = False

        if in_method:
            continue

        if stripped and stripped.endswith(';') and not stripped.startswith('//'):
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
    line = line.rstrip(';').strip()

    modifier_pattern = r'^((?:(?:public|private|protected|static|final|volatile|transient)\s+)*)'

    match = re.match(modifier_pattern, line)
    if not match:
        return None

    modifiers_str = match.group(1).strip()
    rest = line[match.end():].strip()

    if not rest:
        return None

    modifiers = modifiers_str.split() if modifiers_str else []

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

    lines = class_body.split('\n')

    current_annotations = []
    current_method_lines = []
    in_method = False
    brace_count = 0

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('@') and not in_method:
            current_annotations.append(stripped)
            continue

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

        if in_method:
            current_method_lines.append(line)
            brace_count += line.count('{') - line.count('}')

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
    method_pattern = r'^(?:(?:public|private|protected|static|final|synchronized|abstract)\s+)*\w+(?:<[^>]+>)?\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{?'
    return bool(re.match(method_pattern, line.strip()))


def _parse_method(annotations: List[str], method_lines: List[str]) -> Optional[Dict]:
    """Parse a method from its annotation and body lines."""
    if not method_lines:
        return None

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

    first_line = method_lines[0].strip()

    sig_pattern = r'^((?:(?:public|private|protected|static|final|synchronized)\s+)*)(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
    sig_match = re.match(sig_pattern, first_line)

    if not sig_match:
        return None

    modifiers_str = sig_match.group(1).strip()
    return_type = sig_match.group(2)
    method_name = sig_match.group(3)
    params_str = sig_match.group(4)

    modifiers = modifiers_str.split() if modifiers_str else ["public"]

    parameters = []
    if params_str.strip():
        for param in params_str.split(','):
            param = param.strip()
            if param:
                parts = param.rsplit(' ', 1)
                if len(parts) == 2:
                    parameters.append({"type": parts[0], "name": parts[1]})

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


def validate_script_json(script_json: Dict) -> Tuple[bool, List[str]]:
    """Validate a script JSON against the expected schema."""
    errors = []

    required_keys = ["className", "methods"]
    for key in required_keys:
        if key not in script_json:
            errors.append(f"Missing required key: {key}")

    if "className" in script_json:
        if not isinstance(script_json["className"], str) or not script_json["className"]:
            errors.append("className must be a non-empty string")

    if "imports" in script_json:
        if not isinstance(script_json["imports"], list):
            errors.append("imports must be a list")

    if "fields" in script_json:
        if not isinstance(script_json["fields"], list):
            errors.append("fields must be a list")
        else:
            for i, field in enumerate(script_json["fields"]):
                if not isinstance(field, dict):
                    errors.append(f"fields[{i}] must be a dictionary")
                elif "name" not in field or "type" not in field:
                    errors.append(f"fields[{i}] missing required keys: name, type")

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
