import pytest

from prompts.java_automation_feedback_agent import SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT
from prompts.java_json_script_prompts import (
    SYSTEM_INSTRUCTION_API_SCRIPT_JSON,
    SYSTEM_INSTRUCTION_COMPLEX_SCRIPT_MODIFICATION_JSON,
    SYSTEM_INSTRUCTION_UI_SCRIPT_JSON,
)


@pytest.mark.parametrize(
    "template, fields",
    [
        (SYSTEM_INSTRUCTION_API_SCRIPT_JSON, {"FEATURE_FILE": "F", "USER_ADDITIONAL_INPUT": "U"}),
        (SYSTEM_INSTRUCTION_UI_SCRIPT_JSON, {"FEATURE_FILE": "F", "USER_ADDITIONAL_INPUT": "U"}),
        (SYSTEM_INSTRUCTION_COMPLEX_SCRIPT_MODIFICATION_JSON, {"CURRENT_SCRIPT_JSON": "J", "USER_REQUEST": "R"}),
        (SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT, {"CURRENT_SCRIPT": "S", "CHAT_HISTORY": "H", "USER_MESSAGE": "M"}),
    ],
)
def test_format_templates_accept_exactly_their_fields(template, fields):
    rendered = template.format(**fields)
    for value in fields.values():
        assert value in rendered


def test_cucumber_placeholders_render_with_single_braces():
    for template in (SYSTEM_INSTRUCTION_API_SCRIPT_JSON, SYSTEM_INSTRUCTION_UI_SCRIPT_JSON):
        rendered = template.format(FEATURE_FILE="F", USER_ADDITIONAL_INPUT="U")
        assert "{{" not in rendered.replace('{{"', "")
    assert "{string}" in SYSTEM_INSTRUCTION_API_SCRIPT_JSON.format(FEATURE_FILE="F", USER_ADDITIONAL_INPUT="U")


@pytest.mark.parametrize("template", [SYSTEM_INSTRUCTION_API_SCRIPT_JSON, SYSTEM_INSTRUCTION_UI_SCRIPT_JSON])
def test_schema_example_is_valid_json_that_renders_to_java(template):
    import json

    from core.java_json import json_to_java

    rendered = template.format(FEATURE_FILE="F", USER_ADDITIONAL_INPUT="U")
    start = rendered.index('{\n    "package"')
    end = rendered.index("\n}\n", start) + 2
    java = json_to_java(json.loads(rendered[start:end]))
    assert '\\"' not in java.split("@", 1)[1].split("\n", 1)[1], "method bodies must not contain escaped quotes"
