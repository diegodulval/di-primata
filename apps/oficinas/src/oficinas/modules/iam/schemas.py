import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from oficinas.core.enums import Perfil


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """
    ADMIN/ATENDENTE: identificador = email.
    MECANICO: identificador = numero_whatsapp (ex: +5511999990000).
    """
    identificador: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: Perfil


# ─── Criação de usuário (admin only) ──────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nome: str
    perfil: Perfil
    senha: str

    # ADMIN / ATENDENTE: email obrigatório
    email: str | None = None

    # MECANICO: whatsapp obrigatório, e-mail opcional
    numero_whatsapp: str | None = None

    @model_validator(mode="after")
    def validar_campos_por_perfil(self):
        if self.perfil in (Perfil.ADMIN, Perfil.ATENDENTE):
            if not self.email:
                raise ValueError("email é obrigatório para ADMIN e ATENDENTE")
        if self.perfil == Perfil.MECANICO:
            if not self.numero_whatsapp:
                raise ValueError("numero_whatsapp é obrigatório para MECANICO")
        return self


# ─── Troca de senha ───────────────────────────────────────────────────────────

class TrocarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str

    @field_validator("nova_senha")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("nova_senha deve ter no mínimo 8 caracteres")
        return v


# ─── Atualização pelo admin ───────────────────────────────────────────────────

class UsuarioUpdate(BaseModel):
    nome: str | None = None
    perfil: Perfil | None = None
    numero_whatsapp: str | None = None
    ativo: bool | None = None


# ─── Responses ────────────────────────────────────────────────────────────────

class UsuarioResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nome: str
    email: str | None
    perfil: Perfil
    numero_whatsapp: str | None
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class UsuarioListResponse(BaseModel):
    total: int
    items: list[UsuarioResponse]
