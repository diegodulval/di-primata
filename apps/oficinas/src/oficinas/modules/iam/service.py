import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.enums import Perfil
from oficinas.core.exceptions import (
    CredenciaisInvalidas,
    EmailJaCadastrado,
    NaoEncontrado,
    UsuarioInativo,
    WhatsappJaCadastrado,
    WhatsappObrigatorioParaMecanico,
)
from oficinas.core.security import criar_token, hash_senha, verificar_senha
from oficinas.modules.iam.models import Usuario
from oficinas.modules.iam.schemas import LoginRequest, UsuarioCreate, UsuarioUpdate

log = structlog.get_logger()


class IamService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Login ────────────────────────────────────────────────────────────────

    async def login(self, payload: LoginRequest) -> str:
        """
        Tenta encontrar o usuário por email (ADMIN/ATENDENTE)
        ou por numero_whatsapp (MECANICO).
        Retorna JWT em caso de sucesso.
        """
        usuario = await self._buscar_por_identificador(payload.identificador)

        if not usuario:
            log.info("login_falhou", motivo="nao_encontrado", identificador=payload.identificador)
            raise CredenciaisInvalidas("Credenciais inválidas")

        if not verificar_senha(payload.senha, usuario.senha_hash):
            log.info("login_falhou", motivo="senha_errada", usuario_id=str(usuario.id))
            raise CredenciaisInvalidas("Credenciais inválidas")

        if not usuario.ativo:
            log.info("login_bloqueado", usuario_id=str(usuario.id))
            raise UsuarioInativo("Usuário inativo")

        token = criar_token(usuario.id, usuario.tenant_id, Perfil(usuario.perfil))
        log.info("login_ok", usuario_id=str(usuario.id), perfil=usuario.perfil)
        return token

    async def _buscar_por_identificador(self, identificador: str) -> Usuario | None:
        """Tenta email primeiro, depois numero_whatsapp."""
        stmt = select(Usuario).where(Usuario.email == identificador)
        usuario = (await self.db.execute(stmt)).scalar_one_or_none()
        if usuario:
            return usuario

        stmt = select(Usuario).where(Usuario.numero_whatsapp == identificador)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    # ─── Criação de usuário (admin) ───────────────────────────────────────────

    async def criar_usuario(
        self,
        tenant_id: uuid.UUID,
        payload: UsuarioCreate,
    ) -> Usuario:
        await self._validar_unicidade(payload, tenant_id)

        usuario = Usuario(
            tenant_id=tenant_id,
            nome=payload.nome,
            email=payload.email,
            senha_hash=hash_senha(payload.senha),
            perfil=payload.perfil,
            numero_whatsapp=payload.numero_whatsapp,
        )
        self.db.add(usuario)
        await self.db.commit()
        await self.db.refresh(usuario)

        log.info(
            "usuario_criado",
            usuario_id=str(usuario.id),
            perfil=usuario.perfil,
            tenant_id=str(tenant_id),
        )
        return usuario

    async def _validar_unicidade(self, payload: UsuarioCreate, tenant_id: uuid.UUID) -> None:
        if payload.email:
            stmt = select(Usuario).where(
                Usuario.email == payload.email,
                Usuario.tenant_id == tenant_id,
            )
            if (await self.db.execute(stmt)).scalar_one_or_none():
                raise EmailJaCadastrado(f"Email '{payload.email}' já cadastrado")

        if payload.numero_whatsapp:
            stmt = select(Usuario).where(
                Usuario.numero_whatsapp == payload.numero_whatsapp
            )
            if (await self.db.execute(stmt)).scalar_one_or_none():
                raise WhatsappJaCadastrado(
                    f"WhatsApp '{payload.numero_whatsapp}' já cadastrado"
                )

    # ─── Listagem e detalhe ───────────────────────────────────────────────────

    async def listar_usuarios(self, tenant_id: uuid.UUID) -> list[Usuario]:
        stmt = (
            select(Usuario)
            .where(Usuario.tenant_id == tenant_id)
            .order_by(Usuario.perfil, Usuario.nome)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows)

    async def buscar_usuario(self, usuario_id: uuid.UUID, tenant_id: uuid.UUID) -> Usuario:
        stmt = select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.tenant_id == tenant_id,
        )
        usuario = (await self.db.execute(stmt)).scalar_one_or_none()
        if not usuario:
            raise NaoEncontrado(f"Usuário {usuario_id} não encontrado")
        return usuario

    # ─── Atualização pelo admin ───────────────────────────────────────────────

    async def atualizar_usuario(
        self,
        usuario_id: uuid.UUID,
        tenant_id: uuid.UUID,
        payload: UsuarioUpdate,
    ) -> Usuario:
        usuario = await self.buscar_usuario(usuario_id, tenant_id)

        if payload.nome is not None:
            usuario.nome = payload.nome
        if payload.perfil is not None:
            # Se mudar para MECANICO, garante que tem WhatsApp
            if payload.perfil == Perfil.MECANICO and not (
                usuario.numero_whatsapp or payload.numero_whatsapp
            ):
                raise WhatsappObrigatorioParaMecanico(
                    "número WhatsApp obrigatório para MECANICO"
                )
            usuario.perfil = payload.perfil
        if payload.numero_whatsapp is not None:
            usuario.numero_whatsapp = payload.numero_whatsapp
        if payload.ativo is not None:
            usuario.ativo = payload.ativo

        await self.db.commit()
        await self.db.refresh(usuario)
        log.info("usuario_atualizado", usuario_id=str(usuario_id))
        return usuario

    # ─── Troca de senha ───────────────────────────────────────────────────────

    async def trocar_senha(
        self,
        usuario: Usuario,
        senha_atual: str,
        nova_senha: str,
    ) -> None:
        if not verificar_senha(senha_atual, usuario.senha_hash):
            raise CredenciaisInvalidas("Senha atual incorreta")
        usuario.senha_hash = hash_senha(nova_senha)
        await self.db.commit()
        log.info("senha_trocada", usuario_id=str(usuario.id))

    # ─── Desativação (soft-delete) ────────────────────────────────────────────

    async def desativar_usuario(
        self, usuario_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Usuario:
        usuario = await self.buscar_usuario(usuario_id, tenant_id)
        usuario.ativo = False
        await self.db.commit()
        await self.db.refresh(usuario)
        log.info("usuario_desativado", usuario_id=str(usuario_id))
        return usuario
