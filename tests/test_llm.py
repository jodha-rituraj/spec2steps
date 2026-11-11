import pytest

from core.llm import OPENROUTER_URL, get_llm


def test_openrouter_uses_openai_compatible_client(monkeypatch):
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    llm = get_llm("openrouter", api_key="sk-or-test")
    assert llm.openai_api_base == OPENROUTER_URL
    assert llm.model_name == "openai/gpt-oss-120b"
    assert get_llm("openrouter", api_key="sk-or-test", model="some/model").model_name == "some/model"


@pytest.mark.parametrize("provider, env", [("groq", "GROQ_API_KEY"), ("openrouter", "OPENROUTER_API_KEY")])
def test_missing_key_raises_a_readable_error(monkeypatch, provider, env):
    monkeypatch.delenv(env, raising=False)
    with pytest.raises(ValueError, match="API key"):
        get_llm(provider)
