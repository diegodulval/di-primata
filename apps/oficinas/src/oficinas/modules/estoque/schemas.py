import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from oficinas.core.enums import TipoMovimentacao


class MarcaCreate(BaseModel):
    nome: str


class MarcaUpdate(BaseModel):
    nome:  str | None = None
    ativo: bool | None = None


class MarcaResponse(BaseModel):
    id:        uuid.UUID
    tenant_id: uuid.UUID
    nome:      str
    ativo:     bool

    model_config = {"from_attributes": True}


class MarcasPaginadas(BaseModel):
    items:     list[MarcaResponse]
    total:     int
    page:      int
    page_size: int
    pages:     int


class FornecedorCreate(BaseModel):
    razao_social:       str
    nome_fantasia:      str | None = None
    cnpj:               str | None = None
    inscricao_estadual: str | None = None
    telefone:           str | None = None
    email:              str | None = None
    contato:            str | None = None
    ativo:              bool = True
    tipo_pessoa:        str | None = "Juridica"


class FornecedorUpdate(BaseModel):
    razao_social:       str | None = None
    nome_fantasia:      str | None = None
    cnpj:               str | None = None
    inscricao_estadual: str | None = None
    telefone:           str | None = None
    email:              str | None = None
    contato:            str | None = None
    ativo:              bool | None = None
    tipo_pessoa:        str | None = None


class FornecedorResponse(BaseModel):
    id:                 uuid.UUID
    tenant_id:          uuid.UUID
    razao_social:       str
    nome_fantasia:      str | None
    cnpj:               str | None
    inscricao_estadual: str | None
    telefone:           str | None
    email:              str | None
    contato:            str | None
    ativo:              bool
    tipo_pessoa:        str | None

    model_config = {"from_attributes": True}


class ProdutoFornecedorResponse(BaseModel):
    mapeamento_id:     uuid.UUID
    produto_id:        uuid.UUID
    codigo_interno:    str
    codigo_fornecedor: str
    descricao:         str
    marca_id:          uuid.UUID | None


class ImportacaoResponse(BaseModel):
    criados:     int
    atualizados: int
    ignorados:   int
    erros:       list[str]


ImportacaoFornecedorResponse = ImportacaoResponse


class ProdutoCreate(BaseModel):
    codigo:            str
    descricao:         str
    ncm:               str | None = None
    marca_id:          uuid.UUID | None = None
    localizacao:       str | None = None
    ean:               str | None = None
    ref_fabricante:    str | None = None
    unidade_medida:    str = "UN"
    preco_custo:       Decimal = Field(default=Decimal("0"), ge=0)
    preco_venda:       Decimal = Field(default=Decimal("0"), ge=0)
    estoque_minimo:    Decimal = Field(default=Decimal("0"), ge=0)
    estoque_maximo:    Decimal = Field(default=Decimal("0"), ge=0)
    peso_liquido:      Decimal = Field(default=Decimal("0"), ge=0)
    peso_bruto:        Decimal = Field(default=Decimal("0"), ge=0)
    origem_mercadoria: str = "0"
    observacoes:       str | None = None


class ProdutoUpdate(BaseModel):
    descricao:         str | None = None
    ncm:               str | None = None
    marca_id:          uuid.UUID | None = None
    localizacao:       str | None = None
    ean:               str | None = None
    ref_fabricante:    str | None = None
    unidade_medida:    str | None = None
    preco_custo:       Decimal | None = None
    preco_venda:       Decimal | None = None
    estoque_minimo:    Decimal | None = None
    estoque_maximo:    Decimal | None = None
    peso_liquido:      Decimal | None = None
    peso_bruto:        Decimal | None = None
    origem_mercadoria: str | None = None
    observacoes:       str | None = None
    ativo:             bool | None = None


class ProdutoResponse(BaseModel):
    id:                uuid.UUID
    tenant_id:         uuid.UUID
    codigo:            str
    descricao:         str
    ncm:               str | None
    marca_id:          uuid.UUID | None
    localizacao:       str | None
    ean:               str | None
    ref_fabricante:    str | None
    unidade_medida:    str
    preco_custo:       Decimal
    preco_venda:       Decimal
    estoque_atual:     Decimal
    estoque_minimo:    Decimal
    estoque_maximo:    Decimal
    peso_liquido:      Decimal
    peso_bruto:        Decimal
    origem_mercadoria: str
    observacoes:       str | None
    ativo:             bool

    model_config = {"from_attributes": True}


class ProdutosPaginados(BaseModel):
    items:     list[ProdutoResponse]
    total:     int
    page:      int
    page_size: int
    pages:     int


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
    data_entrada:      date | None

    model_config = {"from_attributes": True}


class EntradaNfeResponse(BaseModel):
    id:            uuid.UUID
    tenant_id:     uuid.UUID
    fornecedor_id: uuid.UUID | None
    chave_nfe:     str | None
    numero_nf:     str | None
    data_emissao:  date | None
    data_entrada:  date | None
    valor_total:   Decimal | None
    status:        str
    criado_em:     datetime
    itens:         list[ItemEntradaResponse] = []

    model_config = {"from_attributes": True}


class ItemEntradaUpdate(BaseModel):
    id:           uuid.UUID
    data_entrada: date | None = None


class EntradaUpdate(BaseModel):
    data_entrada: date | None = None
    itens:        list[ItemEntradaUpdate] = []


# ─── Rascunho NF-e ────────────────────────────────────────────────────────────

class VincularItemPayload(BaseModel):
    acao:       Literal["vincular", "criar_novo"]
    produto_id: uuid.UUID | None = None
    marca_id:   uuid.UUID | None = None


class ItemRascunhoResponse(BaseModel):
    id:                uuid.UUID
    rascunho_id:       uuid.UUID
    produto_id:        uuid.UUID | None
    codigo_produto:    str | None = None
    marca_id_produto:  uuid.UUID | None = None
    codigo_fornecedor: str
    codigo_ref:        str | None
    ean:               str | None
    descricao_nfe:     str
    ncm:               str | None
    quantidade:        Decimal
    preco_unitario:    Decimal
    icms:              Decimal
    ipi:               Decimal
    cfop:              str | None
    cst:               str | None
    status_item:       str

    model_config = {"from_attributes": True}


class RascunhoResponse(BaseModel):
    id:              uuid.UUID
    tenant_id:       uuid.UUID
    fornecedor_id:   uuid.UUID | None
    fornecedor_nome: str | None = None
    chave_nfe:       str | None
    numero_nf:       str | None
    data_emissao:    date | None
    valor_total:     Decimal | None
    status:          str
    criado_em:       datetime
    itens:           list[ItemRascunhoResponse] = []
    pendentes:       int = 0

    model_config = {"from_attributes": True}
