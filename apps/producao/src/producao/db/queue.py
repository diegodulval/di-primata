import json
import logging
from datetime import UTC, datetime

import asyncpg

from producao.ingestion.models import IncomingMessage, QueueItem

logger = logging.getLogger(__name__)

_STATUS_PENDING = "pending"
_STATUS_PROCESSING = "processing"
_STATUS_DONE = "done"
_STATUS_FAILED = "failed"


async def insert_message_batch(
    pool: asyncpg.Pool,
    phone: str,
    messages: list[IncomingMessage],
) -> QueueItem:
    messages_json = json.dumps([m.model_dump(mode="json") for m in messages])
    process_after = datetime.now(UTC)

    row = await pool.fetchrow(
        """
        INSERT INTO message_queue (phone, messages, status, process_after)
        VALUES ($1, $2::jsonb, $3, $4)
        RETURNING id, phone, messages, status, process_after, created_at, processed_at
        """,
        phone,
        messages_json,
        _STATUS_PENDING,
        process_after,
    )
    logger.debug("Enqueued | id=%s phone=%s msgs=%d", row["id"], phone, len(messages))
    return _row_to_item(row)


async def fetch_pending(pool: asyncpg.Pool, limit: int = 50) -> list[QueueItem]:
    rows = await pool.fetch(
        """
        SELECT id, phone, messages, status, process_after, created_at, processed_at
        FROM message_queue
        WHERE status = $1
        ORDER BY process_after
        LIMIT $2
        """,
        _STATUS_PENDING,
        limit,
    )
    return [_row_to_item(r) for r in rows]


async def mark_processing(pool: asyncpg.Pool, item_id) -> None:
    await pool.execute(
        "UPDATE message_queue SET status = $1 WHERE id = $2",
        _STATUS_PROCESSING,
        item_id,
    )


async def mark_done(pool: asyncpg.Pool, item_id) -> None:
    await pool.execute(
        "UPDATE message_queue SET status = $1, processed_at = $2 WHERE id = $3",
        _STATUS_DONE,
        datetime.now(UTC),
        item_id,
    )


async def mark_failed(pool: asyncpg.Pool, item_id) -> None:
    await pool.execute(
        "UPDATE message_queue SET status = $1, processed_at = $2 WHERE id = $3",
        _STATUS_FAILED,
        datetime.now(UTC),
        item_id,
    )


def _row_to_item(row) -> QueueItem:
    raw_messages = row["messages"]
    if isinstance(raw_messages, str):
        raw_messages = json.loads(raw_messages)
    messages = [IncomingMessage(**m) for m in raw_messages]
    return QueueItem(
        id=row["id"],
        phone=row["phone"],
        messages=messages,
        status=row["status"],
        process_after=row["process_after"],
        created_at=row["created_at"],
        processed_at=row["processed_at"],
    )
