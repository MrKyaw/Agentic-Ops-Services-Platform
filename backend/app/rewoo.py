"""ReWOO runtime (AO-3): plan up front with evidence placeholders, execute workers,
solve by synthesis. Fewer model calls than ReAct by construction (plan + solve).

Worker parallelism uses a bounded thread pool (AO-10); independent calls run
concurrently, capped at 4. Solver here is extractive (no generative model in this
deployment); a model-backed solver plugs into `solve()` when approved (O1).
"""

import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

_PLACEHOLDER = re.compile(r"#E\d+")


@dataclass
class Plan:
    steps: list[dict]  # [{tool, input, evidence: "#E1"}]
    plan_text: str


@dataclass
class ReWOOresult:
    status: str
    answer: str
    plan: Plan | None = None
    evidence: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)


class ReWOOPlanner:
    """Deterministic stand-in planner (NOT an LLM): decomposes goals into tool calls."""

    def plan(self, goal: str, tools: list[str]) -> Plan:
        lowered = goal.lower()
        steps: list[dict] = []
        if "kb.search" in tools and any(
            w in lowered for w in ("policy", "invoice", "what", "why", "?")
        ):
            steps.append(
                {
                    "tool": "kb.search",
                    "input": {"query": goal},
                    "evidence": f"#E{len(steps) + 1}",
                }
            )
        if "catalog.lookup" in tools and any(c.isdigit() for c in goal):
            steps.append(
                {
                    "tool": "catalog.lookup",
                    "input": {"query": goal},
                    "evidence": f"#E{len(steps) + 1}",
                }
            )
        if not steps and tools:
            steps.append(
                {"tool": tools[0], "input": {"query": goal}, "evidence": "#E1"}
            )
        text = "\n".join(f"{s['evidence']} = {s['tool']}({s['input']})" for s in steps)
        return Plan(steps, text)


def solve(goal: str, plan: Plan, evidence: dict) -> str:
    parts = [
        f"{step['evidence']}: {evidence.get(step['evidence'], 'no evidence')}"
        for step in plan.steps
    ]
    return f"Plan:\n{plan.plan_text}\nEvidence:\n" + "\n".join(parts)


class ReWOORunner:
    def __init__(
        self, planner: ReWOOPlanner | None = None, max_workers: int = 4
    ) -> None:
        self.planner = planner or ReWOOPlanner()
        self.max_workers = max_workers

    def run(self, goal: str, tools: dict[str, "callable"]) -> ReWOOresult:
        plan = self.planner.plan(goal, sorted(tools))
        evidence: dict[str, str] = {}

        def _exec(step: dict) -> tuple[str, str]:
            handler = tools.get(step["tool"])
            if handler is None:
                return step["evidence"], f"unknown tool {step['tool']}"
            if getattr(handler, "needs_approval", False):
                return step["evidence"], "PENDING_APPROVAL"
            return step["evidence"], str(handler(step["input"]))[:2000]

        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, max(len(plan.steps), 1))
        ) as pool:
            for key, value in pool.map(_exec, plan.steps):
                evidence[key] = value
        if evidence and all(
            v.startswith("unknown tool") or v == "no evidence"
            for v in evidence.values()
        ):
            # Replan once (AO-3): drop the approval-gated tool and retry a reduced plan.
            reduced = {k: v for k, v in tools.items() if k != "case.create"}
            if reduced != tools:
                retry = self.run(goal, reduced)
                retry.usage["replanned"] = True
                return retry
        if any(v == "PENDING_APPROVAL" for v in evidence.values()):
            return ReWOOresult(
                "waiting_approval", "", plan, evidence, {"tool_calls": len(plan.steps)}
            )
        answer = solve(goal, plan, evidence)
        return ReWOOresult(
            "succeeded",
            answer,
            plan,
            evidence,
            {"tool_calls": len(plan.steps), "model_calls": 2},
        )


def run_id() -> str:
    return uuid.uuid4().hex[:12]
