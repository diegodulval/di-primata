import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from oficinas.core.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id:                 Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    nome:               Mapped[str] = mapped_column(Text, nullable=False)
    tipo_pessoa:        Mapped[str | None] = mapped_column(String(10), nullable=True, default="Fisica")
    cpf_cnpj:           Mapped[str | None] = mapped_column(String(14), nullable=True)
    rg:                 Mapped[str | None] = mapped_column(String(20), nullable=True)
    apelido:            Mapped[str | None] = mapped_column(Text, nullable=True)
    data_nascimento:    Mapped[date | None] = mapped_column(Date, nullable=True)
    sexo:               Mapped[str | None] = mapped_column(String(10), nullable=True)
    telefone:           Mapped[str | None] = mapped_column(String(20), nullable=True)
    celular:            Mapped[str | None] = mapped_column(String(20), nullable=True)
    email:              Mapped[str | None] = mapped_column(Text, nullable=True)
    cep:                Mapped[str | None] = mapped_column(String(8), nullable=True)
    endereco:           Mapped[str | None] = mapped_column(Text, nullable=True)
    cidade:             Mapped[str | None] = mapped_column(Text, nullable=True)
    uf:                 Mapped[str | None] = mapped_column(String(2), nullable=True)
    inscricao_estadual: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consumidor_final:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    indicador_ie:       Mapped[str] = mapped_column(String(1), nullable=False, default="9")
    observacoes:        Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo:              Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em:          Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ClienteVeiculo(Base):
    __tablename__ = "cliente_veiculo"

    id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    cliente_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cliente.id"))
    veiculo_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    data_fim:    Mapped[date | None] = mapped_column(Date, nullable=True)
    ativo:       Mapped[bool] = mapped_column(Boolean, default=True)
