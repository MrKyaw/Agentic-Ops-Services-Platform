"""Tenant quotas (MT-4), noisy-neighbor guards (MT-8), cost attribution (MT-5, NF-C1).

Rate limiting is an in-memory token bucket per tenant: correct for single-replica
local/dev operation. Multi-replica deployments must back this with Redis (recorded
as a deployment note, not silently assumed).
"""

import time
from dataclasses import dataclass, field


@dataclass
class Bucket:
    capacity: int
    tokens: float
    updated: float


@dataclass
class QuotaState:
    buckets: dict[str, Bucket] = field(default_factory=dict)
    runs_today: dict[str, tuple[str, int]] = field(default_factory=dict)


STATE = QuotaState()
COST_PER_1K_TOKENS = (
    0.002  # planning rate, exposed via usage records; not a billing claim
)


def allow(tenant: str, rpm: int, now: float | None = None) -> bool:
    now = now if now is not None else time.time()
    bucket = STATE.buckets.get(tenant)
    if bucket is None or bucket.capacity != rpm:
        bucket = Bucket(rpm, float(rpm), now)
        STATE.buckets[tenant] = bucket
    elapsed = now - bucket.updated
    bucket.tokens = min(
        float(bucket.capacity), bucket.tokens + elapsed * (bucket.capacity / 60.0)
    )
    bucket.updated = now
    if bucket.tokens < 1.0:
        return False
    bucket.tokens -= 1.0
    return True


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) + len(text) // 40)


def cost_usd(tokens_in: int, tokens_out: int) -> float:
    return round((tokens_in + tokens_out) / 1000.0 * COST_PER_1K_TOKENS, 6)
