"""PII detection (PV-2) and DLP output scanning (SC-9): pattern-based, labeled heuristic.

Covers email, phone, SSN-style sequences, and credential-shaped assignments. It is a
safety net, not a guarantee — data-classification policy still governs routing, and
limits are documented and tested (including a Unicode homoglyph note in tests).
"""

import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}(?!\d)"
)
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
SECRET_ASSIGN = re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*\S+")


def scan(text: str) -> list[dict]:
    findings = []
    for kind, pattern in (
        ("email", EMAIL),
        ("phone", PHONE),
        ("ssn", SSN),
        ("secret", SECRET_ASSIGN),
    ):
        for match in pattern.finditer(text or ""):
            findings.append({"type": kind, "span": [match.start(), match.end()]})
    return findings


def redact_text(text: str) -> str:
    redacted = text or ""
    for _, pattern in (
        ("email", EMAIL),
        ("phone", PHONE),
        ("ssn", SSN),
        ("secret", SECRET_ASSIGN),
    ):
        redacted = pattern.sub("[redacted]", redacted)
    return redacted
