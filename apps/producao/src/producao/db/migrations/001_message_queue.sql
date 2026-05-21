CREATE TABLE IF NOT EXISTS message_queue (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone         TEXT NOT NULL,
    messages      JSONB NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    process_after TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_mq_status_pa ON message_queue (status, process_after);
CREATE INDEX IF NOT EXISTS idx_mq_phone     ON message_queue (phone);
