"""Model gateway (AO-17): policy-driven selection with fallback and kill switches.

Backends implement `generate(prompt, budget) -> dict`. Phase 1 ships the local
deterministic backend; hosted backends register here when model approvals (O1)
land. Kill switches are admin-flipped at agent, tenant, or platform level with
immediate effect (TS-3, local scope).
"""

import json
import urllib.request


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


class OpenRouterBackend:
    """OpenAI-compatible chat backend (OpenRouter). Free-tier models are dev/eval only:
    throttled, rotating, and trainers may retain prompts — never regulated content."""

    name = "openrouter"
    _failures: dict[str, int] = {}
    _open_until: dict[str, float] = {}

    def __init__(
        self, api_key: str, model: str, base_url: str = "https://openrouter.ai/api/v1"
    ) -> None:
        if not api_key:
            raise GatewayError("openrouter backend needs OPENROUTER_API_KEY")
        if not model:
            raise GatewayError("openrouter backend needs a model")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, budget: dict) -> dict:
        import time as _time

        if _time.time() < self._open_until.get(self.model, 0):
            raise GatewayError(f"openrouter circuit open for {self.model}")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": int(budget.get("max_tokens", 512)),
        }
        if budget.get("json_mode"):
            payload["response_format"] = {"type": "json_object"}
        last: Exception | None = None
        for attempt in range(3):
            try:
                return self._call(prompt, payload)
            except GatewayError as exc:
                last = exc
                _time.sleep(min(2.0, 0.25 * (2**attempt)) + 0.05 * attempt)
        self._failures[self.model] = self._failures.get(self.model, 0) + 1
        if self._failures[self.model] >= 5:
            self._open_until[self.model] = _time.time() + 60.0
            self._failures[self.model] = 0
        raise GatewayError(f"openrouter call failed after retries: {last}") from last

    def _call(self, prompt: str, payload: dict) -> dict:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "services-ai-platform",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.load(response)
        except Exception as exc:
            raise GatewayError(f"openrouter transport failed: {exc}") from exc
        try:
            text = body["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise GatewayError(f"openrouter bad response: {exc}") from exc
        usage = body.get("usage") or {}
        return {
            "text": text,
            "model": body.get("model", self.model),
            "tokens_in": usage.get("prompt_tokens", len(prompt.split())),
            "tokens_out": usage.get("completion_tokens", len(text.split())),
        }


KILL_SWITCHES: set[str] = set()  # entries: platform | tenant:<id> | agent:<tenant>:<id>


def killed(scope: str) -> bool:
    return "platform" in KILL_SWITCHES or scope in KILL_SWITCHES


def select(
    tenant: str, agent: str, policy: dict, secrets: dict | None = None
) -> object:
    for scope in (f"agent:{tenant}:{agent}", f"tenant:{tenant}", "platform"):
        if killed(scope):
            return DisabledBackend(scope)
    secrets = secrets or {}
    primary = (policy or {}).get("primary", "local-standin")
    if primary == "local-standin":
        return LocalBackend()
    if primary == "openrouter" or primary.startswith("openrouter/"):
        model = primary.split("/", 1)[1] if "/" in primary else secrets.get("model", "")
        return OpenRouterBackend(
            secrets.get("api_key", ""),
            model,
            secrets.get("base_url", "https://openrouter.ai/api/v1"),
        )
    raise GatewayError(f"model {primary} not approved for this deployment")


def flip(scope: str, on: bool) -> None:
    if on:
        KILL_SWITCHES.add(scope)
    else:
        KILL_SWITCHES.discard(scope)
