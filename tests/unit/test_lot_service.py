import pytest
from fastapi import HTTPException

from app.models.cycle import CycleCreate
from app.models.enums import OrigemCaptura, StatusCiclo, StatusLote, StatusValidacao, TipoEvento
from app.models.event import EventCreate
from app.services.cycle_service import CycleService
from app.services.lot_service import LotService


def _advance_to_validando(store, seeded) -> tuple:
    """Cria ciclo, adiciona evento cobrindo etapa obrigatória, avança até VALIDANDO."""
    cs = CycleService(store)
    cycle = cs.create(
        seeded["account"].id,
        CycleCreate(unit_id=seeded["unit"].id, protocol_id=seeded["protocol"].id, produto="Café"),
        seeded["user"].id,
    )
    event = cs.add_event(
        cycle.id,
        EventCreate(
            etapa_protocolo_id=seeded["step"].id,
            tipo_evento=TipoEvento.COLHEITA,
            descricao="OK",
            origem=OrigemCaptura.MANUAL,
        ),
        seeded["user"].id,
    )
    event.status_validacao = StatusValidacao.VALIDADO
    store.events.save(event)

    for status in [StatusCiclo.EM_PRODUCAO, StatusCiclo.ENCERRADO, StatusCiclo.VALIDANDO]:
        cs.transition(cycle.id, status, seeded["user"].id)

    return cs, cycle


# ── geração de lote ───────────────────────────────────────────────────────────

def test_generate_cria_lote_com_qr(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    ls = LotService(store)
    lot = ls.generate(cycle.id, seeded["user"].id)

    assert lot.ciclo_id == cycle.id
    assert lot.codigo_lote == cycle.codigo
    assert lot.qr_hash and len(lot.qr_hash) == 32
    assert len(lot.assets) == 1
    assert lot.assets[0].url.startswith("data:image/png;base64,")


def test_generate_atualiza_status_ciclo(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    LotService(store).generate(cycle.id, seeded["user"].id)
    assert store.cycles.get(cycle.id).status == StatusCiclo.LOTE_GERADO


def test_generate_status_errado_levanta_422(store, seeded):
    cs = CycleService(store)
    cycle = cs.create(
        seeded["account"].id,
        CycleCreate(unit_id=seeded["unit"].id, protocol_id=seeded["protocol"].id, produto="X"),
        seeded["user"].id,
    )
    with pytest.raises(HTTPException) as exc:
        LotService(store).generate(cycle.id, seeded["user"].id)
    assert exc.value.status_code == 422


def test_generate_duplicado_levanta_409(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    ls = LotService(store)
    ls.generate(cycle.id, seeded["user"].id)

    # Força status VALIDANDO novamente para tentar segunda geração
    cycle.status = StatusCiclo.VALIDANDO
    store.cycles.save(cycle)

    with pytest.raises(HTTPException) as exc:
        ls.generate(cycle.id, seeded["user"].id)
    assert exc.value.status_code == 409


def test_generate_etapa_nao_coberta_levanta_422(store, seeded):
    cs = CycleService(store)
    cycle = cs.create(
        seeded["account"].id,
        CycleCreate(unit_id=seeded["unit"].id, protocol_id=seeded["protocol"].id, produto="X"),
        seeded["user"].id,
    )
    for s in [StatusCiclo.EM_PRODUCAO, StatusCiclo.ENCERRADO, StatusCiclo.VALIDANDO]:
        cs.transition(cycle.id, s, seeded["user"].id)

    with pytest.raises(HTTPException) as exc:
        LotService(store).generate(cycle.id, seeded["user"].id)
    assert exc.value.status_code == 422


# ── publicação ────────────────────────────────────────────────────────────────

def test_publish_muda_status_e_torna_publico(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    ls = LotService(store)
    lot = ls.generate(cycle.id, seeded["user"].id)
    published = ls.publish(lot.id, seeded["user"].id)

    assert published.status == StatusLote.PUBLICADO
    assert published.publico is True


def test_publish_lote_nao_gerado_levanta_422(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    ls = LotService(store)
    lot = ls.generate(cycle.id, seeded["user"].id)
    lot.status = StatusLote.SUSPENSO
    store.lots.save(lot)

    with pytest.raises(HTTPException) as exc:
        ls.publish(lot.id, seeded["user"].id)
    assert exc.value.status_code == 422


# ── portal público ────────────────────────────────────────────────────────────

def test_public_view_retorna_snapshot(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    ls = LotService(store)
    lot = ls.generate(cycle.id, seeded["user"].id)
    ls.publish(lot.id, seeded["user"].id)

    view = ls.get_public_view(lot.qr_hash, "1.2.3.4", "TestAgent/1.0")
    assert view["codigo_lote"] == cycle.codigo
    assert view["produto"] == "Café"


def test_public_view_registra_acesso(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    ls = LotService(store)
    lot = ls.generate(cycle.id, seeded["user"].id)
    ls.publish(lot.id, seeded["user"].id)
    ls.get_public_view(lot.qr_hash, "1.2.3.4", "UA")

    accesses = store.qr_accesses.list_by(lot_id=lot.id)
    assert len(accesses) == 1
    assert accesses[0].ip_origem == "1.2.3.4"


def test_public_view_lote_nao_publicado_levanta_404(store, seeded):
    _, cycle = _advance_to_validando(store, seeded)
    ls = LotService(store)
    lot = ls.generate(cycle.id, seeded["user"].id)

    with pytest.raises(HTTPException) as exc:
        ls.get_public_view(lot.qr_hash, None, None)
    assert exc.value.status_code == 404
