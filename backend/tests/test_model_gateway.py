"""Model gateway tests (AO-17): OpenRouter backend (mocked transport), planner constraints."""

import json

import pytest

from app.llm import GatewayError, OpenRouterBackend, select
from app.react import ModelPlanner


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()

    def __iter__(self):
        yield self.read()


def _fake_urlopen(payload, monkeypatch):
    import app.llm as llm_module

    def fake(request, timeout=90):
        assert "openrouter.ai" in request.full_url
        assert request.headers.get("Authorization", "").startswith("Bearer ")
        return FakeResponse(payload)

    monkeypatch.setattr(llm_module.urllib.request, "urlopen", fake)


def test_openrouter_generate_parses_usage(monkeypatch):
    _fake_urlopen(
        {
            "model": "qwen/qwen-2.5-7b-instruct",
            "choices": [{"message": {"content": "hello"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 1},
        },
        monkeypatch,
    )
    backend = OpenRouterBackend("k", "qwen/qwen-2.5-7b-instruct")
    out = backend.generate("hi", {"max_tokens": 10})
    assert out["text"] == "hello"
    assert (out["tokens_in"], out["tokens_out"]) == (5, 1)


def test_openrouter_transport_failure(monkeypatch):
    import app.llm as llm_module
    import urllib.error

    def boom(request, timeout=90):
        raise urllib.error.URLError("down")

    monkeypatch.setattr(llm_module.urllib.request, "urlopen", boom)
    with pytest.raises(GatewayError, match="openrouter call failed"):
        OpenRouterBackend("k", "m").generate("hi", {})


def test_openrouter_needs_key_and_model():
    with pytest.raises(GatewayError):
        OpenRouterBackend("", "m")
    with pytest.raises(GatewayError):
        OpenRouterBackend("k", "")


def test_select_openrouter_wiring():
    backend = select(
        "t", "a", {"primary": "openrouter/qwen/qwen-2.5-7b-instruct"}, {"api_key": "k"}
    )
    assert isinstance(backend, OpenRouterBackend)
    assert backend.model == "qwen/qwen-2.5-7b-instruct"


def test_model_planner_constrains_unknown_tool():
    class FakeBackend:
        def generate(self, prompt, budget):
            return {
                "text": '{"thought":"t","action":"evil.tool","input":{}}',
                "model": "fake",
                "tokens_in": 1,
                "tokens_out": 1,
            }

    decision = ModelPlanner(FakeBackend()).reason("goal", "", ["kb.search"])
    assert decision["action"] == "finish"
    assert decision.get("constrained") is True


def test_model_planner_accepts_registered_tool():
    class FakeBackend:
        def generate(self, prompt, budget):
            return {
                "text": '{"thought":"need evidence","action":"kb.search","input":{"query":"invoice"}}',
                "model": "fake",
                "tokens_in": 1,
                "tokens_out": 1,
            }

    decision = ModelPlanner(FakeBackend()).reason("invoice?", "", ["kb.search"])
    assert (decision["action"], decision["input"]) == (
        "kb.search",
        {"query": "invoice"},
    )


def test_model_planner_degrades_on_failure():
    class DeadBackend:
        def generate(self, prompt, budget):
            raise GatewayError("down")

    decision = ModelPlanner(DeadBackend()).reason("goal", "ctx", ["kb.search"])
    assert decision["action"] == "finish"
    assert decision["input"] == {"answer": "ctx"}
    assert decision.get("degraded") is True


def test_model_planner_rejects_garbage():
    class GarbageBackend:
        def generate(self, prompt, budget):
            return {
                "text": "not json at all",
                "model": "fake",
                "tokens_in": 1,
                "tokens_out": 1,
            }

    assert (
        ModelPlanner(GarbageBackend()).reason("goal", "ctx", ["kb.search"])["action"]
        == "finish"
    )


def test_openrouter_retries_then_raises(monkeypatch):
    import app.llm as llm_module

    calls = {"n": 0}

    def boom(request, timeout=90):
        calls["n"] += 1
        raise OSError("flaky")

    monkeypatch.setattr(llm_module.urllib.request, "urlopen", boom)
    backend = OpenRouterBackend("k", "retry-model-xyz")
    with __import__("pytest").raises(GatewayError, match="after retries"):
        backend.generate("hi", {})
    assert calls["n"] == 3


def test_openrouter_circuit_opens(monkeypatch):
    import app.llm as llm_module

    monkeypatch.setattr(
        llm_module.urllib.request,
        "urlopen",
        lambda request, timeout=90: (_ for _ in ()).throw(OSError("down")),
    )
    backend = OpenRouterBackend("k", "breaker-model-xyz")
    for _ in range(5):
        try:
            backend.generate("hi", {})
        except GatewayError:
            pass
    with __import__("pytest").raises(GatewayError, match="circuit open"):
        backend.generate("hi", {})
    llm_module.OpenRouterBackend._open_until.clear()
    llm_module.OpenRouterBackend._failures.clear()


def test_model_planner_falls_back_across_backends():
    from app.llm import GatewayError
    from app.react import ModelPlanner

    class DeadBackend:
        def generate(self, prompt, budget):
            raise GatewayError("down")

    class LiveBackend:
        def generate(self, prompt, budget):
            return {
                "text": '{"thought":"t","action":"finish","input":{"answer":"ok"}}',
                "model": "live",
                "tokens_in": 1,
                "tokens_out": 1,
            }

    decision = ModelPlanner([DeadBackend(), LiveBackend()]).reason(
        "goal", "", ["kb.search"]
    )
    assert decision["action"] == "finish"
