"""Testes da integração Twilio WhatsApp."""
# ── Fixtures ──────────────────────────────────────────────────────────────────
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.deps import get_twilio_client
from app.main import app
from app.models.enums import EstadoAgente
from app.models.whatsapp import DirecaoMensagem
from app.repositories.store import Store, get_store
from app.routers.whatsapp import get_settings


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.fixture
def cfg() -> Settings:
    """Settings com validação de assinatura desativada para testes."""
    return Settings(
        twilio_account_sid="",
        twilio_auth_token="",
        twilio_whatsapp_from="+14155238886",
        twilio_validate_signature=False,
    )


@pytest.fixture
def client(store: Store, cfg: Settings):
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_settings] = lambda: cfg
    app.dependency_overrides[get_twilio_client] = lambda: None  # sem chamadas reais ao Twilio
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _webhook(client: TestClient, body: str, phone: str = "+5511999990000", sid: str = "SM001"):
    return client.post(
        "/whatsapp/webhook",
        data={
            "From": f"whatsapp:{phone}",
            "To": "whatsapp:+14155238886",
            "Body": body,
            "MessageSid": sid,
            "NumMedia": "0",
            "ProfileName": "João Produtor",
        },
    )


# ── Testes ────────────────────────────────────────────────────────────────────

def test_webhook_cria_sessao(client, store):
    resp = _webhook(client, "Olá")
    assert resp.status_code == 200

    sessoes = store.whatsapp_sessoes.list_all()
    assert len(sessoes) == 1
    assert sessoes[0].phone == "+5511999990000"
    assert sessoes[0].profile_name == "João Produtor"


def test_webhook_registra_mensagem_inbound(client, store):
    _webhook(client, "Olá")

    sessoes = store.whatsapp_sessoes.list_all()
    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessoes[0].id)
    inbound = [m for m in msgs if m.direcao == DirecaoMensagem.INBOUND]
    assert len(inbound) == 1
    assert inbound[0].corpo == "Olá"
    assert inbound[0].sid == "SM001"


def test_webhook_responde_menu_inicial(client, store):
    resp = _webhook(client, "Oi")
    assert resp.status_code == 200

    sessoes = store.whatsapp_sessoes.list_all()
    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessoes[0].id)
    outbound = [m for m in msgs if m.direcao == DirecaoMensagem.OUTBOUND]
    assert len(outbound) == 1
    assert "Di Mata" in outbound[0].corpo


def test_webhook_mesma_sessao_reutilizada(client, store):
    _webhook(client, "Oi", sid="SM001")
    _webhook(client, "1", sid="SM002")

    assert len(store.whatsapp_sessoes.list_all()) == 1, "Deve reutilizar a sessão existente"


def test_webhook_sessoes_distintas_por_phone(client, store):
    _webhook(client, "Oi", phone="+5511111110001", sid="SM001")
    _webhook(client, "Oi", phone="+5511111110002", sid="SM002")

    assert len(store.whatsapp_sessoes.list_all()) == 2


def test_webhook_opcao_registrar_atividade(client, store):
    _webhook(client, "oi", sid="SM001")  # estado → ESCUTANDO
    _webhook(client, "1", sid="SM002")   # seleciona opção 1

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO
    assert sessao.contexto_json.get("fluxo") == "registrar_atividade"


def test_webhook_opcao_tecnico(client, store):
    _webhook(client, "qualquer", sid="SM001")  # → ESCUTANDO
    _webhook(client, "3", sid="SM002")          # → OCIOSO

    assert store.whatsapp_sessoes.list_all()[0].estado == EstadoAgente.OCIOSO


def test_webhook_sem_from_ignorado(client, store):
    resp = client.post(
        "/whatsapp/webhook",
        data={"Body": "teste", "MessageSid": "SM999", "NumMedia": "0"},
    )
    assert resp.status_code == 200
    assert store.whatsapp_sessoes.list_all() == []


def test_reset_keyword_reinicia_sessao(client, store):
    _webhook(client, "oi", sid="SM001")   # → ESCUTANDO
    _webhook(client, "1", sid="SM002")    # → PROCESSANDO
    _webhook(client, "menu", sid="SM003") # deve resetar → ESCUTANDO (após exibir menu)

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO
    assert sessao.contexto_json == {}


@pytest.mark.parametrize("kw", ["reiniciar", "0", "voltar", "cancelar", "início", "inicio"])
def test_reset_keywords_variantes(client, store, kw):
    _webhook(client, "oi", sid="SM001")  # → ESCUTANDO
    _webhook(client, "1", sid="SM002")   # → PROCESSANDO

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO

    resp = _webhook(client, kw, sid="SM003")
    assert resp.status_code == 200, f"falhou com keyword '{kw}'"

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json == {}, f"contexto não limpo para '{kw}'"
    assert sessao.estado == EstadoAgente.ESCUTANDO, f"estado errado para '{kw}'"


def test_list_sessions(client, store):
    _webhook(client, "oi")
    resp = client.get("/whatsapp/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["phone"] == "+5511999990000"
