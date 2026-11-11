"""Drives the Streamlit app end to end with a scripted fake LLM (no network)."""
import json
from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from streamlit.testing.v1 import AppTest

import core.llm

APP = str(Path(__file__).resolve().parent.parent / "app.py")

FEATURE = {
    "feature": {"name": "Login"},
    "scenarios": [
        {
            "id": "scenario_1",
            "type": "Scenario",
            "name": "Valid login",
            "steps": [
                {"type": "Given", "text": "the login API is available"},
                {"type": "When", "text": "the user logs in with valid credentials"},
                {"type": "Then", "text": "the response status is 200"},
            ],
        }
    ],
}

SCRIPT = {
    "package": "com.example.steps",
    "imports": ["io.restassured.RestAssured"],
    "className": "LoginSteps",
    "fields": [{"modifiers": ["private"], "type": "Response", "name": "response"}],
    "methods": [
        {
            "annotations": [{"name": "Given", "value": "the login API is available"}],
            "modifiers": ["public"],
            "returnType": "void",
            "name": "theLoginApiIsAvailable",
            "parameters": [],
            "body": ['RestAssured.baseURI = "https://api.example.com";'],
        }
    ],
}


def use_fake_llm(monkeypatch, responses):
    llm = FakeListChatModel(responses=[r if isinstance(r, str) else json.dumps(r) for r in responses])
    monkeypatch.setattr(core.llm, "get_llm", lambda *args, **kwargs: llm)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    return llm


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception, at.exception


def send_chat(at, message):
    next(t for t in at.text_input if t.label == "Message").input(message)
    click(at, "Send")


def code_blocks(at, language):
    return [c.value for c in at.code if c.language == language]


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def test_requirements_to_refined_java(monkeypatch):
    use_fake_llm(
        monkeypatch,
        [
            FEATURE,
            "PERFECT",
            {
                "intent": "change",
                "explanation": "Renamed the scenario.",
                "modifications": [{"op": "replace", "path": "scenarios/0/name", "value": "Successful login"}],
            },
            "PERFECT",
            SCRIPT,
            {
                "intent": "change",
                "explanation": "Renamed the class.",
                "modifications": [{"action": "rename_class", "new_name": "LoginApiTests"}],
            },
        ],
    )
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()

    at.text_area[0].input("Users must be able to log in through the API.")
    click(at, "Generate Feature File & Verification")
    assert any("Scenario: Valid login" in c for c in code_blocks(at, "gherkin"))

    send_chat(at, "Rename the scenario to Successful login")
    diff = next(c for c in code_blocks(at, "diff"))
    assert diff.startswith("--- current\n+++ proposed\n@@")
    assert "-  Scenario: Valid login\n+  Scenario: Successful login" in diff
    click(at, "Apply")
    assert any("Scenario: Successful login" in c for c in code_blocks(at, "gherkin"))
    assert any("Version 2 of 2" in m.value for m in at.markdown)

    click(at, "Accept & Proceed to Scripts")
    click(at, "Skip Edit & Generate Scripts")
    click(at, "Generate Automation Scripts")
    java = code_blocks(at, "java")
    assert any("public class GeneratedTests {" in c and "theLoginApiIsAvailable" in c for c in java)

    send_chat(at, "Rename the class to LoginApiTests")
    assert any("+public class LoginApiTests {" in c for c in code_blocks(at, "diff"))
    click(at, "Apply")
    assert any("public class LoginApiTests {" in c for c in code_blocks(at, "java"))

    click(at, "Start Over")
    assert not at.session_state["feature_files"]


def test_scripts_only_workflow(monkeypatch):
    use_fake_llm(monkeypatch, [SCRIPT])
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()

    next(r for r in at.radio if r.label == "What to generate").set_value("Scripts Only").run()
    at.text_area[0].input(
        "Feature: Login\n\n  Scenario: Valid login\n    Given the login API is available\n"
    )
    click(at, "Generate Scripts from Feature File")
    click(at, "Generate Automation Scripts")
    assert any("public class GeneratedTests {" in c for c in code_blocks(at, "java"))


def test_generation_is_blocked_without_a_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.text_area[0].input("Some requirement")
    click(at, "Generate Feature File & Verification")
    assert any("Configure an LLM provider" in e.value for e in at.error)


def test_model_errors_are_shown_not_raised(monkeypatch):
    class FailingModel(FakeListChatModel):
        def _call(self, *args, **kwargs):
            raise RuntimeError("Rate limit reached")

    llm = FailingModel(responses=["unused"])
    monkeypatch.setattr(core.llm, "get_llm", lambda *args, **kwargs: llm)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.text_area[0].input("Some requirement")
    click(at, "Generate Feature File & Verification")
    assert any("Model call failed: Rate limit reached" in e.value for e in at.error)


def test_openrouter_provider_can_be_selected(monkeypatch):
    calls = []
    llm = FakeListChatModel(responses=[json.dumps(FEATURE), "PERFECT"])
    monkeypatch.setattr(core.llm, "get_llm", lambda *args, **kwargs: calls.append(kwargs) or llm)
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.selectbox[0].set_value("OpenRouter").run()
    at.text_area[0].input("Users must be able to log in.")
    click(at, "Generate Feature File & Verification")
    assert calls[-1] == {"provider": "openrouter", "api_key": "sk-or-test", "model": None}
    assert any("Scenario: Valid login" in c for c in code_blocks(at, "gherkin"))
