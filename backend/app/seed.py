"""Synthetic seed data (DG-5: never production content). Idempotent."""

from .db import Store
from .rag import chunk_text

INTENTS = [
    {
        "id": "invoice.exception.triage",
        "workflow": "invoice-triage",
        "examples": [
            "Why was invoice 88123 flagged for exception?",
            "Triage the mismatched invoice from this morning",
            "Which invoices need exception review today?",
        ],
        "keywords": ["invoice", "exception", "triage", "flagged"],
        "min_confidence": 0.82,
    },
    {
        "id": "policy.qa.ask",
        "workflow": "policy-qa",
        "examples": [
            "What are the themes across escalation policies?",
            "Summarize the refund approval policy",
            "What does the escalation policy say about outages?",
        ],
        "keywords": ["policy", "escalation", "refund"],
        "min_confidence": 0.8,
    },
    {
        "id": "case.create",
        "workflow": "case-intake",
        "examples": [
            "Open a case for the mismatched amount on invoice 1024",
            "Create a support case about billing",
        ],
        "keywords": ["open a case", "create a case", "support case"],
        "min_confidence": 0.85,
    },
]

DOCS = [
    (
        "doc-escalation",
        "Escalation Policy",
        "Escalation policy: severity-one outages page the on-call lead within five minutes. "
        "Refunds above five hundred require duty-manager approval. All exceptions are logged "
        "with invoice references for audit. Invoice mismatches route to the triage queue.",
    ),
    (
        "doc-triage",
        "Invoice Triage Guide",
        "Invoice triage: flagged invoices are reviewed for amount mismatch, missing purchase "
        "orders, and duplicate billing. Exception handling time is measured from flag to "
        "resolution. Cases are opened for amounts the analyst cannot clear directly.",
    ),
    (
        "doc-refunds",
        "Refund Approval Policy",
        "Refund policy: approvals depend on amount tiers. Small refunds are automatic, large "
        "refunds need manager sign-off. Policy questions are answered with citations to this "
        "document and the escalation policy.",
    ),
]


def seed(store: Store, tenant: str, kb: str = "kb-policy") -> None:
    for intent in INTENTS:
        store.intent_save(
            tenant,
            intent["id"],
            intent["workflow"],
            intent["examples"],
            intent["keywords"],
            intent["min_confidence"],
        )
    for did, title, body in DOCS:
        store.doc_save(tenant, did, kb, title, ["analyst"], source="synthetic-seed-v1")
        for seq, chunk in enumerate(chunk_text(body)):
            store.chunk_save(
                tenant,
                f"{did}-c{seq}",
                kb,
                did,
                seq,
                chunk,
                {"source": "synthetic-seed-v1", "doc": did},
            )


TEMPLATES = [
    {
        "id": "document-intake",
        "name": "Document intake and classification",
        "description": "Classify incoming documents and route exceptions.",
        "manifest": {"pattern": "react", "tools": ["kb.search", "catalog.lookup"]},
    },
    {
        "id": "case-triage",
        "name": "Case triage with approval",
        "description": "Triage flagged items, opening cases only with human approval.",
        "manifest": {"pattern": "react", "tools": ["kb.search", "case.create"]},
    },
    {
        "id": "policy-qa",
        "name": "Policy Q&A with citations",
        "description": "Answer policy questions grounded in the knowledge base.",
        "manifest": {"pattern": "rewoo", "tools": ["kb.search"]},
    },
]


def seed_templates(store: Store) -> None:
    for template in TEMPLATES:
        store._write(
            "INSERT INTO workflow_templates (id, name, description, manifest) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING",
            (
                template["id"],
                template["name"],
                template["description"],
                __import__("json").dumps(template["manifest"]),
            ),
        )
