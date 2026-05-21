import asyncio
import logging

from producao.ingestion.models import IncomingMessage

logger = logging.getLogger(__name__)


class DebounceBuffer:
    """
    Acumula mensagens do mesmo phone em uma janela de tempo e faz flush
    atômico para a fila PostgreSQL quando a janela expira.
    """

    def __init__(self, pool, window_seconds: float = 2.0) -> None:
        self._pool = pool
        self._window = window_seconds
        self._buffers: dict[str, list[IncomingMessage]] = {}
        self._handles: dict[str, asyncio.TimerHandle] = {}

    async def push(self, msg: IncomingMessage) -> None:
        phone = msg.phone
        if phone in self._handles:
            self._handles[phone].cancel()
        self._buffers.setdefault(phone, []).append(msg)
        loop = asyncio.get_event_loop()
        self._handles[phone] = loop.call_later(
            self._window,
            lambda p=phone: asyncio.ensure_future(self._flush(p)),
        )
        logger.debug("Debounce: buffered msg | phone=%s buffer_size=%d", phone, len(self._buffers[phone]))

    async def _flush(self, phone: str) -> None:
        messages = self._buffers.pop(phone, [])
        self._handles.pop(phone, None)
        if not messages:
            return

        if self._pool is None:
            logger.warning("Debounce flush: db_pool não configurado, %d mensagens descartadas | phone=%s", len(messages), phone)
            return

        from producao.db import queue as db_queue
        await db_queue.insert_message_batch(self._pool, phone, messages)
        logger.info("Debounce flush: %d msg(s) → queue | phone=%s", len(messages), phone)
