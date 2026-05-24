import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

TIMEOUT = timedelta(hours=2)


async def carregar(db: AsyncSession, numero: str) -> list[dict]:
    row = (
        await db.execute(
            text("SELECT mensagens, atualizado_em FROM agente_sessao WHERE numero_whatsapp = :n"),
            {"n": numero},
        )
    ).fetchone()
    if not row:
        return []
    atualizado = row.atualizado_em
    if atualizado.tzinfo is None:
        atualizado = atualizado.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - atualizado > TIMEOUT:
        return []
    # asyncpg desserializa JSONB como Python list/dict automaticamente
    msgs = row.mensagens
    if isinstance(msgs, str):
        msgs = json.loads(msgs)
    return msgs  # type: ignore[return-value]


async def salvar(
    db: AsyncSession,
    numero: str,
    tenant_id: str,
    usuario_id: str,
    msgs: list,
) -> None:
    await db.execute(
        text("""
            INSERT INTO agente_sessao
              (numero_whatsapp, tenant_id, usuario_id, mensagens, atualizado_em)
            VALUES (:n, CAST(:tid AS uuid), CAST(:uid AS uuid), CAST(:msgs AS jsonb), now())
            ON CONFLICT (numero_whatsapp)
            DO UPDATE SET mensagens = CAST(:msgs AS jsonb), atualizado_em = now()
        """),
        {"n": numero, "tid": tenant_id, "uid": usuario_id, "msgs": json.dumps(msgs)},
    )
    await db.commit()
