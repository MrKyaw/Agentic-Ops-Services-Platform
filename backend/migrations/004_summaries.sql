CREATE TABLE IF NOT EXISTS summary_nodes (
    tenant_id TEXT NOT NULL,
    kb_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    id TEXT NOT NULL,
    child_ids JSONB NOT NULL DEFAULT '[]',
    summary TEXT NOT NULL,
    centroid JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (tenant_id, id)
);
CREATE INDEX IF NOT EXISTS summary_kb_idx ON summary_nodes (tenant_id, kb_id, level);
