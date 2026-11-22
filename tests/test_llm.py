import pytest

from policy_assistant.llm import LLMError, available_providers, create_llm, provider_key


def test_available_providers_reads_environment():
    assert available_providers({}) == []
    assert available_providers({"GROQ_API_KEY": "k"}) == ["groq"]
    assert available_providers({"GROQ_API_KEY": " ", "GEMINI_API_KEY": "g"}) == ["gemini"]
    assert provider_key("gemini", {"GEMINI_API_KEY": " abc "}) == "abc"


def test_create_llm_validates_input(settings):
    with pytest.raises(LLMError):
        create_llm("openai", "key", settings)
    with pytest.raises(LLMError):
        create_llm("groq", "  ", settings)


def test_create_llm_builds_clients_without_network(settings):
    assert create_llm("groq", "dummy", settings).provider == "groq"
    assert create_llm("gemini", "dummy", settings).provider == "gemini"
