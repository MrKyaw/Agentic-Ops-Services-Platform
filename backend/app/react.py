"""ReAct runtime skeleton (AO-2, AO-5..AO-11, AO-13, AO-15, AO-16): reason/act/observe loop.

Model backend interface is provider-agnostic (AO-17). Phase 1 ships a deterministic
local planner for dev/tests; hosted-model backends arrive with model approvals (O1).
Budgets, timeouts, traces, HITL checkpoints, and idempotent tool calls are enforced
regardless of backend.
"""

import json
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Budget:
    max_iterations: int = 8
    timeout_seconds: int = 90
    max_tool_calls: int = 12


@dataclass
class Step:
    kind: str
    content: dict


@dataclass
class RunResult:
    status: str
    answer: str
    steps: list[Step] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    needs_approval: dict | None = None


class LocalPlanner:
    """Deterministic stand-in backend (NOT an LLM): keyword-driven act selection for tests."""

    def reason(self, goal: str, observation: str, tools: list[str]) -> dict:
        lowered = (goal + " " + observation).lower()
        available = set(tools)
        if not observation:
            if (
                "open a case" in lowered or "create a case" in lowered
            ) and "case.create" in available:
                return {
                    "thought": "explicit case request",
                    "action": "case.create",
                    "input": {"query": goal},
                }
        if (
            "search" in lowered or "policy" in lowered or "invoice" in lowered
        ) and "kb.search" in available:
            return {
                "thought": "need evidence",
                "action": "kb.search",
                "input": {"query": goal},
            }
        if (
            "lookup" in lowered or "amount" in lowered or "case" in lowered
        ) and "catalog.lookup" in available:
            return {
                "thought": "need record",
                "action": "catalog.lookup",
                "input": {"query": goal},
            }
        if "case.create" in available and ("case" in lowered):
            return {
                "thought": "case intent without lookup path",
                "action": "case.create",
                "input": {"query": goal},
            }
        return {
            "thought": "sufficient context",
            "action": "finish",
            "input": {"answer": observation or goal},
        }


class ReActRunner:
    def __init__(self, planner: LocalPlanner, budget: Budget | None = None) -> None:
        self.planner = planner
        self.budget = budget or Budget()

    def run(
        self,
        goal: str,
        tools: dict[str, "callable"],
        approve: "callable | None" = None,
    ) -> RunResult:
        started = time.time()
        steps: list[Step] = []
        observation, tool_calls = "", 0
        iterations = 0
        seen_actions: set = set()
        while iterations < self.budget.max_iterations:
            iterations += 1
            if time.time() - started > self.budget.timeout_seconds:
                return RunResult("failed", "", steps, {"iterations": iterations}, None)
            decision = self.planner.reason(goal, observation, sorted(tools))
            steps.append(Step("model", decision))
            action = decision.get("action", "finish")
            if action == "finish":
                answer = str(decision.get("input", {}).get("answer", observation))
                return RunResult(
                    "succeeded",
                    answer,
                    steps,
                    {"iterations": iterations, "tool_calls": tool_calls},
                )
            if tool_calls >= self.budget.max_tool_calls:
                return RunResult(
                    "failed", "tool budget exhausted", steps, {"iterations": iterations}
                )
            handler = tools.get(action)
            if handler is None:
                observation = f"unknown tool {action}"
                steps.append(Step("tool", {"error": observation}))
                continue
            signature = (action, json.dumps(decision.get("input", {}), sort_keys=True))
            if signature in seen_actions:
                # Anti-runaway (R13): identical repeat means no progress; finish with context.
                steps.append(Step("tool", {"repeated_action": action}))
                return RunResult(
                    "succeeded",
                    observation or goal,
                    steps,
                    {"iterations": iterations, "tool_calls": tool_calls},
                )
            seen_actions.add(signature)
            if getattr(handler, "needs_approval", False):
                token = uuid.uuid4().hex[:12]
                return RunResult(
                    "waiting_approval",
                    "",
                    steps,
                    {"iterations": iterations},
                    {
                        "token": token,
                        "action": action,
                        "input": decision.get("input", {}),
                    },
                )
            tool_calls += 1
            observation = str(handler(decision.get("input", {})))
            steps.append(
                Step("tool", {"action": action, "observation": observation[:2000]})
            )
        return RunResult(
            "failed", "max iterations reached", steps, {"iterations": iterations}
        )
