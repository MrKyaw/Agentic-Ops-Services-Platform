"""Unit tests for runtime mechanics (AO/R13/MT/TS): budgets, guards, quotas, gateway, audit."""

import json

import pytest

from app import quotas
from app.audit import AuditLogger
from app.llm import DisabledBackend, GatewayError, LocalBackend, flip, killed, select
from app.react import Budget, LocalPlanner, ReActRunner
from app.rewoo import ReWOOPlanner, ReWOORunner


def test_react_budget_exhaustion():
    planner = LocalPlanner()
    runner = ReActRunner(planner, Budget(max_iterations=0))
    result = runner.run("do it", {"kb.search": lambda a: "x"})
    assert result.status == "failed"


def test_react_timeout():
    runner = ReActRunner(LocalPlanner(), Budget(timeout_seconds=-1))
    result = runner.run("do it", {"kb.search": lambda a: "x"})
    assert result.status == "failed"
    assert result.usage["iterations"] == 1


def test_react_unknown_tool_recovered():
    class StubPlanner:
        def __init__(self):
            self.calls = 0

        def reason(self, goal, observation, tools):
            self.calls += 1
            if self.calls == 1:
                return {"thought": "t", "action": "ghost.tool", "input": {}}
            return {
                "thought": "t",
                "action": "finish",
                "input": {"answer": observation},
            }

    result = ReActRunner(StubPlanner()).run("anything", {"other": lambda a: "never"})
    assert result.status == "succeeded"
    assert any(s.kind == "tool" and "error" in s.content for s in result.steps)


def test_react_repeat_guard_terminates():
    calls = {"n": 0}

    def repeat(args):
        calls["n"] += 1
        return "same evidence"

    runner = ReActRunner(LocalPlanner(), Budget(max_iterations=8))
    result = runner.run("invoice search", {"kb.search": repeat})
    assert result.status == "succeeded"
    assert calls["n"] <= 2


def test_react_tool_budget_cap():
    runner = ReActRunner(LocalPlanner(), Budget(max_iterations=8, max_tool_calls=0))
    result = runner.run("invoice search", {"kb.search": lambda a: "x"})
    assert result.status == "failed"
    assert result.answer == "tool budget exhausted"


def test_react_approval_checkpoint():
    def write_tool(args):
        return "written"

    write_tool.needs_approval = True  # type: ignore[attr-defined]
    result = ReActRunner(LocalPlanner()).run(
        "open a case please", {"case.create": write_tool}
    )
    assert result.status == "waiting_approval"
    assert result.needs_approval and result.needs_approval["action"] == "case.create"


def test_rewoo_parallel_workers_all_run():
    seen = []

    def tool(name):
        def _run(args):
            seen.append(name)
            return f"evidence-{name}"

        return _run

    runner = ReWOORunner()
    result = runner.run(
        "invoice 88123 policy question?",
        {"kb.search": tool("kb"), "catalog.lookup": tool("cat")},
    )
    assert result.status == "succeeded"
    assert set(seen) == {"kb", "cat"}
    assert "Evidence:" in result.answer
    assert result.usage["model_calls"] == 2


def test_rewoo_unknown_tool_noted():
    runner = ReWOORunner()
    result = runner.run("zzz", {"kb.search": lambda a: "x"})
    assert result.status in ("succeeded", "failed")


def test_rewoo_approval_blocks_solve():
    def write_tool(args):
        return "written"

    write_tool.needs_approval = True  # type: ignore[attr-defined]
    planner = ReWOOPlanner()
    plan = planner.plan("open a case for invoice 1", ["case.create"])
    assert plan.steps and plan.steps[0]["tool"] == "case.create"
    runner = ReWOORunner(planner)
    result = runner.run("open a case for invoice 1", {"case.create": write_tool})
    assert result.status == "waiting_approval"


def test_quotas_allow_and_deny():
    quotas.STATE.buckets.clear()
    assert quotas.allow("t1", 2, now=1000.0) is True
    assert quotas.allow("t1", 2, now=1000.5) is True
    assert quotas.allow("t1", 2, now=1001.0) is False
    assert quotas.allow("t1", 2, now=1100.0) is True  # refilled


def test_quotas_capacity_change_resets():
    quotas.STATE.buckets.clear()
    assert quotas.allow("t2", 1, now=1000.0) is True
    assert quotas.allow("t2", 60, now=1000.0) is True


def test_estimate_and_cost():
    assert quotas.estimate_tokens("") == 1
    assert quotas.estimate_tokens("a b c") >= 3
    assert quotas.cost_usd(0, 0) == 0.0
    assert quotas.cost_usd(1000, 1000) == pytest.approx(0.004)


def test_gateway_select_and_kill():
    backend = select("t", "a", {})
    assert isinstance(backend, LocalBackend)
    flip("tenant:t", True)
    try:
        assert killed("tenant:t") is True
        assert isinstance(select("t", "a", {}), DisabledBackend)
    finally:
        flip("tenant:t", False)
    assert killed("tenant:t") is False


def test_gateway_platform_kill():
    flip("platform", True)
    try:
        assert isinstance(select("any", "any", {}), DisabledBackend)
    finally:
        flip("platform", False)


def test_gateway_unknown_model():
    with pytest.raises(GatewayError):
        select("t", "a", {"primary": "mystery-model"})


def test_audit_chain_and_nested_redact(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit = AuditLogger(str(log))
    first = audit.record(
        "t", "actor", "a.one", "r", "success", {"nested": {"token": "s3cr3t"}}
    )
    second = audit.record("t", "actor", "a.two", "r", "success", {})
    assert second["prev"] == first["hash"]
    assert first["hash"] != second["hash"]
    lines = open(log, encoding="utf-8").read()
    assert "s3cr3t" not in lines
    assert json.loads(lines.split("\n")[0])["fields"]["nested"]["token"] == "***"
