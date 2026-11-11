import re
from typing import List, Optional, Tuple

from core.java_json import retarget_class_refs

INDENT = "    "


class JavaFileMerger:
    """
    Merges per-scenario Java step-definition classes into one class:
    imports are unioned, fields de-duplicated by signature, methods concatenated.
    """

    def __init__(self, merged_class_name: Optional[str] = None):
        self.merged_class_name = merged_class_name

    def merge(self, java_files: List[str]) -> str:
        packages, imports, fields, methods, source_classes = set(), set(), {}, [], []
        class_name = self.merged_class_name

        for content in java_files:
            package = re.search(r"^package\s+[\w.]+;", content, re.MULTILINE)
            if package:
                packages.add(package.group(0))
            imports.update(re.findall(r"^import\s+(?:static\s+)?[\w.*]+;", content, re.MULTILINE))
            match = re.search(r"public\s+class\s+(\w+)", content)
            if match:
                source_classes.append(match.group(1))
                class_name = class_name or match.group(1)

            class_fields, class_methods = _split_members(content)
            for field in class_fields:
                fields.setdefault(_field_signature(field), field)
            methods.extend(class_methods)

        class_name = class_name or "MergedClass"
        for source in source_classes:
            fields = {k: retarget_class_refs(v, source, class_name) for k, v in fields.items()}
            methods = [retarget_class_refs(m, source, class_name) for m in methods]

        lines = []
        if packages:
            lines += [sorted(packages)[0], ""]
        if imports:
            lines += sorted(imports) + [""]
        lines += [f"public class {class_name} {{", ""]
        if fields:
            lines += [_reindent(f, INDENT) for f in fields.values()] + [""]
        if methods:
            lines.append("\n\n".join(_reindent(m, INDENT) for m in methods))
        lines.append("}")
        return "\n".join(lines)


def _split_members(content: str) -> Tuple[List[str], List[str]]:
    header = re.search(r"public\s+class\s+\w+[^{]*{", content)
    if not header:
        return [], []

    body = content[header.end():]
    depth = 1
    for i, char in enumerate(body):
        depth += {"{": 1, "}": -1}.get(char, 0)
        if depth == 0:
            body = body[:i]
            break

    fields, methods = [], []
    for member in _members(body.strip()):
        (fields if _is_field(member) else methods).append(member)
    return fields, methods


def _members(class_body: str) -> List[str]:
    """Split a class body into top-level members by tracking brace depth."""
    members, current, depth = [], [], 0
    for line in class_body.split("\n"):
        stripped = line.strip()
        if not stripped and not current:
            continue
        current.append(line)
        depth += line.count("{") - line.count("}")
        if depth == 0 and stripped.endswith((";", "}")):
            members.append(_reindent("\n".join(current)))
            current = []
    if current:
        members.append(_reindent("\n".join(current)))
    return [m for m in members if m.strip()]


def _is_field(member: str) -> bool:
    member = member.strip()
    if member.startswith("@") or re.search(r"\b\w+\s+\w+\s*\([^)]*\)\s*{", member):
        return False
    last_line = member.split("\n")[-1].strip()
    if last_line.endswith(";"):
        return True
    return not last_line.endswith("}") and "{" not in member


def _field_signature(field: str) -> str:
    """'private static Foo bar = ...;' -> 'private static Foo bar', used as the dedupe key."""
    normalized = " ".join(field.split())
    match = re.match(r"((?:public|private|protected|static|final|\s)+)([\w<>.,\s]+?)\s+(\w+)\s*[=;]", normalized)
    if not match:
        return normalized
    return f"{' '.join(match.group(1).split())} {match.group(2).strip()} {match.group(3)}"


def _reindent(code: str, prefix: str = "") -> str:
    """Strip the common leading indentation, then prefix every non-empty line."""
    lines = code.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return code
    margin = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    return "\n".join(prefix + l[margin:] if l.strip() else "" for l in lines)
