CREATE TABLE IF NOT EXISTS finetune_jobs (
    tenant_id TEXT NOT NULL,
    id TEXT NOT NULL,
    base_model TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'lora' CHECK (method IN ('sft', 'lora', 'qlora', 'dpo')),
    dataset_ref TEXT NOT NULL DEFAULT '',
    hyperparams JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
    cost_ack BOOLEAN NOT NULL DEFAULT FALSE,
    approvals JSONB NOT NULL DEFAULT '[]',
    created_by TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);
