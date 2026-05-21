import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from oficinas.core.database import Base


class Veiculo(Base):
    __tablename__ = "veiculo"
    __table_args__ = {"schema": "global"}

    id:      Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placa:   Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    chassi:  Mapped[str | None] = mapped_column(String(17), nullable=True)
    marca:   Mapped[str | None] = mapped_column(Text, nullable=True)
    modelo:  Mapped[str | None] = mapped_column(Text, nullable=True)
    ano_fab: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ano_mod: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    cor:     Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo:    Mapped[str | None] = mapped_column(String(10), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class HistoricoVeiculo(Base):
    __tablename__ = "historico_veiculo"
    __table_args__ = {"schema": "global"}

    id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    veiculo_id:      Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    tenant_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    os_id:           Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    data_servico:    Mapped[date] = mapped_column(Date, nullable=False)
    km_entrada:      Mapped[int | None] = mapped_column(Integer, nullable=True)
    resumo_publico:  Mapped[str | None] = mapped_column(Text, nullable=True)
    detalhe_privado: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em:       Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
