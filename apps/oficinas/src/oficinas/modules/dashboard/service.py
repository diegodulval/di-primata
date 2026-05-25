from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.modules.dashboard.schemas import (
    AniversarianteItem,
    DashboardResponse,
    OSRecenteItem,
)

_AGG_SQL = text("""
    WITH os_stats AS (
        SELECT
            COUNT(*) FILTER (WHERE status = 'ABERTA') AS os_abertas,
            COUNT(*) FILTER (WHERE status = 'EM_EXECUCAO') AS os_em_execucao,
            COUNT(*) FILTER (WHERE status = 'AGUARDANDO_PECA') AS os_aguardando_peca,
            COUNT(*) FILTER (
                WHERE status = 'FECHADA' AND fechada_em::date = CURRENT_DATE
            ) AS os_fechadas_hoje,
            COALESCE(SUM(total_final) FILTER (
                WHERE status = 'FECHADA' AND fechada_em::date = CURRENT_DATE
            ), 0) AS fat_os_hoje,
            COALESCE(SUM(total_final) FILTER (
                WHERE status = 'FECHADA' AND fechada_em >= date_trunc('month', now())
            ), 0) AS fat_os_mes,
            COALESCE(AVG(total_final) FILTER (
                WHERE status = 'FECHADA' AND fechada_em >= date_trunc('month', now())
            ), 0) AS ticket_os_mes
        FROM ordem_servico
    ),
    venda_stats AS (
        SELECT
            COUNT(*) FILTER (
                WHERE status = 'CONCLUIDA' AND criado_em::date = CURRENT_DATE
            ) AS vendas_hoje,
            COALESCE(SUM(total) FILTER (
                WHERE status = 'CONCLUIDA' AND criado_em::date = CURRENT_DATE
            ), 0) AS fat_venda_hoje,
            COALESCE(SUM(total) FILTER (
                WHERE status = 'CONCLUIDA' AND criado_em >= date_trunc('month', now())
            ), 0) AS fat_venda_mes,
            COALESCE(AVG(total) FILTER (
                WHERE status = 'CONCLUIDA' AND criado_em >= date_trunc('month', now())
            ), 0) AS ticket_venda_mes
        FROM venda
    ),
    estoque_stats AS (
        SELECT COUNT(*) AS estoque_critico
        FROM produto
        WHERE ativo = true AND estoque_atual <= estoque_minimo
    )
    SELECT
        os_abertas, os_em_execucao, os_aguardando_peca, os_fechadas_hoje,
        vendas_hoje,
        estoque_critico,
        fat_os_hoje + fat_venda_hoje AS faturamento_hoje,
        fat_os_mes  + fat_venda_mes  AS faturamento_mes,
        ticket_os_mes,
        ticket_venda_mes
    FROM os_stats, venda_stats, estoque_stats
""")

_ANIVERSARIANTES_SQL = text("""
    SELECT
        COUNT(*) FILTER (
            WHERE to_char(data_nascimento, 'MM-DD') = to_char(CURRENT_DATE, 'MM-DD')
        ) AS aniversariantes_hoje,
        COUNT(*) FILTER (
            WHERE to_char(data_nascimento, 'MM-DD') = ANY(
                ARRAY(
                    SELECT to_char(CURRENT_DATE + s.i, 'MM-DD')
                    FROM generate_series(0, 6) AS s(i)
                )
            )
        ) AS aniversariantes_semana
    FROM cliente
    WHERE ativo = true AND data_nascimento IS NOT NULL
""")

_ANIVERSARIANTES_HOJE_SQL = text("""
    SELECT id, nome, celular, telefone, data_nascimento
    FROM cliente
    WHERE ativo = true
      AND data_nascimento IS NOT NULL
      AND to_char(data_nascimento, 'MM-DD') = to_char(CURRENT_DATE, 'MM-DD')
    ORDER BY nome
""")

_RECENTES_SQL = text("""
    SELECT
        os.id,
        os.numero_os,
        v.placa,
        os.descricao_problema,
        os.status,
        u.nome AS mecanico_nome
    FROM ordem_servico os
    JOIN global.veiculo v ON v.id = os.veiculo_id
    JOIN usuario        u ON u.id = os.mecanico_id
    WHERE os.status IN ('ABERTA', 'EM_EXECUCAO', 'AGUARDANDO_PECA')
    ORDER BY os.aberta_em DESC
    LIMIT 5
""")


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self) -> DashboardResponse:
        row = (await self.db.execute(_AGG_SQL)).one()
        aniv_row = (await self.db.execute(_ANIVERSARIANTES_SQL)).one()
        aniv_lista = (await self.db.execute(_ANIVERSARIANTES_HOJE_SQL)).all()
        recentes_rows = (await self.db.execute(_RECENTES_SQL)).all()

        return DashboardResponse(
            os_abertas=row.os_abertas,
            os_em_execucao=row.os_em_execucao,
            os_aguardando_peca=row.os_aguardando_peca,
            os_fechadas_hoje=row.os_fechadas_hoje,
            vendas_hoje=row.vendas_hoje,
            estoque_critico=row.estoque_critico,
            faturamento_hoje=row.faturamento_hoje,
            faturamento_mes=row.faturamento_mes,
            ticket_medio_os_mes=row.ticket_os_mes,
            ticket_medio_venda_mes=row.ticket_venda_mes,
            aniversariantes_hoje=aniv_row.aniversariantes_hoje,
            aniversariantes_semana=aniv_row.aniversariantes_semana,
            aniversariantes_hoje_lista=[
                AniversarianteItem(
                    id=r.id,
                    nome=r.nome,
                    celular=r.celular,
                    telefone=r.telefone,
                    data_nascimento=r.data_nascimento,
                )
                for r in aniv_lista
            ],
            os_recentes=[
                OSRecenteItem(
                    id=r.id,
                    numero_os=r.numero_os,
                    placa=r.placa,
                    descricao_problema=r.descricao_problema,
                    status=r.status,
                    mecanico_nome=r.mecanico_nome,
                )
                for r in recentes_rows
            ],
        )
