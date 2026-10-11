"""Model gateway (AO-17): policy-driven selection with fallback and kill switches.

Backends implement `generate(prompt, budget) -> dict`. Phase 1 ships the local
deterministic backend; hosted backends register here when model approvals (O1)
land. Kill switches are admin-flipped at agent, tenant, or platform level with
immediate effect (TS-3, local scope).
"""


class GatewayError(Exception):
    pass


class LocalBackend:
    name = "local-standin"

    def generate(self, prompt: str, budget: dict) -> dict:
        return {
            "text": prompt[:2000],
            "model": self.name,
            "tokens_in": len(prompt.split()),
            "tokens_out": 0,
        }


class DisabledBackend:
    def __init__(self, name: str) -> None:
        self.name = name

    def generate(self, prompt: str, budget: dict) -> dict:
        raise GatewayError(f"backend {self.name} is kill-switched")


KILL_SWITCHES: set[str] = set()  # entries: platform | tenant:<id> | agent:<tenant>:<id>


def killed(scope: str) -> bool:
    return "platform" in KILL_SWITCHES or scope in KILL_SWITCHES


def select(tenant: str, agent: str, policy: dict) -> object:
    for scope in (f"agent:{tenant}:{agent}", f"tenant:{tenant}", "platform"):
        if killed(scope):
            return DisabledBackend(scope)
    primary = (policy or {}).get("primary", "local-standin")
    if primary == "local-standin":
        return LocalBackend()
    raise GatewayError(f"model {primary} not approved for this deployment")


def flip(scope: str, on: bool) -> None:
    if on:
        KILL_SWITCHES.add(scope)
    else:
        KILL_SWITCHES.discard(scope)
