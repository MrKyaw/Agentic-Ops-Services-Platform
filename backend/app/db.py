"""Postgres data access. Every query filters on tenant_id (MT-2/MT-3). No ORM: plain parameterized SQL."""

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row


def connect(url: str) -> psycopg.Connection:
    conn = psycopg.connect(url, row_factory=dict_row)
    conn.execute("SET app.tenant = ''")
    return conn


def _j(value: Any) -> str:
    return json.dumps(value or {})


class Store:
    def __init__(self, url: str) -> None:
        self.url = url

    def _one(self, sql: str, params: tuple = ()) -> dict | None:
        with connect(self.url) as conn:
            return conn.execute(sql, params).fetchone()

    def _all(self, sql: str, params: tuple = ()) -> list[dict]:
        with connect(self.url) as conn:
            return list(conn.execute(sql, params).fetchall())

    def _write(self, sql: str, params: tuple = ()) -> None:
        with connect(self.url) as conn:
            conn.execute(sql, params)
            conn.commit()

    # tenants (global table, id is the tenant)
    def tenant_upsert(self, tid: str, name: str, status: str = "active") -> dict:
        self._write(
            "INSERT INTO tenants (id, name, status) VALUES (%s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status",
            (tid, name, status),
        )
        return self.tenant_get(tid) or {}

    def tenant_get(self, tid: str) -> dict | None:
        return self._one("SELECT id, name, status FROM tenants WHERE id = %s", (tid,))

    def tenant_list(self) -> list[dict]:
        return self._all("SELECT id, name, status FROM tenants ORDER BY id")

    # prompts (immutable versions)
    def prompt_save(
        self,
        tenant: str,
        pid: str,
        version: int,
        template: str,
        variables: list,
        by: str,
        risk: str = "low",
    ) -> None:
        self._write(
            "INSERT INTO prompts (tenant_id, id, version, template, variables, created_by, risk) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (tenant, pid, version, template, _j(variables), by, risk),
        )

    def prompt_latest(self, tenant: str, pid: str) -> dict | None:
        return self._one(
            "SELECT tenant_id, id, version, template, variables, status, created_by, risk FROM prompts "
            "WHERE tenant_id = %s AND id = %s ORDER BY version DESC LIMIT 1",
            (tenant, pid),
        )

    def prompt_get(self, tenant: str, pid: str, version: int) -> dict | None:
        return self._one(
            "SELECT tenant_id, id, version, template, variables, status, created_by, risk FROM prompts "
            "WHERE tenant_id = %s AND id = %s AND version = %s",
            (tenant, pid, version),
        )

    def prompt_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT DISTINCT ON (id) id, version, status FROM prompts WHERE tenant_id = %s ORDER BY id, version DESC",
            (tenant,),
        )

    def prompt_set_status(
        self, tenant: str, pid: str, version: int, status: str
    ) -> None:
        self._write(
            "UPDATE prompts SET status = %s WHERE tenant_id = %s AND id = %s AND version = %s",
            (status, tenant, pid, version),
        )

    # intents
    def intent_save(
        self,
        tenant: str,
        iid: str,
        workflow: str,
        examples: list,
        keywords: list,
        min_conf: float,
    ) -> None:
        self._write(
            "INSERT INTO intents (tenant_id, id, workflow_id, examples, keywords, min_confidence) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, id, version) DO UPDATE SET workflow_id = EXCLUDED.workflow_id, "
            "examples = EXCLUDED.examples, keywords = EXCLUDED.keywords, min_confidence = EXCLUDED.min_confidence",
            (tenant, iid, workflow, _j(examples), _j(keywords), min_conf),
        )

    def intent_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT id, workflow_id, examples, keywords, min_confidence FROM intents WHERE tenant_id = %s",
            (tenant,),
        )

    # agents (immutable versions)
    def agent_save(
        self,
        tenant: str,
        aid: str,
        version: str,
        display: str,
        pattern: str,
        manifest: dict,
    ) -> None:
        self._write(
            "INSERT INTO agents (tenant_id, id, version, display_name, pattern, manifest) VALUES (%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, id, version) DO UPDATE SET display_name = EXCLUDED.display_name, "
            "pattern = EXCLUDED.pattern, manifest = EXCLUDED.manifest",
            (tenant, aid, version, display, pattern, _j(manifest)),
        )

    def agent_latest(self, tenant: str, aid: str) -> dict | None:
        return self._one(
            "SELECT tenant_id, id, version, display_name, pattern, manifest, status FROM agents "
            "WHERE tenant_id = %s AND id = %s ORDER BY created_at DESC LIMIT 1",
            (tenant, aid),
        )

    def agent_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT DISTINCT ON (id) id, version, display_name, pattern, status FROM agents "
            "WHERE tenant_id = %s ORDER BY id, created_at DESC",
            (tenant,),
        )

    # documents + chunks
    def doc_save(
        self,
        tenant: str,
        did: str,
        kb: str,
        title: str,
        acl: list,
        source: str = "",
        classification: str = "internal",
    ) -> None:
        self._write(
            "INSERT INTO documents (tenant_id, id, kb_id, title, acl_labels, source_ref, classification) VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, id) DO UPDATE SET title = EXCLUDED.title, acl_labels = EXCLUDED.acl_labels, classification = EXCLUDED.classification",
            (tenant, did, kb, title, _j(acl), source, classification),
        )

    def chunk_save(
        self,
        tenant: str,
        cid: str,
        kb: str,
        did: str,
        seq: int,
        content: str,
        prov: dict,
    ) -> None:
        self._write(
            "INSERT INTO chunks (tenant_id, id, kb_id, document_id, seq, content, token_count, provenance) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, id) DO UPDATE SET content = EXCLUDED.content, token_count = EXCLUDED.token_count",
            (tenant, cid, kb, did, seq, content, len(content.split()), _j(prov)),
        )

    CLASS_RANK = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}

    def chunk_search_fts(
        self,
        tenant: str,
        kb: str,
        query: str,
        limit: int,
        max_class: str = "restricted",
    ) -> list[dict]:
        rank = self.CLASS_RANK.get(max_class, 3)
        hits = self._all(
            "SELECT c.id, c.document_id, c.seq, c.content, ts_rank(c.content_tsv, plainto_tsquery('english', %s)) AS rank "
            "FROM chunks c JOIN documents d ON d.tenant_id = c.tenant_id AND d.id = c.document_id "
            "WHERE c.tenant_id = %s AND c.kb_id = %s "
            "AND CASE d.classification WHEN 'public' THEN 0 WHEN 'internal' THEN 1 WHEN 'confidential' THEN 2 ELSE 3 END <= %s "
            "AND c.content_tsv @@ plainto_tsquery('english', %s) ORDER BY rank DESC LIMIT %s",
            (query, tenant, kb, rank, query, limit),
        )
        if hits:
            return hits
        # Recall fallback (RG-7): strict conjunction starves on multi-term queries;
        # retry with OR semantics so ranking (not matching) decides. Documented heuristic.
        from psycopg import sql

        terms = [t for t in query.split() if len(t) > 2][:8]
        if len(terms) < 2:
            return hits
        ors = sql.SQL(" || ").join(
            sql.SQL("plainto_tsquery('english', {})").format(sql.Literal(t))
            for t in terms
        )
        with connect(self.url) as conn:
            rows = conn.execute(
                sql.SQL(
                    "SELECT c.id, c.document_id, c.seq, c.content, ts_rank(c.content_tsv, ({q})) AS rank "
                    "FROM chunks c JOIN documents d ON d.tenant_id = c.tenant_id AND d.id = c.document_id "
                    "WHERE c.tenant_id = %s AND c.kb_id = %s "
                    "AND CASE d.classification WHEN 'public' THEN 0 WHEN 'internal' THEN 1 WHEN 'confidential' THEN 2 ELSE 3 END <= %s "
                    "AND c.content_tsv @@ ({q}) ORDER BY rank DESC LIMIT %s"
                ).format(q=ors),
                (tenant, kb, rank, limit),
            ).fetchall()
            return list(rows)

    # runs + steps + approvals
    def run_create(
        self, tenant: str, rid: str, agent: str, version: str, rin: dict, idem: str
    ) -> None:
        self._write(
            "INSERT INTO runs (tenant_id, id, agent_id, agent_version, input, idempotency_key) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant, rid, agent, version, _j(rin), idem),
        )

    def run_get(self, tenant: str, rid: str) -> dict | None:
        return self._one(
            "SELECT * FROM runs WHERE tenant_id = %s AND id = %s", (tenant, rid)
        )

    def run_list(self, tenant: str, limit: int = 50) -> list[dict]:
        return self._all(
            "SELECT id, agent_id, agent_version, status, created_at, ended_at FROM runs "
            "WHERE tenant_id = %s ORDER BY created_at DESC LIMIT %s",
            (tenant, limit),
        )

    def run_set(
        self, tenant: str, rid: str, status: str, out: dict, usage: dict
    ) -> None:
        self._write(
            "UPDATE runs SET status = %s, output = %s, usage = %s, ended_at = now() "
            "WHERE tenant_id = %s AND id = %s",
            (status, _j(out), _j(usage), tenant, rid),
        )

    def run_set_status(self, tenant: str, rid: str, status: str) -> None:
        self._write(
            "UPDATE runs SET status = %s WHERE tenant_id = %s AND id = %s",
            (status, tenant, rid),
        )

    def step_add(
        self,
        tenant: str,
        rid: str,
        seq: int,
        kind: str,
        payload: dict,
        latency_ms: int = 0,
    ) -> None:
        self._write(
            "INSERT INTO run_steps (tenant_id, run_id, seq, kind, payload, latency_ms) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant, rid, seq, kind, _j(payload), latency_ms),
        )

    def steps(self, tenant: str, rid: str) -> list[dict]:
        return self._all(
            "SELECT seq, kind, payload, latency_ms, created_at FROM run_steps "
            "WHERE tenant_id = %s AND run_id = %s ORDER BY seq",
            (tenant, rid),
        )

    def approval_create(
        self, tenant: str, aid: str, rid: str, action: str, ctx: dict
    ) -> None:
        self._write(
            "INSERT INTO approvals (tenant_id, id, run_id, action, context) VALUES (%s, %s, %s, %s, %s)",
            (tenant, aid, rid, action, _j(ctx)),
        )

    def approval_get(self, tenant: str, aid: str) -> dict | None:
        return self._one(
            "SELECT * FROM approvals WHERE tenant_id = %s AND id = %s", (tenant, aid)
        )

    def approval_list(self, tenant: str, status: str = "pending") -> list[dict]:
        return self._all(
            "SELECT id, run_id, action, status, created_at FROM approvals "
            "WHERE tenant_id = %s AND status = %s ORDER BY created_at",
            (tenant, status),
        )

    def approval_decide(self, tenant: str, aid: str, status: str, by: str) -> None:
        self._write(
            "UPDATE approvals SET status = %s, decided_by = %s, decided_at = now() "
            "WHERE tenant_id = %s AND id = %s",
            (status, by, tenant, aid),
        )

    # quotas + usage + memory
    def quotas_get(self, tenant: str) -> dict:
        row = self._one("SELECT quotas FROM tenants WHERE id = %s", (tenant,))
        return (row or {}).get("quotas") or {"rpm": 60, "runs_per_day": 1000}

    def quotas_set(self, tenant: str, quotas: dict) -> None:
        self._write(
            "INSERT INTO tenants (id, name, quotas) VALUES (%s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET quotas = EXCLUDED.quotas",
            (tenant, tenant, _j(quotas)),
        )

    def usage_add(
        self,
        tenant: str,
        period: str,
        workflow: str,
        runs: int,
        tin: int,
        tout: int,
        cost: float,
    ) -> None:
        self._write(
            "INSERT INTO usage_records (tenant_id, period, workflow_id, runs, tokens_in, tokens_out, cost_usd) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, period, workflow_id) DO UPDATE SET runs = usage_records.runs + EXCLUDED.runs, "
            "tokens_in = usage_records.tokens_in + EXCLUDED.tokens_in, "
            "tokens_out = usage_records.tokens_out + EXCLUDED.tokens_out, "
            "cost_usd = usage_records.cost_usd + EXCLUDED.cost_usd",
            (tenant, period, workflow, runs, tin, tout, cost),
        )

    def usage_get(self, tenant: str, period: str) -> list[dict]:
        return self._all(
            "SELECT period, workflow_id, runs, tokens_in, tokens_out, cost_usd FROM usage_records "
            "WHERE tenant_id = %s AND period = %s ORDER BY workflow_id",
            (tenant, period),
        )

    def memory_add(
        self, tenant: str, agent: str, session: str, role: str, content: str
    ) -> None:
        row = self._one(
            "SELECT COALESCE(MAX(turn), -1) AS m FROM memories WHERE tenant_id = %s AND agent_id = %s AND session_id = %s",
            (tenant, agent, session),
        )
        turn = (row or {}).get("m", -1) + 1
        self._write(
            "INSERT INTO memories (tenant_id, agent_id, session_id, turn, role, content) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant, agent, session, turn, role, content),
        )
        self._write(
            "DELETE FROM memories WHERE tenant_id = %s AND agent_id = %s AND session_id = %s AND turn < %s",
            (tenant, agent, session, turn - 19),
        )

    def memory_list(self, tenant: str, agent: str, session: str) -> list[dict]:
        return self._all(
            "SELECT turn, role, content FROM memories WHERE tenant_id = %s AND agent_id = %s AND session_id = %s ORDER BY turn",
            (tenant, agent, session),
        )

    def memory_clear(self, tenant: str, agent: str, session: str) -> int:
        with connect(self.url) as conn:
            cur = conn.execute(
                "DELETE FROM memories WHERE tenant_id = %s AND agent_id = %s AND session_id = %s",
                (tenant, agent, session),
            )
            conn.commit()
            return cur.rowcount

    # raptor-style extractive summaries
    def summary_save(
        self,
        tenant: str,
        kb: str,
        level: int,
        sid: str,
        children: list,
        summary: str,
        centroid: dict,
    ) -> None:
        self._write(
            "INSERT INTO summary_nodes (tenant_id, kb_id, level, id, child_ids, summary, centroid) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, id) DO UPDATE SET summary = EXCLUDED.summary, centroid = EXCLUDED.centroid",
            (tenant, kb, level, sid, _j(children), summary, _j(centroid)),
        )

    def summary_list(self, tenant: str, kb: str, level: int) -> list[dict]:
        return self._all(
            "SELECT id, child_ids, summary, centroid FROM summary_nodes "
            "WHERE tenant_id = %s AND kb_id = %s AND level = %s ORDER BY id",
            (tenant, kb, level),
        )

    # dense vectors (pgvector)
    def chunk_set_embedding(self, tenant: str, cid: str, vector: list[float]) -> None:
        from pgvector.psycopg import register_vector

        with connect(self.url) as conn:
            register_vector(conn)
            conn.execute(
                "UPDATE chunks SET embedding = %s WHERE tenant_id = %s AND id = %s",
                (vector, tenant, cid),
            )
            conn.commit()

    def chunk_search_dense(
        self,
        tenant: str,
        kb: str,
        vector: list[float],
        limit: int,
        max_class: str = "restricted",
    ) -> list[dict]:
        from pgvector.psycopg import register_vector

        rank = self.CLASS_RANK.get(max_class, 3)
        with connect(self.url) as conn:
            register_vector(conn)
            rows = conn.execute(
                "SELECT c.id, c.document_id, c.seq, c.content, (c.embedding <=> %s::vector) AS distance "
                "FROM chunks c JOIN documents d ON d.tenant_id = c.tenant_id AND d.id = c.document_id "
                "WHERE c.tenant_id = %s AND c.kb_id = %s AND c.embedding IS NOT NULL "
                "AND CASE d.classification WHEN 'public' THEN 0 WHEN 'internal' THEN 1 WHEN 'confidential' THEN 2 ELSE 3 END <= %s "
                "ORDER BY c.embedding <=> %s::vector LIMIT %s",
                (vector, tenant, kb, rank, vector, limit),
            ).fetchall()
            return list(rows)

    def chunks_missing_embeddings(
        self, tenant: str, kb: str, limit: int = 64
    ) -> list[dict]:
        return self._all(
            "SELECT id, content FROM chunks WHERE tenant_id = %s AND kb_id = %s AND embedding IS NULL ORDER BY document_id, seq LIMIT %s",
            (tenant, kb, limit),
        )

    # experiments (ET-1: parameters + metrics + config refs, reproducible by id)
    def experiment_record(
        self,
        tenant: str,
        eid: str,
        subject_type: str,
        subject_ref: str,
        params: dict,
        metrics: dict,
        by: str,
    ) -> None:
        self._write(
            "INSERT INTO experiments (tenant_id, id, subject_type, subject_ref, params, metrics, created_by) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (tenant, eid, subject_type, subject_ref, _j(params), _j(metrics), by),
        )

    def experiment_list(self, tenant: str, subject_type: str = "") -> list[dict]:
        if subject_type:
            return self._all(
                "SELECT id, subject_type, subject_ref, params, metrics, created_by, created_at FROM experiments "
                "WHERE tenant_id = %s AND subject_type = %s ORDER BY created_at",
                (tenant, subject_type),
            )
        return self._all(
            "SELECT id, subject_type, subject_ref, params, metrics, created_by, created_at FROM experiments "
            "WHERE tenant_id = %s ORDER BY created_at",
            (tenant,),
        )

    # erasure + retention (DL-9, PV-4)
    def kb_delete_doc(self, tenant: str, kb: str, did: str) -> dict:
        with connect(self.url) as conn:
            chunks = conn.execute(
                "DELETE FROM chunks WHERE tenant_id = %s AND kb_id = %s AND document_id = %s RETURNING id",
                (tenant, kb, did),
            ).fetchall()
            docs = conn.execute(
                "DELETE FROM documents WHERE tenant_id = %s AND kb_id = %s AND id = %s RETURNING id",
                (tenant, kb, did),
            ).fetchall()
            summaries = conn.execute(
                "DELETE FROM summary_nodes WHERE tenant_id = %s AND kb_id = %s AND child_ids::jsonb ? %s RETURNING id",
                (tenant, kb, did),
            ).fetchall()
            conn.commit()
            return {
                "chunks": len(chunks),
                "documents": len(docs),
                "summaries": len(summaries),
            }

    def tenant_erase(self, tenant: str) -> dict:
        counts = {}
        with connect(self.url) as conn:
            for table, col in (
                ("run_steps", "tenant_id"),
                ("approvals", "tenant_id"),
                ("runs", "tenant_id"),
                ("chunks", "tenant_id"),
                ("documents", "tenant_id"),
                ("agents", "tenant_id"),
                ("intents", "tenant_id"),
                ("prompts", "tenant_id"),
                ("usage_records", "tenant_id"),
                ("memories", "tenant_id"),
                ("experiments", "tenant_id"),
                ("summary_nodes", "tenant_id"),
                ("consents", "tenant_id"),
                ("webhooks", "tenant_id"),
                ("model_registry", "tenant_id"),
                ("corrections", "tenant_id"),
            ):
                cur = conn.execute(f"DELETE FROM {table} WHERE {col} = %s", (tenant,))
                counts[table] = cur.rowcount
            conn.execute("DELETE FROM tenants WHERE id = %s", (tenant,))
            conn.commit()
            return counts

    def tenant_export(self, tenant: str) -> dict:
        bundle: dict = {"tenant": self.tenant_get(tenant) or {"id": tenant}}
        for table in (
            "agents",
            "intents",
            "prompts",
            "documents",
            "runs",
            "usage_records",
            "consents",
            "model_registry",
        ):
            with connect(self.url) as conn:
                rows = conn.execute(
                    f"SELECT * FROM {table} WHERE tenant_id = %s LIMIT 1000", (tenant,)
                ).fetchall()
                bundle[table] = [dict(r) for r in rows]
        return bundle

    # consents / webhooks / registry / corrections / templates
    def consent_set(
        self, tenant: str, subject: str, purpose: str, granted: bool, policy: str = "v1"
    ) -> None:
        self._write(
            "INSERT INTO consents (tenant_id, subject, purpose, policy_version, granted) VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, subject, purpose) DO UPDATE SET granted = EXCLUDED.granted, policy_version = EXCLUDED.policy_version",
            (tenant, subject, purpose, policy, granted),
        )

    def consent_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT subject, purpose, policy_version, granted, recorded_at FROM consents WHERE tenant_id = %s",
            (tenant,),
        )

    def webhook_add(
        self, tenant: str, wid: str, url: str, events: list, secret: str
    ) -> None:
        self._write(
            "INSERT INTO webhooks (tenant_id, id, url, events, secret) VALUES (%s, %s, %s, %s, %s)",
            (tenant, wid, url, _j(events), secret),
        )

    def webhook_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT id, url, events, secret FROM webhooks WHERE tenant_id = %s",
            (tenant,),
        )

    def model_register(
        self,
        tenant: str,
        mid: str,
        version: str,
        backend: str,
        tier: str,
        metadata: dict,
    ) -> None:
        self._write(
            "INSERT INTO model_registry (tenant_id, id, version, backend, risk_tier, metadata) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant, mid, version, backend, tier, _j(metadata)),
        )

    def model_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT id, version, backend, risk_tier, status, metadata FROM model_registry WHERE tenant_id = %s ORDER BY id, version",
            (tenant,),
        )

    def model_set_status(
        self, tenant: str, mid: str, version: str, status: str
    ) -> None:
        self._write(
            "UPDATE model_registry SET status = %s WHERE tenant_id = %s AND id = %s AND version = %s",
            (status, tenant, mid, version),
        )

    def correction_add(
        self, tenant: str, cid: str, text: str, predicted: str, correct: str, by: str
    ) -> None:
        self._write(
            "INSERT INTO corrections (tenant_id, id, text, predicted, correct, created_by) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant, cid, text, predicted, correct, by),
        )

    def correction_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT id, text, predicted, correct FROM corrections WHERE tenant_id = %s",
            (tenant,),
        )

    def template_list(self) -> list[dict]:
        return self._all(
            "SELECT id, name, description, manifest FROM workflow_templates ORDER BY id"
        )

    def _write_and_count(self, sql: str, params: tuple = ()) -> int:
        with connect(self.url) as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.rowcount

    # feature flags (MT-10) + retrieval configs (RG-13)
    def flag_set(self, tenant: str, key: str, value: dict) -> None:
        self._write(
            "INSERT INTO feature_flags (tenant_id, key, value) VALUES (%s, %s, %s) "
            "ON CONFLICT (tenant_id, key) DO UPDATE SET value = EXCLUDED.value, version = feature_flags.version + 1",
            (tenant, key, _j(value)),
        )

    def flag_list(self, tenant: str) -> list[dict]:
        return self._all(
            "SELECT key, value, version FROM feature_flags WHERE tenant_id = %s ORDER BY key",
            (tenant,),
        )

    def rconfig_save(
        self, tenant: str, cid: str, strategy: str, top_k: int, min_faith: float
    ) -> int:
        row = self._one(
            "SELECT COALESCE(MAX(version), 0) AS v FROM retrieval_configs WHERE tenant_id = %s AND id = %s",
            (tenant, cid),
        )
        version = ((row or {}).get("v") or 0) + 1
        self._write(
            "INSERT INTO retrieval_configs (tenant_id, id, version, strategy, top_k, min_faithfulness) VALUES (%s, %s, %s, %s, %s, %s)",
            (tenant, cid, version, strategy, top_k, min_faith),
        )
        return version

    def rconfig_latest(self, tenant: str, cid: str) -> dict | None:
        return self._one(
            "SELECT id, version, strategy, top_k, min_faithfulness FROM retrieval_configs "
            "WHERE tenant_id = %s AND id = %s ORDER BY version DESC LIMIT 1",
            (tenant, cid),
        )
