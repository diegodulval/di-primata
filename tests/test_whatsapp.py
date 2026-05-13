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


# ── Fixtures: domínio ─────────────────────────────────────────────────────────

@pytest.fixture
def account(store):
    from app.models.account import Account
    from app.models.enums import PlanoAssinatura
    acc = Account(
        nome="Fazenda Teste",
        documento="12345678000199",
        email="fazenda@teste.com",
        plano=PlanoAssinatura.FREE,
        setor_primario="cafe",
        whatsapp_phone="+5511999990000",
    )
    store.accounts.save(acc)
    return acc


@pytest.fixture
def unit(store, account):
    from app.models.enums import TipoUnidade
    from app.models.unit import Unit
    u = Unit(
        account_id=account.id,
        nome="Talhão Norte",
        tipo=TipoUnidade.TALHAO,
        area_capacidade=12.5,
        setor_template="cafe",
    )
    store.units.save(u)
    return u


@pytest.fixture
def two_units(store, account):
    from app.models.enums import TipoUnidade
    from app.models.unit import Unit
    u1 = Unit(account_id=account.id, nome="Talhão Norte", tipo=TipoUnidade.TALHAO, setor_template="cafe")
    u2 = Unit(account_id=account.id, nome="Talhão Sul",   tipo=TipoUnidade.TALHAO, setor_template="cafe")
    store.units.save(u1)
    store.units.save(u2)
    return u1, u2


# ── Testes: sessão e mensagens ────────────────────────────────────────────────

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


def test_webhook_responde_mensagem_inicial(client, store):
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


def test_webhook_sem_from_ignorado(client, store):
    resp = client.post(
        "/whatsapp/webhook",
        data={"Body": "teste", "MessageSid": "SM999", "NumMedia": "0"},
    )
    assert resp.status_code == 200
    assert store.whatsapp_sessoes.list_all() == []


def test_list_sessions(client, store):
    _webhook(client, "oi")
    resp = client.get("/whatsapp/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["phone"] == "+5511999990000"


# ── Testes: vínculo conta ─────────────────────────────────────────────────────

def test_sessao_vincula_account_id(client, store, account):
    _webhook(client, "oi")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.account_id == account.id


def test_sessao_sem_conta_inicia_identificacao(client, store):
    """Sem conta cadastrada, primeira mensagem inicia fluxo de identificação."""
    _webhook(client, "oi")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.account_id is None
    assert sessao.estado == EstadoAgente.PROCESSANDO
    assert sessao.contexto_json.get("fluxo") == "identificar_contexto"
    assert sessao.contexto_json.get("passo") == "propriedade"


# ── Testes: identificação de propriedade e talhão ────────────────────────────

def test_fluxo_cadastro_nova_propriedade_e_talhao(client, store):
    """Usuário sem conta cadastra propriedade e talhão pelo próprio WhatsApp."""
    _webhook(client, "oi",           sid="SM001")   # → pede nome da propriedade
    _webhook(client, "Fazenda Nova", sid="SM002")   # → não encontrada → confirmar?
    _webhook(client, "sim",          sid="SM003")   # → cria propriedade → pede talhão
    _webhook(client, "Talhão A",     sid="SM004")   # → cria talhão → menu

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO
    assert sessao.account_id is not None
    assert sessao.unit_id is not None

    conta = store.accounts.get(sessao.account_id)
    assert conta.nome == "Fazenda Nova"
    assert conta.whatsapp_phone == "+5511999990000"

    talhao = store.units.get(sessao.unit_id)
    assert talhao.nome == "Talhão A"


def test_fluxo_recusa_cadastro_pede_nome_novamente(client, store):
    """Se recusar cadastro, bot pede o nome da propriedade de novo."""
    _webhook(client, "oi",           sid="SM001")
    _webhook(client, "Fazenda Nova", sid="SM002")
    _webhook(client, "não",          sid="SM003")   # → recusa → pede nome de novo

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json.get("passo") == "propriedade"
    assert store.accounts.list_all() == []           # nada criado


def test_fluxo_propriedade_existente_pula_cadastro(client, store, account, unit):
    """Se propriedade existir, vincula e vai direto para seleção de talhão."""
    _webhook(client, "oi",           sid="SM001")
    _webhook(client, "Fazenda Teste",sid="SM002")   # → encontrada → pede talhão

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.account_id == account.id
    assert sessao.contexto_json.get("passo") == "selecionar_talhao"


def test_identificacao_selecionar_talhao_multiplos(client, store, account, two_units):
    """Com dois talhões cadastrados, bot lista as opções na identificação."""
    u1, u2 = two_units
    _webhook(client, "oi", sid="SM001")

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json.get("passo") == "selecionar_talhao"

    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessao.id)
    outbound = [m for m in msgs if m.direcao == DirecaoMensagem.OUTBOUND]
    assert "Talhão Norte" in outbound[-1].corpo
    assert "Talhão Sul" in outbound[-1].corpo


