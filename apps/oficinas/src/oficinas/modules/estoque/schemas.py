import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from oficinas.core.enums import TipoMovimentacao


class FornecedorCreate(BaseModel):
    razao_social: str
    cnpj:         str | None = None
    contato:      str | None = None


class FornecedorUpdate(BaseModel):
    razao_social: str | None = None
    cnpj:         str | None = None
    contato:      str | None = None


class FornecedorResponse(BaseModel):
    id:           uuid.UUID
    tenant_id:    uuid.UUID
    razao_social: str
    cnpj:         str | None
    contato:      str | None

    model_config = {"from_attributes": True}


class ProdutoCreate(BaseModel):
    codigo:         str
    descricao:      str
    ncm:            str | None = None
    marca:          str | None = None
    localizacao:    str | None = None
    ean:            str | None = None
    preco_custo:    Decimal = Field(default=Decimal("0"), ge=0)
    preco_venda:    Decimal = Field(default=Decimal("0"), ge=0)
    estoque_minimo: Decimal = Field(default=Decimal("0"), ge=0)
    estoque_maximo: Decimal = Field(default=Decimal("0"), ge=0)


class ProdutoUpdate(BaseModel):
    descricao:      str | None = None
    ncm:            str | None = None
    marca:          str | None = None
    localizacao:    str | None = None
    ean:            str | None = None
    preco_custo:    Decimal | None = None
    preco_venda:    Decimal | None = None
    estoque_minimo: Decimal | None = None
    estoque_maximo: Decimal | None = None
    ativo:          bool | None = None


class ProdutoResponse(BaseModel):
    id:             uuid.UUID
    tenant_id:      uuid.UUID
    codigo:         str
    descricao:      str
    ncm:            str | None
    marca:          str | None
    localizacao:    str | None
    ean:            str | None
    preco_custo:    Decimal
    preco_venda:    Decimal
    estoque_atual:  Decimal
    estoque_minimo: Decimal
    estoque_maximo: Decimal
    ativo:          bool

    model_config = {"from_attributes": True}


class MovimentacaoResponse(BaseModel):
    id:               uuid.UUID
    produto_id:       uuid.UUID
    tipo_mov:         TipoMovimentacao
    quantidade:       Decimal
    estoque_anterior: Decimal
    estoque_novo:     Decimal
    referencia_id:    uuid.UUID | None
    tipo_ref:         str | None
    criado_em:        datetime

    model_config = {"from_attributes": True}


class ItemEntradaResponse(BaseModel):
    id:                uuid.UUID
    produto_id:        uuid.UUID | None
    codigo_fornecedor: str | None
    quantidade:        Decimal
    preco_unitario:    Decimal
    icms:              Decimal
    ipi:               Decimal

    model_config = {"from_attributes": True}


class EntradaNfeResponse(BaseModel):
    id:            uuid.UUID
    tenant_id:     uuid.UUID
    fornecedor_id: uuid.UUID | None
    chave_nfe:     str | None
    numero_nf:     str | None
    data_emissao:  date | None
    valor_total:   Decimal | None
    status:        str
    criado_em:     datetime
    itens:         list[ItemEntradaResponse] = []

    model_config = {"from_attributes": True}


# ─── Rascunho NF-e ────────────────────────────────────────────────────────────

class VincularItemPayload(BaseModel):
    acao:       Literal["vincular", "criar_novo"]
    produto_id: uuid.UUID | None = None


class ItemRascunhoResponse(BaseModel):
    id:                uuid.UUID
    rascunho_id:       uuid.UUID
    produto_id:        uuid.UUID | None
    codigo_fornecedor: str
    codigo_ref:        str | None
    ean:               str | None
    descricao_nfe:     str
    ncm:               str | None
    quantidade:        Decimal
    preco_unitario:    Decimal
    icms:              Decimal
    ipi:               Decimal
    status_item:       str

    model_config = {"from_attributes": True}


class RascunhoResponse(BaseModel):
    id:            uuid.UUID
    tenant_id:     uuid.UUID
    fornecedor_id: uuid.UUID | None
    chave_nfe:     str | None
    numero_nf:     str | None
    data_emissao:  date | None
    valor_total:   Decimal | None
    status:        str
    criado_em:     datetime
    itens:         list[ItemRascunhoResponse] = []
    pendentes:     int = 0

    model_config = {"from_attributes": True}
