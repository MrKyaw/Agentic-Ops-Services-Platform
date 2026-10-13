"""Example: classify, ask grounded, run an agent. Needs API_URL, API_TOKEN, API_TENANT env vars."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from platform_client import PlatformClient

client = PlatformClient(
    os.environ["API_URL"], os.environ["API_TOKEN"], os.environ["API_TENANT"]
)
print("classify:", client.classify("Why was invoice 88123 flagged?")["intent_id"])
print(
    "query:",
    str(client.query("kb-policy", "escalation policy refunds")["answer"])[:120],
)
print(
    "run:",
    client.run(
        "pilot-triage", "Why was invoice 88123 flagged?", idempotency_key="example-1"
    )["status"],
)
