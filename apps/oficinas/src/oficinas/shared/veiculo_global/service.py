import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.exceptions import NaoEncontrado
from oficinas.shared.veiculo_global.models import HistoricoVeiculo, Veiculo
from oficinas.shared.veiculo_global.schemas import (
    ConsultaVeiculoResponse,
    HistoricoCreate,
    VeiculoCreate,
)
from oficinas.shared.veiculo_global.sinesp import DadosSinesp, consultar_placa

log = structlog.get_logger()

# Colunas mutáveis — placa e criado_em nunca são atualizadas no upsert
_COLS_MUTAVEIS = ("chassi", "marca", "modelo", "ano_fab", "ano_mod", "cor", "tipo")


def _enriquecer_payload(payload: VeiculoCreate, sinesp: DadosSinesp) -> VeiculoCreate:
    """Preenche campos nulos do payload com dados do SINESP."""
    return VeiculoCreate(
        placa=payload.placa,
        chassi=payload.chassi or sinesp.chassi,
        marca=payload.marca or sinesp.marca,
        modelo=payload.modelo or sinesp.modelo,
        ano_fab=payload.ano_fab or sinesp.ano_fab,
        ano_mod=payload.ano_mod or sinesp.ano_mod,
        cor=payload.cor or sinesp.cor,
        tipo=payload.tipo,
    )


class VeiculoService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def consultar(self, placa: str) -> ConsultaVeiculoResponse:
        """
        Retorna dados do veículo para pré-preenchimento do formulário de cadastro.
        Prioridade: DB local → SINESP → não encontrado.
        Não persiste nada.
        """
        placa = placa.strip().upper()

        stmt = select(Veiculo).where(Veiculo.placa == placa)
        veiculo = (await self.db.execute(stmt)).scalar_one_or_none()
        if veiculo:
            return ConsultaVeiculoResponse(
                fonte="db",
                id=veiculo.id,
                placa=veiculo.placa,
                chassi=veiculo.chassi,
                marca=veiculo.marca,
                modelo=veiculo.modelo,
                ano_fab=veiculo.ano_fab,
                ano_mod=veiculo.ano_mod,
                cor=veiculo.cor,
                tipo=veiculo.tipo,
                criado_em=veiculo.criado_em,
            )

        sinesp = await consultar_placa(placa)
        if sinesp:
            log.info("sinesp_encontrado", placa=placa, marca=sinesp.marca)
            return ConsultaVeiculoResponse(
                fonte="sinesp",
                placa=placa,
                chassi=sinesp.chassi,
                marca=sinesp.marca,
                modelo=sinesp.modelo,
                ano_fab=sinesp.ano_fab,
                ano_mod=sinesp.ano_mod,
                cor=sinesp.cor,
                municipio=sinesp.municipio,
                uf=sinesp.uf,
                situacao=sinesp.situacao,
            )

        return ConsultaVeiculoResponse(fonte="nao_encontrado", placa=placa)

    async def upsert(self, payload: VeiculoCreate) -> Veiculo:
        """
        INSERT ... ON CONFLICT (placa) DO UPDATE.
        Preserva o valor existente quando o novo é NULL (enriquecimento progressivo).
        Enriquece campos nulos com dados do SINESP antes de persistir.
        """
        campos_vazios = not any([payload.chassi, payload.marca, payload.modelo,
                                  payload.ano_fab, payload.ano_mod, payload.cor])
        if campos_vazios:
            sinesp = await consultar_placa(payload.placa)
            if sinesp:
                payload = _enriquecer_payload(payload, sinesp)
                log.info("veiculo_enriquecido_sinesp", placa=payload.placa, marca=sinesp.marca)

        ins = pg_insert(Veiculo).values(
            placa=payload.placa,
            chassi=payload.chassi,
            marca=payload.marca,
            modelo=payload.modelo,
            ano_fab=payload.ano_fab,
            ano_mod=payload.ano_mod,
            cor=payload.cor,
            tipo=payload.tipo,
        )
        stmt = ins.on_conflict_do_update(
            index_elements=["placa"],
            set_={
                c: func.coalesce(getattr(ins.excluded, c), Veiculo.__table__.c[c])
                for c in _COLS_MUTAVEIS
            },
        ).returning(Veiculo)

        result = await self.db.execute(stmt)
        await self.db.commit()
        veiculo = result.scalar_one()
        log.info("veiculo_upsert", placa=veiculo.placa, veiculo_id=str(veiculo.id))
        return veiculo

    async def buscar_por_placa(self, placa: str) -> Veiculo:
        placa = placa.strip().upper()
        stmt = select(Veiculo).where(Veiculo.placa == placa)
        veiculo = (await self.db.execute(stmt)).scalar_one_or_none()
        if not veiculo:
            raise NaoEncontrado(f"Veículo com placa '{placa}' não encontrado")
        return veiculo

    async def historico_publico(self, veiculo_id: uuid.UUID) -> list[HistoricoVeiculo]:
        stmt = (
            select(HistoricoVeiculo)
            .where(
                HistoricoVeiculo.veiculo_id == veiculo_id,
                HistoricoVeiculo.resumo_publico.isnot(None),
            )
            .order_by(HistoricoVeiculo.data_servico.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def registrar_historico(self, payload: HistoricoCreate) -> HistoricoVeiculo:
        """Append-only — chamado pelo módulo de OS no fechamento. Nunca UPDATE/DELETE."""
        historico = HistoricoVeiculo(**payload.model_dump())
        self.db.add(historico)
        await self.db.commit()
        await self.db.refresh(historico)
        log.info(
            "historico_registrado",
            veiculo_id=str(payload.veiculo_id),
            tenant_id=str(payload.tenant_id),
            publico=payload.resumo_publico is not None,
        )
        return historico
