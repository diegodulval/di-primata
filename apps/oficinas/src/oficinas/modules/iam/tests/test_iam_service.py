import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from oficinas.core.enums import Perfil
from oficinas.core.exceptions import (
    CredenciaisInvalidas,
    EmailJaCadastrado,
    NaoEncontrado,
    UsuarioInativo,
    WhatsappJaCadastrado,
    WhatsappObrigatorioParaMecanico,
)
from oficinas.core.security import hash_senha, verificar_senha
from oficinas.modules.iam.models import Usuario
from oficinas.modules.iam.schemas import LoginRequest, UsuarioCreate, UsuarioUpdate
from oficinas.modules.iam.service import IamService
from oficinas.modules.iam.tests.conftest import resultado_com, resultado_vazio


# ─── Login ────────────────────────────────────────────────────────────────────

async def test_login_por_email_retorna_token(mock_db, usuario_admin):
    mock_db.execute.return_value = resultado_com(usuario_admin)

    token = await IamService(mock_db).login(
        LoginRequest(identificador="admin@oficina.dev", senha="dev1234")
    )

    assert token and isinstance(token, str)
    mock_db.execute.assert_called_once()


async def test_login_por_whatsapp_tenta_email_primeiro(mock_db, usuario_mecanico):
    mock_db.execute.side_effect = [resultado_vazio(), resultado_com(usuario_mecanico)]

    token = await IamService(mock_db).login(
        LoginRequest(identificador="+5511999990000", senha="dev1234")
    )

    assert token
    assert mock_db.execute.call_count == 2  # tentou email, caiu no whatsapp


async def test_login_nao_encontrado_levanta_credenciais_invalidas(mock_db):
    mock_db.execute.side_effect = [resultado_vazio(), resultado_vazio()]

    with pytest.raises(CredenciaisInvalidas):
        await IamService(mock_db).login(
            LoginRequest(identificador="fantasma@x.dev", senha="qualquer")
        )


async def test_login_senha_errada_levanta_credenciais_invalidas(mock_db, usuario_admin):
    mock_db.execute.return_value = resultado_com(usuario_admin)

    with pytest.raises(CredenciaisInvalidas):
        await IamService(mock_db).login(
            LoginRequest(identificador="admin@oficina.dev", senha="senha_errada")
        )


async def test_login_usuario_inativo_levanta_usuario_inativo(mock_db, tenant_id):
    inativo = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        nome="Inativo",
        email="inativo@x.dev",
        senha_hash=hash_senha("dev1234"),
        perfil=Perfil.ADMIN,
        numero_whatsapp=None,
        ativo=False,
        criado_em=datetime.now(timezone.utc),
    )
    mock_db.execute.return_value = resultado_com(inativo)

    with pytest.raises(UsuarioInativo):
        await IamService(mock_db).login(
            LoginRequest(identificador="inativo@x.dev", senha="dev1234")
        )


# ─── Criar usuário ────────────────────────────────────────────────────────────

