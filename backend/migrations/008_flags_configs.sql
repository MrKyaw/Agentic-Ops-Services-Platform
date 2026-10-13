CREATE TABLE IF NOT EXISTS feature_flags (
    tenant_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value JSONB NOT NULL DEFAULT 'false',
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, key)
);

CREATE TABLE IF NOT EXISTS retrieval_configs (
    tenant_id TEXT NOT NULL,
    id TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    strategy TEXT NOT NULL DEFAULT 'auto',
    top_k INTEGER NOT NULL DEFAULT 5,
    min_faithfulness DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id, version)
);