def test_identificacao_selecionar_talhao_opcao_invalida(client, store, account, two_units):
    _webhook(client, "oi", sid="SM001")
    resp = _webhook(client, "9", sid="SM002")
    assert resp.status_code == 200

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json.get("passo") == "selecionar_talhao"


def test_identificacao_novo_talhao_em_conta_existente(client, store, account):
    """Usuário com conta mas sem talhão pode criar um novo."""
    _webhook(client, "oi",       sid="SM001")   # → sem talhão → pede criar novo
    _webhook(client, "Talhão B", sid="SM002")   # → cria talhão → menu

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO
    assert sessao.unit_id is not None
    talhao = store.units.get(sessao.unit_id)
    assert talhao.nome == "Talhão B"


# ── Testes: menu e navegação ──────────────────────────────────────────────────

def test_webhook_opcao_registrar_atividade(client, store, account, unit):
    _webhook(client, "oi", sid="SM001")   # → talhão question
    _webhook(client, "1",  sid="SM002")   # → seleciona talhão → menu
    _webhook(client, "1",  sid="SM003")   # → registrar atividade

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO
    assert sessao.contexto_json.get("fluxo") == "registrar_atividade"


def test_webhook_opcao_tecnico(client, store, account, unit):
    _webhook(client, "oi", sid="SM001")
    _webhook(client, "1",  sid="SM002")
    _webhook(client, "3",  sid="SM003")

    assert store.whatsapp_sessoes.list_all()[0].estado == EstadoAgente.OCIOSO


def test_reset_keyword_reinicia_sessao(client, store, account, unit):
    _webhook(client, "oi",   sid="SM001")  # → talhão question
    _webhook(client, "1",    sid="SM002")  # → menu
    _webhook(client, "1",    sid="SM003")  # → PROCESSANDO
    _webhook(client, "menu", sid="SM004")  # → reset → menu

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO
    assert sessao.contexto_json == {}


@pytest.mark.parametrize("kw", ["reiniciar", "0", "voltar", "cancelar", "início", "inicio"])
def test_reset_keywords_variantes(client, store, account, unit, kw):
    _webhook(client, "oi", sid="SM001")
    _webhook(client, "1",  sid="SM002")
    _webhook(client, "1",  sid="SM003")  # → PROCESSANDO

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO

    resp = _webhook(client, kw, sid="SM004")
    assert resp.status_code == 200, f"falhou com keyword '{kw}'"

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json == {}, f"contexto não limpo para '{kw}'"
    assert sessao.estado == EstadoAgente.ESCUTANDO, f"estado errado para '{kw}'"


# ── Testes: fluxo adubação ────────────────────────────────────────────────────

def test_adubacao_fluxo_completo_um_talhao(client, store, account, unit):
    _webhook(client, "oi",  sid="SM001")  # → talhão question
    _webhook(client, "1",   sid="SM002")  # → seleciona talhão → menu
    _webhook(client, "1",   sid="SM003")  # → registrar atividade → menu atividades
    _webhook(client, "1",   sid="SM004")  # → opção 1 = adubação
    _webhook(client, "350", sid="SM005")
    _webhook(client, "sim", sid="SM006")

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.OCIOSO
    assert sessao.contexto_json == {}

    ciclos = store.cycles.list_by(account_id=account.id, unit_id=unit.id)
    assert len(ciclos) == 1

    from app.models.enums import TipoEvento
    eventos = store.events.list_by(ciclo_id=ciclos[0].id)
    assert len(eventos) == 1
    assert eventos[0].tipo_evento == TipoEvento.ENTRADA_INSUMO
    assert eventos[0].custo == 350.0
    assert eventos[0].payload_json.get("origem_wpp") is True


