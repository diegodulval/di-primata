import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ItemVendaIn(BaseModel):
    produto_id:     uuid.UUID
    quantidade:     Decimal = Field(gt=0)
    preco_unitario: Decimal = Field(ge=0)


class VendaCreate(BaseModel):
    cliente_id: uuid.UUID | None = None
    itens:      list[ItemVendaIn] = Field(min_length=1)


class ItemVendaResponse(BaseModel):
    id:             uuid.UUID
    venda_id:       uuid.UUID
    produto_id:     uuid.UUID
    quantidade:     Decimal
    preco_unitario: Decimal
    subtotal:       Decimal

    model_config = {"from_attributes": True}


class VendaResponse(BaseModel):
    id:           uuid.UUID
    tenant_id:    uuid.UUID
    cliente_id:   uuid.UUID | None
    usuario_id:   uuid.UUID
    numero_venda: str
    origem:       str
    total:        Decimal
    status:       str
    criado_em:    datetime
    itens:        list[ItemVendaResponse] = []

    model_config = {"from_attributes": True}
