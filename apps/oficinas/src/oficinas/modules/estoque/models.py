import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from oficinas.core.database import Base


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id:                  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:           Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    razao_social:        Mapped[str] = mapped_column(Text, nullable=False)
    nome_fantasia:       Mapped[str | None] = mapped_column(Text, nullable=True)
    cnpj:                Mapped[str | None] = mapped_column(String(14), nullable=True)
    inscricao_estadual:  Mapped[str | None] = mapped_column(String(20), nullable=True)
    telefone:            Mapped[str | None] = mapped_column(String(20), nullable=True)
    email:               Mapped[str | None] = mapped_column(Text, nullable=True)
    contato:             Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo:               Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tipo_pessoa:         Mapped[str | None] = mapped_column(String(10), nullable=True, default="Juridica")


class Produto(Base):
    __tablename__ = "produto"

    id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:      Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    codigo:         Mapped[str] = mapped_column(Text, nullable=False)
    descricao:      Mapped[str] = mapped_column(Text, nullable=False)
    ncm:            Mapped[str | None] = mapped_column(String(8), nullable=True)
    marca:          Mapped[str | None] = mapped_column(Text, nullable=True)
    localizacao:    Mapped[str | None] = mapped_column(Text, nullable=True)
    preco_custo:    Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    preco_venda:    Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    estoque_atual:  Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0"))
    estoque_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0"))
    estoque_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0"))
    ativo:          Mapped[bool] = mapped_column(Boolean, default=True)
    ean:            Mapped[str | None] = mapped_column(String(14), nullable=True)


class EntradaNfe(Base):
    __tablename__ = "entrada_nfe"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    fornecedor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("fornecedor.id"), nullable=True)
    chave_nfe:     Mapped[str | None] = mapped_column(String(44), unique=True, nullable=True)
    numero_nf:     Mapped[str | None] = mapped_column(Text, nullable=True)
    data_emissao:  Mapped[date | None] = mapped_column(Date, nullable=True)
    data_entrada:  Mapped[date | None] = mapped_column(Date, nullable=True)
    valor_total:   Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    xml_path:      Mapped[str | None] = mapped_column(Text, nullable=True)
    status:        Mapped[str] = mapped_column(String(20), default="PROCESSADA")
    criado_em:     Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ItemEntrada(Base):
    __tablename__ = "item_entrada"

    id:                Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrada_id:        Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entrada_nfe.id"))
    produto_id:        Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("produto.id"), nullable=True)
    codigo_fornecedor: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantidade:        Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario:    Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    icms:              Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    ipi:               Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    data_entrada:      Mapped[date | None] = mapped_column(Date, nullable=True)


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacao_estoque"

    id:               Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:        Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    produto_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("produto.id"))
    referencia_id:    Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    tipo_ref:         Mapped[str | None] = mapped_column(String(10), nullable=True)
    tipo_mov:         Mapped[str] = mapped_column(String(10), nullable=False)
    quantidade:       Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    estoque_anterior: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    estoque_novo:     Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    criado_em:        Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class MapeamentoFornecedorProduto(Base):
    __tablename__ = "mapeamento_fornecedor_produto"
    __table_args__ = (UniqueConstraint("tenant_id", "fornecedor_id", "codigo_fornecedor"),)

    id:                Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    fornecedor_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fornecedor.id"))
    codigo_fornecedor: Mapped[str] = mapped_column(Text, nullable=False)
    produto_id:        Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("produto.id"))


class RascunhoEntrada(Base):
    __tablename__ = "rascunho_entrada"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    fornecedor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("fornecedor.id"), nullable=True)
    chave_nfe:     Mapped[str | None] = mapped_column(String(44), nullable=True)
    numero_nf:     Mapped[str | None] = mapped_column(Text, nullable=True)
    data_emissao:  Mapped[date | None] = mapped_column(Date, nullable=True)
    valor_total:   Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status:        Mapped[str] = mapped_column(String(20), nullable=False, default="PENDENTE")
    criado_em:     Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ItemRascunhoEntrada(Base):
    __tablename__ = "item_rascunho_entrada"

    id:                Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rascunho_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rascunho_entrada.id"))
    produto_id:        Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("produto.id"), nullable=True)
    codigo_fornecedor: Mapped[str] = mapped_column(Text, nullable=False)
    codigo_ref:        Mapped[str | None] = mapped_column(Text, nullable=True)
    ean:               Mapped[str | None] = mapped_column(String(14), nullable=True)
    descricao_nfe:     Mapped[str] = mapped_column(Text, nullable=False)
    ncm:               Mapped[str | None] = mapped_column(String(8), nullable=True)
    quantidade:        Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario:    Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    icms:              Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    ipi:               Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    cfop:              Mapped[str | None] = mapped_column(String(4), nullable=True)
    cst:               Mapped[str | None] = mapped_column(String(3), nullable=True)
    status_item:       Mapped[str] = mapped_column(String(20), nullable=False, default="PENDENTE")
