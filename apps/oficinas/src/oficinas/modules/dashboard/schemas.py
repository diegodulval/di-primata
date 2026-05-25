import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class OSRecenteItem(BaseModel):
    id: uuid.UUID
    numero_os: str
    placa: str
    descricao_problema: str
    status: str
    mecanico_nome: str


class AniversarianteItem(BaseModel):
    id: uuid.UUID
    nome: str
    celular: str | None
    telefone: str | None
    data_nascimento: date


class DashboardResponse(BaseModel):
    # Operacional
    os_abertas: int
    os_em_execucao: int
    os_aguardando_peca: int
    os_fechadas_hoje: int
    vendas_hoje: int
    estoque_critico: int

    # Financeiro
    faturamento_hoje: Decimal
    faturamento_mes: Decimal
    ticket_medio_os_mes: Decimal
    ticket_medio_venda_mes: Decimal

    # Aniversariantes
    aniversariantes_hoje: int
    aniversariantes_semana: int
    aniversariantes_hoje_lista: list[AniversarianteItem]

    # Lista
    os_recentes: list[OSRecenteItem]
