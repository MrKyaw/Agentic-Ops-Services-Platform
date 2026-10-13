CREATE TABLE IF NOT EXISTS consents (
    tenant_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    purpose TEXT NOT NULL,
    policy_version TEXT NOT NULL DEFAULT 'v1',
    granted BOOLEAN NOT NULL DEFAULT TRUE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, subject, purpose)
);

CREATE TABLE IF NOT EXISTS webhooks (
    tenant_id TEXT NOT NULL,
    id TEXT NOT NULL,
    url TEXT NOT NULL,
    events JSONB NOT NULL DEFAULT '[]',
    secret TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS model_registry (
    tenant_id TEXT NOT NULL,
    id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0',
    backend TEXT NOT NULL,
    risk_tier TEXT NOT NULL DEFAULT 'low' CHECK (risk_tier IN ('low', 'medium', 'high')),
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (status IN ('candidate', 'evaluated', 'approved', 'deployed', 'deprecated', 'retired')),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id, version)
);

CREATE TABLE IF NOT EXISTS corrections (
    tenant_id TEXT NOT NULL,
    id TEXT NOT NULL,
    text TEXT NOT NULL,
    predicted TEXT NOT NULL,
    correct TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS workflow_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    manifest JSONB NOT NULL DEFAULT '{}'
);