async def test_criar_admin_persiste_e_retorna(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()

    usuario = await IamService(mock_db).criar_usuario(
        tenant_id,
        UsuarioCreate(nome="João Admin", perfil=Perfil.ADMIN, email="joao@x.dev", senha="dev1234"),
    )

    assert usuario.nome == "João Admin"
    assert usuario.perfil == Perfil.ADMIN
    assert usuario.email == "joao@x.dev"
    mock_db.add.assert_called_once_with(usuario)
    mock_db.commit.assert_called_once()


async def test_criar_mecanico_sem_email(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()

    usuario = await IamService(mock_db).criar_usuario(
        tenant_id,
        UsuarioCreate(
            nome="Pedro Mecânico",
            perfil=Perfil.MECANICO,
            numero_whatsapp="+5511888880000",
            senha="dev1234",
        ),
    )

    assert usuario.numero_whatsapp == "+5511888880000"
    assert usuario.email is None


async def test_criar_email_duplicado_levanta_email_ja_cadastrado(mock_db, tenant_id, usuario_admin):
    mock_db.execute.return_value = resultado_com(usuario_admin)

    with pytest.raises(EmailJaCadastrado):
        await IamService(mock_db).criar_usuario(
            tenant_id,
            UsuarioCreate(nome="Clone", perfil=Perfil.ADMIN, email="admin@oficina.dev", senha="dev1234"),
        )
    mock_db.add.assert_not_called()


async def test_criar_whatsapp_duplicado_levanta_whatsapp_ja_cadastrado(mock_db, tenant_id, usuario_mecanico):
    mock_db.execute.return_value = resultado_com(usuario_mecanico)

    with pytest.raises(WhatsappJaCadastrado):
        await IamService(mock_db).criar_usuario(
            tenant_id,
            UsuarioCreate(
                nome="Clone Mecânico",
                perfil=Perfil.MECANICO,
                numero_whatsapp="+5511999990000",
                senha="dev1234",
            ),
        )


# ─── Trocar senha ─────────────────────────────────────────────────────────────

async def test_trocar_senha_sucesso_atualiza_hash(mock_db, usuario_admin):
    await IamService(mock_db).trocar_senha(usuario_admin, "dev1234", "nova_super_senha")

    assert verificar_senha("nova_super_senha", usuario_admin.senha_hash)
    mock_db.commit.assert_called_once()


async def test_trocar_senha_errada_nao_commita(mock_db, usuario_admin):
    with pytest.raises(CredenciaisInvalidas):
        await IamService(mock_db).trocar_senha(usuario_admin, "errada", "nova_senha")

    mock_db.commit.assert_not_called()


# ─── Desativar ────────────────────────────────────────────────────────────────

async def test_desativar_usuario_define_ativo_false(mock_db, usuario_admin):
    mock_db.execute.return_value = resultado_com(usuario_admin)

    resultado = await IamService(mock_db).desativar_usuario(usuario_admin.id, usuario_admin.tenant_id)

    assert resultado.ativo is False
    mock_db.commit.assert_called_once()


async def test_desativar_usuario_inexistente_levanta_nao_encontrado(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()

    with pytest.raises(NaoEncontrado):
        await IamService(mock_db).desativar_usuario(uuid.uuid4(), tenant_id)


# ─── Atualizar ────────────────────────────────────────────────────────────────

async def test_atualizar_perfil_mecanico_sem_whatsapp_levanta_erro(mock_db, usuario_admin):
    mock_db.execute.return_value = resultado_com(usuario_admin)

    with pytest.raises(WhatsappObrigatorioParaMecanico):
        await IamService(mock_db).atualizar_usuario(
            usuario_admin.id,
            usuario_admin.tenant_id,
            UsuarioUpdate(perfil=Perfil.MECANICO),
        )


async def test_atualizar_perfil_mecanico_com_whatsapp_no_payload(mock_db, usuario_admin):
    mock_db.execute.return_value = resultado_com(usuario_admin)

    resultado = await IamService(mock_db).atualizar_usuario(
        usuario_admin.id,
        usuario_admin.tenant_id,
        UsuarioUpdate(perfil=Perfil.MECANICO, numero_whatsapp="+5511777770000"),
    )

    assert resultado.perfil == Perfil.MECANICO
    assert resultado.numero_whatsapp == "+5511777770000"


async def test_atualizar_nome(mock_db, usuario_admin):
    mock_db.execute.return_value = resultado_com(usuario_admin)

    resultado = await IamService(mock_db).atualizar_usuario(
        usuario_admin.id,
        usuario_admin.tenant_id,
        UsuarioUpdate(nome="Novo Nome"),
    )

    assert resultado.nome == "Novo Nome"


# ─── Listar e buscar ──────────────────────────────────────────────────────────

async def test_listar_usuarios_retorna_todos_do_tenant(mock_db, tenant_id, usuario_admin, usuario_mecanico):
    lista = MagicMock()
    lista.scalars.return_value.all.return_value = [usuario_admin, usuario_mecanico]
    mock_db.execute.return_value = lista

    items = await IamService(mock_db).listar_usuarios(tenant_id)

    assert len(items) == 2


async def test_buscar_usuario_inexistente_levanta_nao_encontrado(mock_db, tenant_id):
    mock_db.execute.return_value = resultado_vazio()

    with pytest.raises(NaoEncontrado):
        await IamService(mock_db).buscar_usuario(uuid.uuid4(), tenant_id)