def test_adubacao_valor_com_virgula(client, store, account, unit):
    _webhook(client, "oi",       sid="SM001")
    _webhook(client, "1",        sid="SM002")
    _webhook(client, "1",        sid="SM003")
    _webhook(client, "1",        sid="SM004")  # opção 1 = adubação
    _webhook(client, "1.250,50", sid="SM005")
    _webhook(client, "sim",      sid="SM006")

    ciclos = store.cycles.list_by(account_id=account.id, unit_id=unit.id)
    eventos = store.events.list_by(ciclo_id=ciclos[0].id)
    assert eventos[0].custo == 1250.50


def test_adubacao_cancelar_nao_persiste_evento(client, store, account, unit):
    _webhook(client, "oi",  sid="SM001")
    _webhook(client, "1",   sid="SM002")
    _webhook(client, "1",   sid="SM003")
    _webhook(client, "1",   sid="SM004")  # opção 1 = adubação
    _webhook(client, "200", sid="SM005")
    _webhook(client, "não", sid="SM006")

    assert store.cycles.list_all() == []
    assert store.events.list_all() == []

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO


def test_adubacao_atividade_nao_reconhecida(client, store, account, unit):
    _webhook(client, "oi",  sid="SM001")
    _webhook(client, "1",   sid="SM002")
    _webhook(client, "1",   sid="SM003")
    resp = _webhook(client, "9", sid="SM004")  # opção fora do intervalo
    assert resp.status_code == 200

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO

    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessao.id)
    outbound = [m for m in msgs if m.direcao == DirecaoMensagem.OUTBOUND]
    assert "Opção inválida" in outbound[-1].corpo


def test_adubacao_valor_invalido_pede_novamente(client, store, account, unit):
    _webhook(client, "oi",  sid="SM001")
    _webhook(client, "1",   sid="SM002")
    _webhook(client, "1",   sid="SM003")
    _webhook(client, "1",   sid="SM004")  # opção 1 = adubação
    resp = _webhook(client, "abc", sid="SM005")
    assert resp.status_code == 200

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO
    assert sessao.contexto_json.get("passo") == "valor_gasto"


def test_adubacao_com_dois_talhoes_usa_selecionado(client, store, account, two_units):
    """Após selecionar talhão na identificação, atividade usa esse talhão sem perguntar."""
    u1, u2 = two_units
    _webhook(client, "oi",  sid="SM001")  # → selecionar talhão
    _webhook(client, "1",   sid="SM002")  # → talhão Norte → menu
    _webhook(client, "1",   sid="SM003")  # → registrar atividade → menu atividades
    _webhook(client, "1",   sid="SM004")  # → opção 1 = adubação → pede valor
    _webhook(client, "200", sid="SM005")
    _webhook(client, "sim", sid="SM006")

    ciclos = store.cycles.list_by(account_id=account.id, unit_id=u1.id)
    assert len(ciclos) == 1
    eventos = store.events.list_by(ciclo_id=ciclos[0].id)
    assert len(eventos) == 1


# ── Testes: segundo evento reutiliza ciclo aberto ─────────────────────────────

def test_segundo_registro_reutiliza_ciclo(client, store, account, unit):
    # Primeira iteração: inclui seleção de talhão
    _webhook(client, "oi",  sid="SM001")
    _webhook(client, "1",   sid="SM002")  # → seleciona talhão
    _webhook(client, "1",   sid="SM003")  # → registrar atividade → menu atividades
    _webhook(client, "1",   sid="SM004")  # → opção 1 = adubação
    _webhook(client, "150", sid="SM005")
    _webhook(client, "sim", sid="SM006")

    # Segunda iteração: unit_id já persistido → vai direto ao menu
    _webhook(client, "oi",  sid="SM007")
    _webhook(client, "1",   sid="SM008")  # → registrar atividade → menu atividades
    _webhook(client, "2",   sid="SM009")  # → opção 2 = irrigação
    _webhook(client, "80",  sid="SM010")
    _webhook(client, "sim", sid="SM011")

    assert len(store.cycles.list_all()) == 1, "Deve reutilizar o ciclo existente"
    assert len(store.events.list_all()) == 2
