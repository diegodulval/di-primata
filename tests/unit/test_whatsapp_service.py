"""Testes unitários do WhatsappService (chamado diretamente, sem HTTP)."""
import pytest

from app.models.enums import EstadoAgente
from app.models.whatsapp import DirecaoMensagem
from app.repositories.store import Store
from app.services.whatsapp_service import WhatsappService

TWILIO_FROM = "+14155238886"


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.fixture
def svc(store) -> WhatsappService:
    return WhatsappService(store, twilio_client=None, from_number=TWILIO_FROM)


def _send(svc: WhatsappService, body: str, phone: str = "+5511999990000", sid: str = "SM001"):
    svc.processar_webhook({
        "From": f"whatsapp:{phone}",
        "To": f"whatsapp:{TWILIO_FROM}",
        "Body": body,
        "MessageSid": sid,
        "NumMedia": "0",
        "ProfileName": "João Produtor",
    })


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


# ── Sessão e mensagens ────────────────────────────────────────────────────────

def test_webhook_cria_sessao(svc, store):
    _send(svc, "Olá")
    sessoes = store.whatsapp_sessoes.list_all()
    assert len(sessoes) == 1
    assert sessoes[0].phone == "+5511999990000"
    assert sessoes[0].profile_name == "João Produtor"


def test_webhook_registra_mensagem_inbound(svc, store):
    _send(svc, "Olá")
    sessoes = store.whatsapp_sessoes.list_all()
    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessoes[0].id)
    inbound = [m for m in msgs if m.direcao == DirecaoMensagem.INBOUND]
    assert len(inbound) == 1
    assert inbound[0].corpo == "Olá"
    assert inbound[0].sid == "SM001"


def test_webhook_responde_mensagem_inicial(svc, store):
    _send(svc, "Oi")
    sessoes = store.whatsapp_sessoes.list_all()
    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessoes[0].id)
    outbound = [m for m in msgs if m.direcao == DirecaoMensagem.OUTBOUND]
    assert len(outbound) == 1
    assert "Di Mata" in outbound[0].corpo


def test_webhook_mesma_sessao_reutilizada(svc, store):
    _send(svc, "Oi", sid="SM001")
    _send(svc, "1", sid="SM002")
    assert len(store.whatsapp_sessoes.list_all()) == 1


def test_webhook_sessoes_distintas_por_phone(svc, store):
    _send(svc, "Oi", phone="+5511111110001", sid="SM001")
    _send(svc, "Oi", phone="+5511111110002", sid="SM002")
    assert len(store.whatsapp_sessoes.list_all()) == 2


# ── Vínculo conta ─────────────────────────────────────────────────────────────

def test_sessao_vincula_account_id(svc, store, account):
    _send(svc, "oi")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.account_id == account.id


def test_sessao_sem_conta_inicia_identificacao(svc, store):
    _send(svc, "oi")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.account_id is None
    assert sessao.estado == EstadoAgente.PROCESSANDO
    assert sessao.contexto_json.get("fluxo") == "identificar_contexto"
    assert sessao.contexto_json.get("passo") == "propriedade"


# ── Identificação de propriedade e talhão ────────────────────────────────────

def test_fluxo_cadastro_nova_propriedade_e_talhao(svc, store):
    _send(svc, "oi",           sid="SM001")
    _send(svc, "Fazenda Nova", sid="SM002")
    _send(svc, "sim",          sid="SM003")
    _send(svc, "Talhão A",     sid="SM004")

    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO
    assert sessao.account_id is not None
    assert sessao.unit_id is not None

    conta = store.accounts.get(sessao.account_id)
    assert conta.nome == "Fazenda Nova"
    assert conta.whatsapp_phone == "+5511999990000"

    talhao = store.units.get(sessao.unit_id)
    assert talhao.nome == "Talhão A"


def test_fluxo_recusa_cadastro_pede_nome_novamente(svc, store):
    _send(svc, "oi",           sid="SM001")
    _send(svc, "Fazenda Nova", sid="SM002")
    _send(svc, "não",          sid="SM003")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json.get("passo") == "propriedade"
    assert store.accounts.list_all() == []


def test_fluxo_propriedade_existente_pula_cadastro(svc, store, account, unit):
    _send(svc, "oi",            sid="SM001")
    _send(svc, "Fazenda Teste", sid="SM002")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.account_id == account.id
    assert sessao.contexto_json.get("passo") == "selecionar_talhao"


def test_identificacao_selecionar_talhao_multiplos(svc, store, account, two_units):
    u1, u2 = two_units
    _send(svc, "oi", sid="SM001")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json.get("passo") == "selecionar_talhao"
    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessao.id)
    outbound = [m for m in msgs if m.direcao == DirecaoMensagem.OUTBOUND]
    assert "Talhão Norte" in outbound[-1].corpo
    assert "Talhão Sul" in outbound[-1].corpo


def test_identificacao_selecionar_talhao_opcao_invalida(svc, store, account, two_units):
    _send(svc, "oi", sid="SM001")
    _send(svc, "9",  sid="SM002")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json.get("passo") == "selecionar_talhao"


def test_identificacao_novo_talhao_em_conta_existente(svc, store, account):
    _send(svc, "oi",       sid="SM001")
    _send(svc, "Talhão B", sid="SM002")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO
    assert sessao.unit_id is not None
    assert store.units.get(sessao.unit_id).nome == "Talhão B"


# ── Menu e navegação ──────────────────────────────────────────────────────────

