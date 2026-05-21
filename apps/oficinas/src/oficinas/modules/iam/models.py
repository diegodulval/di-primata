import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oficinas.core.database import Base
from oficinas.core.enums import Perfil, RegimeTributario


class Tenant(Base):
    __tablename__ = "tenant"

    id:                Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    razao_social:      Mapped[str]
    cnpj:              Mapped[str] = mapped_column(String(14), unique=True)
    regime_tributario: Mapped[str | None] = mapped_column(
        String, nullable=True,
        default=RegimeTributario.SIMPLES,
    )
    ativo:     Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="tenant")


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        UniqueConstraint("email", "tenant_id", name="uq_usuario_email_tenant"),
    )

    id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id"))
    nome:            Mapped[str]
    # email: nullable — MECANICO se identifica por numero_whatsapp
    email:           Mapped[str | None] = mapped_column(Text, nullable=True)
    senha_hash:      Mapped[str]
    perfil:          Mapped[str] = mapped_column(String, default=Perfil.MECANICO)
    # numero_whatsapp: obrigatório para MECANICO (validado no service)
    numero_whatsapp: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    ativo:           Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em:       Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="usuarios")

    @property
    def perfil_enum(self) -> Perfil:
        return Perfil(self.perfil)
