"""Smoke-test the Streamlit app headlessly with a fake LLM and the test embedder."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from policy_assistant import llm as llm_module
from tests.conftest import HashingEmbedding

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class FakeLLM(llm_module.BaseLLM):
    provider, model = "fake", "fake"

    def complete(self, system, messages, temperature=0.1):
        return messages[-1].content.splitlines()[-1]

    def stream(self, system, messages, temperature=0.1):
        yield from ["Annual leave is ", "18 days [S1]."]


@pytest.fixture()
def app(monkeypatch, tmp_path):
    from chromadb.utils import embedding_functions

    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(embedding_functions, "DefaultEmbeddingFunction", HashingEmbedding)
    monkeypatch.setattr(llm_module, "create_llm", lambda *a, **k: FakeLLM())
    monkeypatch.setattr("app.create_llm", lambda *a, **k: FakeLLM(), raising=False)
    import streamlit as st

    st.cache_resource.clear()
    return AppTest.from_file(APP, default_timeout=60)


def test_app_loads_and_answers_a_question(app):
    app.run()
    assert not app.exception
    assert any("Company Policy Assistant" in t.value for t in app.title)

    app.chat_input[0].set_value("How many days of annual leave do I get?").run()
    assert not app.exception
    roles = [m.name for m in app.chat_message]
    assert roles == ["user", "assistant"]
    assert "18 days" in app.chat_message[1].markdown[0].value
