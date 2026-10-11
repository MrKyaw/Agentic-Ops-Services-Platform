CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prompts (
    id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    template TEXT NOT NULL,
    variables JSONB NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'retired')),
    created_by TEXT NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id, version)
);

CREATE TABLE IF NOT EXISTS intents (
    id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    examples JSONB NOT NULL DEFAULT '[]',
    keywords JSONB NOT NULL DEFAULT '[]',
    min_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.8,
    version INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (tenant_id, id, version)
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '0.1.0',
    display_name TEXT NOT NULL,
    pattern TEXT NOT NULL DEFAULT 'react' CHECK (pattern IN ('react', 'rewoo')),
    manifest JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id, version)
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    kb_id TEXT NOT NULL,
    source_ref TEXT NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1,
    title TEXT NOT NULL DEFAULT '',
    acl_labels JSONB NOT NULL DEFAULT '[]',
    classification TEXT NOT NULL DEFAULT 'internal',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS documents_kb_idx ON documents (tenant_id, kb_id);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    kb_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    token_count INTEGER NOT NULL DEFAULT 0,
    provenance JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING GIN (content_tsv);
CREATE INDEX IF NOT EXISTS chunks_kb_idx ON chunks (tenant_id, kb_id);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    agent_version TEXT NOT NULL DEFAULT '0.1.0',
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'waiting_approval', 'succeeded', 'failed', 'rejected')),
    input JSONB NOT NULL DEFAULT '{}',
    output JSONB NOT NULL DEFAULT '{}',
    usage JSONB NOT NULL DEFAULT '{}',
    idempotency_key TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, id)
);
CREATE UNIQUE INDEX IF NOT EXISTS runs_idem_idx ON runs (tenant_id, idempotency_key) WHERE idempotency_key <> '';

CREATE TABLE IF NOT EXISTS run_steps (
    run_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('intent', 'plan', 'model', 'tool', 'retrieval', 'approval', 'result')),
    payload JSONB NOT NULL DEFAULT '{}',
    latency_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, run_id, seq)
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    action TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    decided_by TEXT NOT NULL DEFAULT '',
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);