def test_webhook_opcao_registrar_atividade(svc, store, account, unit):
    _send(svc, "oi", sid="SM001")
    _send(svc, "1",  sid="SM002")
    _send(svc, "1",  sid="SM003")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO
    assert sessao.contexto_json.get("fluxo") == "registrar_atividade"


def test_webhook_opcao_tecnico(svc, store, account, unit):
    _send(svc, "oi", sid="SM001")
    _send(svc, "1",  sid="SM002")
    _send(svc, "3",  sid="SM003")
    assert store.whatsapp_sessoes.list_all()[0].estado == EstadoAgente.OCIOSO


def test_reset_keyword_reinicia_sessao(svc, store, account, unit):
    _send(svc, "oi",   sid="SM001")
    _send(svc, "1",    sid="SM002")
    _send(svc, "1",    sid="SM003")
    _send(svc, "menu", sid="SM004")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.ESCUTANDO
    assert sessao.contexto_json == {}


@pytest.mark.parametrize("kw", ["reiniciar", "0", "voltar", "cancelar", "início", "inicio"])
def test_reset_keywords_variantes(svc, store, account, unit, kw):
    _send(svc, "oi", sid="SM001")
    _send(svc, "1",  sid="SM002")
    _send(svc, "1",  sid="SM003")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO
    _send(svc, kw, sid="SM004")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.contexto_json == {}, f"contexto não limpo para '{kw}'"
    assert sessao.estado == EstadoAgente.ESCUTANDO, f"estado errado para '{kw}'"


# ── Fluxo adubação ────────────────────────────────────────────────────────────

def test_adubacao_fluxo_completo_um_talhao(svc, store, account, unit):
    _send(svc, "oi",  sid="SM001")
    _send(svc, "1",   sid="SM002")
    _send(svc, "1",   sid="SM003")
    _send(svc, "1",   sid="SM004")
    _send(svc, "350", sid="SM005")
    _send(svc, "sim", sid="SM006")

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


def test_adubacao_valor_com_virgula(svc, store, account, unit):
    _send(svc, "oi",       sid="SM001")
    _send(svc, "1",        sid="SM002")
    _send(svc, "1",        sid="SM003")
    _send(svc, "1",        sid="SM004")
    _send(svc, "1.250,50", sid="SM005")
    _send(svc, "sim",      sid="SM006")
    ciclos = store.cycles.list_by(account_id=account.id, unit_id=unit.id)
    eventos = store.events.list_by(ciclo_id=ciclos[0].id)
    assert eventos[0].custo == 1250.50


def test_adubacao_cancelar_nao_persiste_evento(svc, store, account, unit):
    _send(svc, "oi",  sid="SM001")
    _send(svc, "1",   sid="SM002")
    _send(svc, "1",   sid="SM003")
    _send(svc, "1",   sid="SM004")
    _send(svc, "200", sid="SM005")
    _send(svc, "não", sid="SM006")
    assert store.cycles.list_all() == []
    assert store.events.list_all() == []
    assert store.whatsapp_sessoes.list_all()[0].estado == EstadoAgente.ESCUTANDO


def test_adubacao_atividade_nao_reconhecida(svc, store, account, unit):
    _send(svc, "oi",  sid="SM001")
    _send(svc, "1",   sid="SM002")
    _send(svc, "1",   sid="SM003")
    _send(svc, "9",   sid="SM004")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO
    msgs = store.whatsapp_mensagens.list_by(sessao_id=sessao.id)
    outbound = [m for m in msgs if m.direcao == DirecaoMensagem.OUTBOUND]
    assert "Opção inválida" in outbound[-1].corpo


def test_adubacao_valor_invalido_pede_novamente(svc, store, account, unit):
    _send(svc, "oi",  sid="SM001")
    _send(svc, "1",   sid="SM002")
    _send(svc, "1",   sid="SM003")
    _send(svc, "1",   sid="SM004")
    _send(svc, "abc", sid="SM005")
    sessao = store.whatsapp_sessoes.list_all()[0]
    assert sessao.estado == EstadoAgente.PROCESSANDO
    assert sessao.contexto_json.get("passo") == "valor_gasto"


def test_adubacao_com_dois_talhoes_usa_selecionado(svc, store, account, two_units):
    u1, u2 = two_units
    _send(svc, "oi",  sid="SM001")
    _send(svc, "1",   sid="SM002")
    _send(svc, "1",   sid="SM003")
    _send(svc, "1",   sid="SM004")
    _send(svc, "200", sid="SM005")
    _send(svc, "sim", sid="SM006")
    ciclos = store.cycles.list_by(account_id=account.id, unit_id=u1.id)
    assert len(ciclos) == 1
    assert len(store.events.list_by(ciclo_id=ciclos[0].id)) == 1


# ── Segundo evento reutiliza ciclo aberto ─────────────────────────────────────

def test_segundo_registro_reutiliza_ciclo(svc, store, account, unit):
    _send(svc, "oi",  sid="SM001")
    _send(svc, "1",   sid="SM002")
    _send(svc, "1",   sid="SM003")
    _send(svc, "1",   sid="SM004")
    _send(svc, "150", sid="SM005")
    _send(svc, "sim", sid="SM006")
    _send(svc, "oi",  sid="SM007")
    _send(svc, "1",   sid="SM008")
    _send(svc, "2",   sid="SM009")
    _send(svc, "80",  sid="SM010")
    _send(svc, "sim", sid="SM011")
    assert len(store.cycles.list_all()) == 1
    assert len(store.events.list_all()) == 2
