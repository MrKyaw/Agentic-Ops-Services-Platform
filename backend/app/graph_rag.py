"""Knowledge-graph RAG (RG-8) over Neo4j with a heuristic extractor, and extractive
RAPTOR-style summary trees (RG-10).

Honesty notes: entity extraction is pattern-based (capitalized phrases, invoice
IDs, amount mentions), NOT an LLM joint extractor — precision/recall limits are
documented and extraction accuracy is sampled in tests. Summaries are extractive
(centroid sentences), not abstractive. Both upgrade paths (model extractor,
abstractive summarizer) plug in behind these interfaces when approved (O1).
"""

import re
from collections import Counter

from neo4j import GraphDatabase

_CAP = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")
_INV = re.compile(r"\binvoice\s+(\d+)\b", re.IGNORECASE)
STOP = {"The", "All", "For", "With", "Small", "Large", "Refund", "Policy"}


def extract_entities(text: str) -> list[str]:
    found = [m for m in _CAP.findall(text) if m not in STOP and len(m) > 3]
    found += [f"invoice-{m}" for m in _INV.findall(text)]
    seen, out = set(), []
    for entity in found:
        key = entity.lower()
        if key not in seen:
            seen.add(key)
            out.append(entity)
    return out


class GraphStore:
    def __init__(self, uri: str, user: str, password: str) -> None:
        auth = (user, password) if password else None
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self) -> None:
        self.driver.close()

    def ingest_chunk(
        self, tenant: str, chunk_id: str, kb_id: str, text: str
    ) -> list[str]:
        entities = extract_entities(text)
        with self.driver.session() as session:
            session.run(
                "MERGE (c:Chunk {tenant: $tenant, id: $cid}) SET c.kb = $kb",
                tenant=tenant,
                cid=chunk_id,
                kb=kb_id,
            )
            for entity in entities:
                session.run(
                    "MERGE (e:Entity {tenant: $tenant, name: $name}) "
                    "MERGE (c:Chunk {tenant: $tenant, id: $cid}) MERGE (c)-[:MENTIONS]->(e)",
                    tenant=tenant,
                    name=entity,
                    cid=chunk_id,
                )
            for first, second in zip(entities, entities[1:]):
                session.run(
                    "MATCH (a:Entity {tenant: $tenant, name: $first}), (b:Entity {tenant: $tenant, name: $second}) "
                    "MERGE (a)-[r:CO_OCCURS]->(b) SET r.weight = coalesce(r.weight, 0) + 1",
                    tenant=tenant,
                    first=first,
                    second=second,
                )
        return entities

    def neighborhood(self, tenant: str, query: str, limit: int = 8) -> list[dict]:
        terms = extract_entities(query) or query.lower().split()[:4]
        with self.driver.session() as session:
            rows = session.run(
                "MATCH (e:Entity {tenant: $tenant}) WHERE toLower(e.name) IN $terms "
                "MATCH (e)-[r]-(n) RETURN n.name AS name, labels(n) AS labels, "
                "coalesce(r.weight, 1) AS weight ORDER BY weight DESC LIMIT $limit",
                tenant=tenant,
                terms=[t.lower() for t in terms],
                limit=limit,
            )
            return [
                {"name": r["name"], "labels": r["labels"], "weight": r["weight"]}
                for r in rows
            ]

    def community_terms(self, tenant: str, kb_id: str, limit: int = 10) -> list[str]:
        with self.driver.session() as session:
            rows = session.run(
                "MATCH (c:Chunk {tenant: $tenant, kb: $kb})-[:MENTIONS]->(e:Entity {tenant: $tenant}) "
                "RETURN e.name AS name, count(*) AS degree ORDER BY degree DESC LIMIT $limit",
                tenant=tenant,
                kb=kb_id,
                limit=limit,
            )
            return [r["name"] for r in rows]


def extractive_summary(texts: list[str], max_sentences: int = 3) -> str:
    sentences = [
        s.strip()
        for t in texts
        for s in re.split(r"(?<=[.!?])\s+", t)
        if len(s.split()) > 4
    ]
    if not sentences:
        return ""
    df: Counter = Counter()
    tokenized = [[w.lower() for w in re.findall(r"[a-z0-9]+", s)] for s in sentences]
    for toks in tokenized:
        df.update(set(toks))
    n = len(sentences)
    import math

    def score(toks: list[str]) -> float:
        return sum((math.log((1 + n) / (1 + df[t])) + 1.0) for t in set(toks))

    ranked = sorted(
        range(len(sentences)), key=lambda i: score(tokenized[i]), reverse=True
    )
    return " ".join(sentences[i] for i in sorted(ranked[:max_sentences]))
