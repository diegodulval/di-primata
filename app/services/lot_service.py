import base64
import hashlib
import io
import secrets
from uuid import UUID

from fastapi import HTTPException

import qrcode

from app.models.audit import AuditLog
from app.models.enums import StatusCiclo, StatusLote, StatusValidacao, TipoAsset
from app.models.lot import Lot, LotAsset, QrAccess
from app.repositories.store import Store


class LotService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def generate(self, cycle_id: UUID, actor_id: UUID) -> Lot:
        cycle = self.store.cycles.get(cycle_id)
        if not cycle:
            raise HTTPException(status_code=404, detail="Ciclo não encontrado")
        if cycle.status != StatusCiclo.VALIDANDO:
            raise HTTPException(status_code=422, detail="Ciclo precisa estar em VALIDANDO para gerar lote")
        if self.store.lots.find_one(ciclo_id=cycle_id):
            raise HTTPException(status_code=409, detail="Lote já gerado para este ciclo")

        protocol = self.store.protocols.get(cycle.protocol_id)
        events = self.store.events.list_by(ciclo_id=cycle_id)

        # RN-01: todas as etapas obrigatórias precisam estar cobertas
        if protocol and protocol.etapas_obrig_ids:
            covered = {e.etapa_protocolo_id for e in events if e.status_validacao != StatusValidacao.INVALIDO}
            missing = [sid for sid in protocol.etapas_obrig_ids if sid not in covered]
            if missing:
                raise HTTPException(
                    status_code=422,
                    detail=f"Etapas obrigatórias pendentes: {[str(s) for s in missing]}",
                )
        unit = self.store.units.get(cycle.unit_id)

        qr_hash = self._make_qr_hash(cycle.codigo)
        snapshot = self._build_snapshot(cycle, events, unit, protocol)

        lot = Lot(
            ciclo_id=cycle_id,
            codigo_lote=cycle.codigo,
            qr_hash=qr_hash,
            snapshot_json=snapshot,
        )
        self.store.lots.save(lot)

        qr_asset = self._generate_qr_asset(lot)
        self.store.lot_assets.save(qr_asset)
        lot.assets.append(qr_asset)

        cycle.status = StatusCiclo.LOTE_GERADO
        self.store.cycles.save(cycle)

        self._audit(lot.id, "Lot", actor_id, "GERAR_LOTE", None, lot.model_dump())
        return lot

    def publish(self, lot_id: UUID, actor_id: UUID) -> Lot:
        lot = self._get_or_404(lot_id)
        if lot.status != StatusLote.GERADO:
            raise HTTPException(status_code=422, detail="Lote não está em estado GERADO")
        lot.status = StatusLote.PUBLICADO
        lot.publico = True
        self.store.lots.save(lot)
        self._audit(lot.id, "Lot", actor_id, "PUBLICAR_LOTE", None, lot.model_dump())
        return lot

    def get_public_view(self, qr_hash: str, ip: str | None, user_agent: str | None) -> dict:
        lot = self.store.lots.find_one(qr_hash=qr_hash)
        if not lot or not lot.publico:
            raise HTTPException(status_code=404, detail="Lote não encontrado")

        access = QrAccess(lot_id=lot.id, ip_origem=ip, user_agent=user_agent)
        self.store.qr_accesses.save(access)

        return lot.snapshot_json

    def _make_qr_hash(self, codigo_lote: str) -> str:
        raw = f"{codigo_lote}{secrets.token_hex(8)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _build_snapshot(self, cycle, events, unit, protocol) -> dict:
        public_events = [
            {k: v for k, v in e.model_dump().items() if k not in ("attachments",)}
            for e in events
            if e.visivel_publico
        ]
        return {
            "codigo_lote": cycle.codigo,
            "produto": cycle.produto,
            "iniciado_em": cycle.iniciado_em.isoformat(),
            "encerrado_em": cycle.encerrado_em.isoformat() if cycle.encerrado_em else None,
            "unidade": unit.model_dump() if unit else None,
            "protocolo": {"nome": protocol.nome, "versao": protocol.versao, "ref_normativa": protocol.ref_normativa} if protocol else None,
            "eventos": public_events,
            "meta": cycle.meta_json,
        }

    def _generate_qr_asset(self, lot: Lot) -> LotAsset:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(f"/p/{lot.qr_hash}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return LotAsset(
            lot_id=lot.id,
            tipo=TipoAsset.QR_PNG,
            url=f"data:image/png;base64,{b64}",
        )

    def _get_or_404(self, lot_id: UUID) -> Lot:
        lot = self.store.lots.get(lot_id)
        if not lot:
            raise HTTPException(status_code=404, detail="Lote não encontrado")
        return lot

    def _audit(self, entity_id, entity_tipo, actor_id, acao, before, after) -> None:
        self.store.audit_logs.save(AuditLog(
            entidade_id=entity_id,
            entidade_tipo=entity_tipo,
            ator_id=actor_id,
            acao=acao,
            dados_antes=before,
            dados_depois=after,
        ))
