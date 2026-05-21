import pytest
from fastapi import HTTPException

from core.models.cycle import CycleCreate
from core.models.enums import OrigemCaptura, StatusCiclo, StatusValidacao, TipoEvento
from core.models.event import EventCreate
from producao.services.cycle_service import CycleService


def _create_cycle(store, seeded) -> tuple:
    svc = CycleService(store)
    data = CycleCreate(
        unit_id=seeded["unit"].id,
        protocol_id=seeded["protocol"].id,
        produto="Café Especial",
    )
    cycle = svc.create(seeded["account"].id, data, seeded["user"].id)
    return svc, cycle


def _make_event(step_id):
    return EventCreate(
        etapa_protocolo_id=step_id,
        tipo_evento=TipoEvento.COLHEITA,
        descricao="Colheita realizada",
        origem=OrigemCaptura.MANUAL,
    )


# ── criação ────────────────────────────────────────────────────────────────────

def test_create_gera_codigo_formatado(store, seeded):
    _, cycle = _create_cycle(store, seeded)
    parts = cycle.codigo.split("-")
    assert len(parts) == 4
    assert parts[2].isdigit()


def test_create_status_inicial_aberto(store, seeded):
    _, cycle = _create_cycle(store, seeded)
    assert cycle.status == StatusCiclo.ABERTO


def test_create_unidade_nao_encontrada_levanta_404(store, seeded):
    from uuid import uuid4
    svc = CycleService(store)
    data = CycleCreate(unit_id=uuid4(), protocol_id=seeded["protocol"].id, produto="X")
    with pytest.raises(HTTPException) as exc:
        svc.create(seeded["account"].id, data, seeded["user"].id)
    assert exc.value.status_code == 404


def test_create_protocolo_inativo_levanta_404(store, seeded):
    seeded["protocol"].ativo = False
    store.protocols.save(seeded["protocol"])
    svc = CycleService(store)
    data = CycleCreate(
        unit_id=seeded["unit"].id, protocol_id=seeded["protocol"].id, produto="X"
    )
    with pytest.raises(HTTPException) as exc:
        svc.create(seeded["account"].id, data, seeded["user"].id)
    assert exc.value.status_code == 404


# ── máquina de estados ─────────────────────────────────────────────────────────

def test_transicao_valida_aberto_para_em_producao(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    updated = svc.transition(cycle.id, StatusCiclo.EM_PRODUCAO, seeded["user"].id)
    assert updated.status == StatusCiclo.EM_PRODUCAO


def test_transicao_invalida_levanta_422(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    with pytest.raises(HTTPException) as exc:
        svc.transition(cycle.id, StatusCiclo.ARQUIVADO, seeded["user"].id)
    assert exc.value.status_code == 422


def test_transicao_encerrado_define_encerrado_em(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    svc.transition(cycle.id, StatusCiclo.EM_PRODUCAO, seeded["user"].id)
    updated = svc.transition(cycle.id, StatusCiclo.ENCERRADO, seeded["user"].id)
    assert updated.encerrado_em is not None


def test_transicao_lote_gerado_sem_etapas_levanta_422(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    for s in [StatusCiclo.EM_PRODUCAO, StatusCiclo.ENCERRADO, StatusCiclo.VALIDANDO]:
        svc.transition(cycle.id, s, seeded["user"].id)
    with pytest.raises(HTTPException) as exc:
        svc.transition(cycle.id, StatusCiclo.LOTE_GERADO, seeded["user"].id)
    assert exc.value.status_code == 422


# ── eventos ────────────────────────────────────────────────────────────────────

def test_add_event_em_ciclo_aberto(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    event = svc.add_event(cycle.id, _make_event(seeded["step"].id), seeded["user"].id)
    assert event.ciclo_id == cycle.id
    assert event.status_validacao == StatusValidacao.PENDENTE


def test_add_event_em_ciclo_encerrado_levanta_422(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    for s in [StatusCiclo.EM_PRODUCAO, StatusCiclo.ENCERRADO]:
        svc.transition(cycle.id, s, seeded["user"].id)
    with pytest.raises(HTTPException) as exc:
        svc.add_event(cycle.id, _make_event(seeded["step"].id), seeded["user"].id)
    assert exc.value.status_code == 422


def test_aditamento_marca_original_como_aditado(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    original = svc.add_event(cycle.id, _make_event(seeded["step"].id), seeded["user"].id)

    adit = EventCreate(
        etapa_protocolo_id=seeded["step"].id,
        tipo_evento=TipoEvento.COLHEITA,
        descricao="Correção",
        origem=OrigemCaptura.MANUAL,
        aditamento_de_id=original.id,
    )
    svc.add_event(cycle.id, adit, seeded["user"].id)

    updated = store.events.get(original.id)
    assert updated.status_validacao == StatusValidacao.ADITADO


# ── etapas faltantes ──────────────────────────────────────────────────────────

def test_missing_steps_sem_eventos(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    missing = svc.missing_steps(cycle.id)
    assert seeded["step"].id in missing


def test_missing_steps_zerado_apos_cobertura(store, seeded):
    svc, cycle = _create_cycle(store, seeded)
    event = svc.add_event(cycle.id, _make_event(seeded["step"].id), seeded["user"].id)
    event.status_validacao = StatusValidacao.VALIDADO
    store.events.save(event)
    assert svc.missing_steps(cycle.id) == []
