from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

from core.models.audit import AuditLog
from core.models.cycle import Cycle, CycleCreate
from core.models.enums import StatusCiclo, StatusValidacao
from core.models.event import Event, EventCreate
from producao.repositories.store import Store

VALID_TRANSITIONS: dict[StatusCiclo, list[StatusCiclo]] = {
    StatusCiclo.ABERTO:      [StatusCiclo.EM_PRODUCAO],
    StatusCiclo.EM_PRODUCAO: [StatusCiclo.ENCERRADO],
    StatusCiclo.ENCERRADO:   [StatusCiclo.VALIDANDO],
    StatusCiclo.VALIDANDO:   [StatusCiclo.LOTE_GERADO],
    StatusCiclo.LOTE_GERADO: [StatusCiclo.ARQUIVADO],
    StatusCiclo.ARQUIVADO:   [],
}


class CycleService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def create(self, account_id: UUID, data: CycleCreate, actor_id: UUID) -> Cycle:
        unit = self.store.units.get(data.unit_id)
        if not unit or unit.account_id != account_id:
            raise HTTPException(status_code=404, detail="Unidade não encontrada")

        protocol = self.store.protocols.get(data.protocol_id)
        if not protocol or not protocol.ativo:
            raise HTTPException(status_code=404, detail="Protocolo não encontrado")

        year = datetime.now(timezone.utc).year
        unit_code = unit.nome[:3].upper()
        setor_code = unit.setor_template[:3].upper()
        seq_key = f"{setor_code}-{unit_code}-{year}"
        seq = self.store.next_lot_seq(seq_key)
        codigo = f"{setor_code}-{unit_code}-{year}-{seq:04d}"

        cycle = Cycle(
            account_id=account_id,
            unit_id=data.unit_id,
            protocol_id=data.protocol_id,
            codigo=codigo,
            produto=data.produto,
            insumos_json=data.insumos_json,
            meta_json=data.meta_json,
        )
        self.store.cycles.save(cycle)
        self._audit(cycle.id, "Cycle", actor_id, "CREATE", None, cycle.model_dump())
        return cycle

    def transition(self, cycle_id: UUID, new_status: StatusCiclo, actor_id: UUID) -> Cycle:
        cycle = self._get_or_404(cycle_id)

        allowed = VALID_TRANSITIONS.get(cycle.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Transição inválida: {cycle.status} → {new_status}",
            )

        if new_status == StatusCiclo.LOTE_GERADO:
            missing = self._missing_steps(cycle)
            if missing:
                raise HTTPException(
                    status_code=422,
                    detail=f"Etapas obrigatórias pendentes: {[str(s) for s in missing]}",
                )

        before = cycle.model_dump()
        cycle.status = new_status
        if new_status == StatusCiclo.ENCERRADO:
            cycle.encerrado_em = datetime.now(timezone.utc)

        self.store.cycles.save(cycle)
        self._audit(cycle.id, "Cycle", actor_id, "STATUS_CHANGE", before, cycle.model_dump())
        return cycle

    def add_event(self, cycle_id: UUID, data: EventCreate, author_id: UUID) -> Event:
        cycle = self._get_or_404(cycle_id)

        if cycle.status not in (StatusCiclo.ABERTO, StatusCiclo.EM_PRODUCAO):
            raise HTTPException(status_code=422, detail="Ciclo não aceita novos eventos neste estado")

        if data.aditamento_de_id:
            original = self.store.events.get(data.aditamento_de_id)
            if not original or original.ciclo_id != cycle_id:
                raise HTTPException(status_code=404, detail="Evento original não encontrado")
            original.status_validacao = StatusValidacao.ADITADO
            self.store.events.save(original)

        event = Event(
            ciclo_id=cycle_id,
            autor_user_id=author_id,
            **data.model_dump(),
        )
        self.store.events.save(event)
        return event

    def get_events(self, cycle_id: UUID) -> list[Event]:
        self._get_or_404(cycle_id)
        return self.store.events.list_by(ciclo_id=cycle_id)

    def missing_steps(self, cycle_id: UUID) -> list[UUID]:
        cycle = self._get_or_404(cycle_id)
        return self._missing_steps(cycle)

    def _missing_steps(self, cycle: Cycle) -> list[UUID]:
        protocol = self.store.protocols.get(cycle.protocol_id)
        if not protocol:
            return []
        events = self.store.events.list_by(ciclo_id=cycle.id)
        covered = {e.etapa_protocolo_id for e in events if e.status_validacao != StatusValidacao.INVALIDO}
        return [sid for sid in protocol.etapas_obrig_ids if sid not in covered]

    def _get_or_404(self, cycle_id: UUID) -> Cycle:
        cycle = self.store.cycles.get(cycle_id)
        if not cycle:
            raise HTTPException(status_code=404, detail="Ciclo não encontrado")
        return cycle

    def _audit(self, entity_id, entity_tipo, actor_id, acao, before, after) -> None:
        log = AuditLog(
            entidade_id=entity_id,
            entidade_tipo=entity_tipo,
            ator_id=actor_id,
            acao=acao,
            dados_antes=before,
            dados_depois=after,
        )
        self.store.audit_logs.save(log)
