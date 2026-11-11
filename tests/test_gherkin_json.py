from core.gherkin_json import (
    apply_feature_modifications,
    gherkin_to_json,
    has_scenario_id_gaps,
    json_to_gherkin,
    normalize_feature_json,
    renumber_scenario_ids,
    validate_gherkin_json,
)
from core.scenario_parser import GherkinScenarioParser

FEATURE = """@auth
Feature: Login

  Users sign in with email and password.

  Background:
    Given the login page is open

  @smoke
  Scenario: Valid credentials
    When the user signs in as "alice@example.com"
    Then the inbox is shown

  Scenario Outline: Invalid email
    When the user enters "<email>"
    Then the error "<message>" is shown

    Examples:
      | email | message |
      | foo | Invalid email |
      |  | Email is required |"""


def test_gherkin_round_trip_is_lossless():
    """FEATURE is written in the canonical layout json_to_gherkin produces."""
    parsed = gherkin_to_json(FEATURE)
    assert json_to_gherkin(parsed) == FEATURE


def test_gherkin_to_json_structure():
    parsed = gherkin_to_json(FEATURE)
    assert parsed["feature"] == {"name": "Login", "tags": ["@auth"], "description": "Users sign in with email and password."}
    assert parsed["background"]["steps"] == [{"type": "Given", "text": "the login page is open"}]
    outline = parsed["scenarios"][1]
    assert outline["id"] == "scenario_2"
    assert outline["type"] == "Scenario Outline"
    assert outline["examples"]["headers"] == ["email", "message"]
    assert outline["examples"]["rows"][1] == ["", "Email is required"]
    assert validate_gherkin_json(parsed) == (True, [])


def test_modifications_touch_only_the_targeted_paths():
    original = gherkin_to_json(FEATURE)
    updated = apply_feature_modifications(
        original,
        [
            {"op": "replace", "path": "scenarios/0/name", "value": "Valid login"},
            {"op": "add", "path": "scenarios/0/steps/-", "value": {"type": "And", "text": "a session cookie is set"}},
            {"op": "remove", "path": "scenarios/1/examples/rows/0"},
            {"op": "replace", "path": "scenarios/9/name", "value": "out of range is ignored"},
        ],
    )
    assert updated["scenarios"][0]["name"] == "Valid login"
    assert updated["scenarios"][0]["steps"][-1]["text"] == "a session cookie is set"
    assert len(updated["scenarios"][1]["examples"]["rows"]) == 1
    assert updated["scenarios"][1]["steps"] == original["scenarios"][1]["steps"]
    assert original["scenarios"][0]["name"] == "Valid credentials", "input must not be mutated"


def test_scenario_ids_are_renumbered_after_a_removal():
    feature = apply_feature_modifications(gherkin_to_json(FEATURE), [{"op": "remove", "path": "scenarios/0"}])
    assert has_scenario_id_gaps(feature)
    renumbered, mapping = renumber_scenario_ids(feature)
    assert mapping == {"scenario_2": "scenario_1"}
    assert not has_scenario_id_gaps(renumbered)


def test_normalize_accepts_llm_style_examples():
    feature = {
        "feature": {"name": "X", "description": ["line 1", "line 2"], "tags": "@one"},
        "scenarios": [{"name": "S", "steps": [], "examples": [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]}],
    }
    normalized = normalize_feature_json(feature)
    assert normalized["feature"]["description"] == "line 1\nline 2"
    assert normalized["feature"]["tags"] == ["@one"]
    assert normalized["scenarios"][0]["examples"] == {"headers": ["a", "b"], "rows": [["1", "2"], ["3", "4"]]}


def test_scenario_parser_splits_one_block_per_scenario():
    blocks = GherkinScenarioParser().parse(FEATURE)
    assert len(blocks) == 2
    assert blocks[0].strip().startswith("Scenario: Valid credentials")
    assert blocks[1].strip().startswith("Scenario Outline: Invalid email")
    assert "| foo | Invalid email |" in blocks[1]
