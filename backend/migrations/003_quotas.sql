ALTER TABLE tenants ADD COLUMN IF NOT EXISTS quotas JSONB NOT NULL DEFAULT '{"rpm": 60, "runs_per_day": 1000}';

CREATE TABLE IF NOT EXISTS usage_records (
    tenant_id TEXT NOT NULL,
    period DATE NOT NULL,
    workflow_id TEXT NOT NULL DEFAULT '',
    runs INTEGER NOT NULL DEFAULT 0,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    PRIMARY KEY (tenant_id, period, workflow_id)
);

CREATE TABLE IF NOT EXISTS memories (
    tenant_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    turn INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, agent_id, session_id, turn)
);
CREATE INDEX IF NOT EXISTS memories_session_idx ON memories (tenant_id, agent_id, session_id, turn);
