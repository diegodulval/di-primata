import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from oficinas.core.database import Base


class OrdemServico(Base):
    __tablename__ = "ordem_servico"

    id:                     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    cliente_id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cliente.id"))
    veiculo_id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    mecanico_id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"))
    numero_os:              Mapped[str] = mapped_column(Text, nullable=False)
    km_entrada:             Mapped[int | None] = mapped_column(Integer, nullable=True)
    descricao_problema:     Mapped[str] = mapped_column(Text, nullable=False)
    status:                 Mapped[str] = mapped_column(String(20), nullable=False, default="ABERTA")
    compartilhar_historico: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aberta_em:              Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    fechada_em:             Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_pecas:            Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    total_servicos:         Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    desconto:               Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    total_final:            Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))


class ItemOS(Base):
    __tablename__ = "item_os"

    id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    os_id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ordem_servico.id"))
    produto_id:     Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("produto.id"), nullable=True)
    tipo:           Mapped[str] = mapped_column(String(10), nullable=False)
    descricao:      Mapped[str] = mapped_column(Text, nullable=False)
    quantidade:     Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal:       Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class ApontamentoOS(Base):
    __tablename__ = "apontamento_os"

    id:               Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    os_id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ordem_servico.id"))
    usuario_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"))
    item_os_id:       Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("item_os.id"), nullable=True)
    descricao:        Mapped[str] = mapped_column(Text, nullable=False)
    duracao_minutos:  Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_apontamento: Mapped[date] = mapped_column(Date, nullable=False)
    criado_em:        Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
