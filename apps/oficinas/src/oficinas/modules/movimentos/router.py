import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.database import make_db
from oficinas.core.security import requer_autenticado

router = APIRouter(prefix="/movimentos", tags=["movimentos"])


class MovimentoResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    numero: str
    cliente_nome: str | None
    placa: str | None
    valor: Decimal
    status: str
    criado_em: datetime
    fechada_em: datetime | None


@router.get("", response_model=list[MovimentoResponse])
async def listar_movimentos(
    tipo: str | None = Query(None, description="OS | VENDA"),
    status: str | None = Query(None),
    q: str | None = Query(None),
    data_inicial: date | None = Query(None),
    data_final: date | None = Query(None),
    usuario=Depends(requer_autenticado),
    db: AsyncSession = Depends(make_db(requer_autenticado)),
) -> list[MovimentoResponse]:
    params: dict = {"tenant_id": usuario.tenant_id}
    parts: list[str] = []

    if tipo is None or tipo == "OS":
        os_where = "o.tenant_id = :tenant_id"
        if status:
            os_where += " AND o.status = :status_os"
            params["status_os"] = status
        parts.append(f"""
            SELECT o.id, 'OS'::text AS tipo, o.numero_os AS numero,
                   c.nome AS cliente_nome, v.placa,
                   o.total_final AS valor, o.status,
                   o.aberta_em AS criado_em, o.fechada_em
            FROM ordem_servico o
            LEFT JOIN cliente c ON c.id = o.cliente_id
            LEFT JOIN global.veiculo v ON v.id = o.veiculo_id
            WHERE {os_where}
        """)

    if tipo is None or tipo == "VENDA":
        venda_where = "vd.tenant_id = :tenant_id AND vd.origem = 'BALCAO'"
        if status:
            venda_where += " AND vd.status = :status_venda"
            params["status_venda"] = status
        parts.append(f"""
            SELECT vd.id, 'VENDA'::text AS tipo, vd.numero_venda AS numero,
                   c.nome AS cliente_nome, NULL::text AS placa,
                   vd.total AS valor, vd.status,
                   vd.criado_em, NULL::timestamptz AS fechada_em
            FROM venda vd
            LEFT JOIN cliente c ON c.id = vd.cliente_id
            WHERE {venda_where}
        """)

    if not parts:
        return []

    outer_conditions: list[str] = []
    if q:
        outer_conditions.append(
            "(LOWER(m.numero) LIKE :q OR LOWER(m.cliente_nome) LIKE :q)"
        )
        params["q"] = f"%{q.lower()}%"
    if data_inicial:
        outer_conditions.append("m.criado_em >= :data_inicial")
        params["data_inicial"] = data_inicial
    if data_final:
        outer_conditions.append("m.criado_em < :data_final + INTERVAL '1 day'")
        params["data_final"] = data_final

    where_clause = ("WHERE " + " AND ".join(outer_conditions)) if outer_conditions else ""
    union_sql = " UNION ALL ".join(parts)

    sql = text(f"""
        SELECT m.id, m.tipo, m.numero, m.cliente_nome, m.placa,
               m.valor, m.status, m.criado_em, m.fechada_em
        FROM ({union_sql}) m
        {where_clause}
        ORDER BY m.criado_em DESC
    """)

    rows = (await db.execute(sql, params)).mappings().all()
    return [MovimentoResponse(**dict(row)) for row in rows]
