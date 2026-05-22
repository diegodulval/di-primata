import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from oficinas.core.database import Base


class Venda(Base):
    __tablename__ = "venda"

    id:           Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    cliente_id:   Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cliente.id"), nullable=True)
    usuario_id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"))
    numero_venda: Mapped[str] = mapped_column(Text, nullable=False)
    origem:       Mapped[str] = mapped_column(String(10), nullable=False)
    total:        Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status:       Mapped[str] = mapped_column(String(20), nullable=False, default="CONCLUIDA")
    criado_em:    Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ItemVenda(Base):
    __tablename__ = "item_venda"

    id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venda_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venda.id"))
    produto_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("produto.id"))
    quantidade:     Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal:       Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
