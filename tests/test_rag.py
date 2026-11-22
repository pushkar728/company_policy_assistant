from policy_assistant.indexer import index_directory
from policy_assistant.llm import ChatMessage, LLMError
from policy_assistant.rag import NOT_FOUND_MESSAGE, PolicyAssistant, build_user_prompt


class FakeLLM:
    provider, model = "fake", "fake-1"

    def __init__(self, reply="Fake answer [S1]", fail=False):
        self.reply, self.fail, self.calls = reply, fail, []

    def complete(self, system, messages, temperature=0.1):
        self.calls.append((system, messages))
        if self.fail:
            raise LLMError("boom")
        return self.reply

    def stream(self, system, messages, temperature=0.1):
        self.calls.append((system, messages))
        yield from self.reply.split(" ")


def make_assistant(store, settings, llm=None):
    index_directory(store, settings.sample_dir, settings)
    return PolicyAssistant(store, llm or FakeLLM(), settings)


def test_answer_uses_retrieved_context_and_returns_sources(store, settings):
    llm = FakeLLM()
    assistant = make_assistant(store, settings, llm)
    text, sources = assistant.answer("How many sick leave days per year?")
    assert text == "Fake answer [S1]"
    assert sources and sources[0].file == "Leave_Policy.pdf"
    _, messages = llm.calls[-1]
    assert "[S1]" in messages[-1].content and "Employee question" in messages[-1].content


def test_irrelevant_question_returns_not_found_without_calling_llm(store, settings):
    strict = type(settings)(**{**settings.__dict__, "max_distance": 0.05})
    llm = FakeLLM()
    assistant = make_assistant(store, strict, llm)
    text, sources = assistant.answer("What is the capital of Mars?")
    assert text == NOT_FOUND_MESSAGE and sources == [] and llm.calls == []


def test_follow_up_is_rewritten_using_history(store, settings):
    llm = FakeLLM(reply="How many sick leave days do managers get?")
    assistant = make_assistant(store, settings, llm)
    history = [ChatMessage("user", "How many sick leave days?"), ChatMessage("assistant", "10 days.")]
    retrieval = assistant.retrieve("what about managers?", history)
    assert retrieval.standalone_question == "How many sick leave days do managers get?"


def test_rewrite_failure_falls_back_to_original_question(store, settings):
    assistant = make_assistant(store, settings, FakeLLM(fail=True))
    history = [ChatMessage("user", "hi"), ChatMessage("assistant", "hello")]
    assert assistant.rewrite_question("sick leave?", history) == "sick leave?"


def test_no_history_means_no_rewrite_call(store, settings):
    llm = FakeLLM()
    assistant = make_assistant(store, settings, llm)
    assistant.retrieve("sick leave?", [])
    assert llm.calls == []


def test_stream_answer_yields_tokens_and_handles_empty_sources(store, settings):
    assistant = make_assistant(store, settings)
    sources = assistant.retrieve("hotel limit per night").sources
    assert "".join(assistant.stream_answer("q", [], sources)).startswith("Fake")
    assert list(assistant.stream_answer("q", [], [])) == [NOT_FOUND_MESSAGE]


def test_history_is_trimmed(store, settings):
    llm = FakeLLM()
    assistant = make_assistant(store, settings, llm)
    history = [ChatMessage("user" if i % 2 == 0 else "assistant", f"m{i}") for i in range(20)]
    sources = assistant.retrieve("hotel stay maximum per night in Tier 1 cities").sources
    assert sources
    list(assistant.stream_answer("q", history, sources))
    _, messages = llm.calls[-1]
    assert len(messages) == settings.max_history_messages + 1


def test_prompt_numbers_every_source(store, settings):
    assistant = make_assistant(store, settings)
    sources = assistant.retrieve("travel approval").sources
    prompt = build_user_prompt("q?", sources)
    for i in range(1, len(sources) + 1):
        assert f"[S{i}]" in prompt
