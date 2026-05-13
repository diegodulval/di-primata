"""Testes da Camada 1 — Entrada/Recebimento (webhook HTTP)."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.deps import get_debounce_buffer, get_rate_limiter
from app.ingestion.debounce import DebounceBuffer
from app.ingestion.rate_limiter import FixedWindowRateLimiter
from app.main import app
from app.repositories.store import Store, get_store
from app.routers.whatsapp import get_settings


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.fixture
def cfg() -> Settings:
    return Settings(
        twilio_account_sid="",
        twilio_auth_token="",
        twilio_whatsapp_from="+14155238886",
        twilio_validate_signature=False,
    )


@pytest.fixture
def debounce() -> DebounceBuffer:
    return DebounceBuffer(pool=None, window_seconds=9999)  # timer nunca dispara nos testes


@pytest.fixture
def rate_limiter() -> FixedWindowRateLimiter:
    return FixedWindowRateLimiter(max_requests=3, window_seconds=60)


@pytest.fixture
def client(store, cfg, debounce, rate_limiter):
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_settings] = lambda: cfg
    app.dependency_overrides[get_debounce_buffer] = lambda: debounce
    app.dependency_overrides[get_rate_limiter] = lambda: rate_limiter
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _webhook(client: TestClient, body: str = "oi", phone: str = "+5511999990000",
             sid: str = "SM001", num_media: int = 0):
    data = {
        "From": f"whatsapp:{phone}",
        "To": "whatsapp:+14155238886",
        "Body": body,
        "MessageSid": sid,
        "NumMedia": str(num_media),
        "ProfileName": "João Produtor",
    }
    return client.post("/whatsapp/webhook", data=data)


# ── Comportamento básico ──────────────────────────────────────────────────────

def test_webhook_retorna_200(client):
    resp = _webhook(client)
    assert resp.status_code == 200


def test_webhook_sem_from_retorna_200(client, store):
    resp = client.post("/whatsapp/webhook", data={"Body": "teste", "MessageSid": "SM999", "NumMedia": "0"})
    assert resp.status_code == 200
    assert store.whatsapp_sessoes.list_all() == []


def test_webhook_nao_processa_sincronamente(client, store):
    """Layer 1 não cria sessões — processamento é assíncrono (Layer 2)."""
    _webhook(client)
    assert store.whatsapp_sessoes.list_all() == []


# ── Normalização ──────────────────────────────────────────────────────────────

def test_webhook_normaliza_phone(client, debounce):
    _webhook(client, phone="+5511999990000", sid="SM001")
    assert len(debounce._buffers) == 1
    assert "+5511999990000" in debounce._buffers
    msg = debounce._buffers["+5511999990000"][0]
    assert msg.phone == "+5511999990000"
    assert msg.profile_name == "João Produtor"
    assert msg.message_sid == "SM001"


def test_webhook_remove_prefixo_whatsapp(client, debounce):
    _webhook(client, phone="+5511888880000")
    phone_key = list(debounce._buffers.keys())[0]
    assert not phone_key.startswith("whatsapp:")


# ── Debounce buffer ───────────────────────────────────────────────────────────

def test_webhook_acumula_mensagens_no_buffer(client, debounce):
    _webhook(client, body="primeira", sid="SM001")
    _webhook(client, body="segunda",  sid="SM002")
    assert len(debounce._buffers["+5511999990000"]) == 2


def test_webhook_phones_distintos_buffers_separados(client, debounce):
    _webhook(client, phone="+5511000000001", sid="SM001")
    _webhook(client, phone="+5511000000002", sid="SM002")
    assert len(debounce._buffers) == 2


# ── Mídia ─────────────────────────────────────────────────────────────────────

def test_webhook_midia_ignorada_retorna_200(client, debounce):
    resp = _webhook(client, num_media=1)
    assert resp.status_code == 200


def test_webhook_midia_nao_entra_no_buffer(client, debounce):
    _webhook(client, num_media=1)
    assert len(debounce._buffers) == 0


# ── Rate limit ────────────────────────────────────────────────────────────────

def test_webhook_rate_limit_bloqueia_apos_limite(client, debounce, rate_limiter):
    """Com max_requests=3, a 4ª mensagem é silenciosamente descartada."""
    for i in range(3):
        resp = _webhook(client, sid=f"SM00{i}")
        assert resp.status_code == 200

    resp_extra = _webhook(client, sid="SM999")
    assert resp_extra.status_code == 200  # sempre 200 ao Twilio

    assert len(debounce._buffers.get("+5511999990000", [])) == 3


def test_webhook_rate_limit_independente_por_phone(client, debounce, rate_limiter):
    """Rate limit é por phone — outro phone não é afetado."""
    for i in range(3):
        _webhook(client, phone="+5511000000001", sid=f"SM00{i}")

    # phone diferente ainda passa
    resp = _webhook(client, phone="+5511000000002", sid="SM099")
    assert resp.status_code == 200
    assert len(debounce._buffers.get("+5511000000002", [])) == 1


# ── Endpoints auxiliares (não alterados) ──────────────────────────────────────

def test_list_sessions_retorna_lista_vazia(client):
    resp = client.get("/whatsapp/sessions")
    assert resp.status_code == 200
    assert resp.json() == []
