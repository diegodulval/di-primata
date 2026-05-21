import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from oficinas.core.enums import StatusOS, TipoItem


class OSCreate(BaseModel):
    cliente_id: uuid.UUID
    veiculo_id: uuid.UUID
    km_entrada: int | None = None
    descricao_problema: str


class ItemOSAdd(BaseModel):
    produto_id: uuid.UUID | None = None
    tipo: TipoItem
    descricao: str
    quantidade: Decimal
    preco_unitario: Decimal


class AtualizarStatusOS(BaseModel):
    novo_status: StatusOS


class FecharOS(BaseModel):
    compartilhar_historico: bool = False
    resumo_publico: str | None = None


class ItemOSResponse(BaseModel):
    id: uuid.UUID
    os_id: uuid.UUID
    produto_id: uuid.UUID | None
    tipo: str
    descricao: str
    quantidade: Decimal
    preco_unitario: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OSResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    cliente_id: uuid.UUID
    veiculo_id: uuid.UUID
    mecanico_id: uuid.UUID
    numero_os: str
    km_entrada: int | None
    descricao_problema: str
    status: str
    compartilhar_historico: bool
    aberta_em: datetime
    fechada_em: datetime | None
    total_pecas: Decimal
    total_servicos: Decimal
    desconto: Decimal
    total_final: Decimal

    model_config = {"from_attributes": True}


class OSListResponse(BaseModel):
    total: int
    items: list[OSResponse]
