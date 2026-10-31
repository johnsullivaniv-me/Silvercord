from types import SimpleNamespace

import pytest

from silvercord.writer import SYSTEM_PROMPT, Chronicler, WriterError, word_count


def resp(text, stop="end_turn", model="claude-sonnet-5-5"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
        stop_reason=stop, model=model,
    )


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        outer = self

        class _Msgs:
            def create(self, **kw):
                outer.calls.append(kw)
                return outer.responses.pop(0)

        self.messages = _Msgs()
        self.beta = SimpleNamespace(messages=_Msgs())


def words(n):
    return " ".join(["saga"] * n)


def test_request_shape_for_default_model():
    client = FakeClient([resp(words(200))])
    entry = Chronicler("claude-sonnet-5-5", client=client).write("FACTS HERE")
    kw = client.calls[0]
    assert kw["model"] == "claude-sonnet-5-5"
    assert kw["fallbacks"] == "default" and kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["output_config"] == {"effort": "medium"}
    assert kw["system"] == SYSTEM_PROMPT
    assert "FACTS HERE" in kw["messages"][0]["content"]
    assert "thinking" not in kw and "temperature" not in kw
    assert entry.words == 200 and entry.attempts == 1


def test_older_model_gets_plain_request():
    client = FakeClient([resp(words(180))])
    Chronicler("claude-3-haiku-legacy", client=client).write("f")
    kw = client.calls[0]
    assert "fallbacks" not in kw and "output_config" not in kw


def test_retry_when_length_is_off():
    client = FakeClient([resp(words(400)), resp(words(210))])
    entry = Chronicler("claude-sonnet-5-5", client=client).write("f")
    assert entry.attempts == 2 and entry.words == 210
    assert "400 words" in client.calls[1]["messages"][-1]["content"]


def test_refusal_raises():
    client = FakeClient([resp("", stop="refusal")])
    with pytest.raises(WriterError, match="refusal"):
        Chronicler("claude-sonnet-5-5", client=client).write("f")


def test_word_count():
    assert word_count("Grukk's axe—sharp, mostly. Zen’jah laughed.") == 6


def test_auth_errors_are_fatal():
    class AuthenticationError(Exception):
        pass

    class Boom(FakeClient):
        def __init__(self):
            super().__init__([])

            def create(**kw):
                raise AuthenticationError("invalid x-api-key")

            self.beta = SimpleNamespace(messages=SimpleNamespace(create=create))

    with pytest.raises(WriterError) as ei:
        Chronicler("claude-sonnet-5-5", client=Boom()).write("f")
    assert ei.value.fatal and "ANTHROPIC_API_KEY" in str(ei.value)


def test_fallback_rejection_degrades_gracefully():
    class BadRequestError(Exception):
        pass

    client = FakeClient([resp(words(200))])
    attempts = []

    def beta_create(**kw):
        attempts.append(kw)
        raise BadRequestError("fallbacks: unknown parameter")

    client.beta = SimpleNamespace(messages=SimpleNamespace(create=beta_create))
    entry = Chronicler("claude-sonnet-5-5", client=client).write("f")
    assert len(attempts) == 1 and entry.words == 200
    assert "fallbacks" not in client.calls[0]
