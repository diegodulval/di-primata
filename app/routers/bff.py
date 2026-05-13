from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import TokenData, hash_password
from app.core.deps import get_token
from app.domains.registry import ALL_SETOR_OPTIONS, resolve_domain
from app.models.account import Account
from app.models.cycle import Cycle
from app.models.enums import (
    OrigemCaptura,
    RolePerfil,
    StatusCiclo,
    TipoAgente,
    TipoEvento,
    TipoUnidade,
)
from app.models.event import Event
from app.models.unit import Unit
from app.models.user import Profile, User
from app.repositories.store import Store, get_store
from app.services.lot_service import LotService

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class UnitCreate(BaseModel):
    nome: str
    tipo: str = "TALHAO"
    area_capacidade: float | None = None


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    role: RolePerfil
    # Obrigatórios somente quando role == PRODUTOR
    nome_conta: str | None = None
    documento: str | None = None
    setor_primario: str | None = None
    whatsapp_phone: str | None = None
    unidades: list[UnitCreate] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/schema")
def get_schema(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    """Retorna o vocabulário do domínio da conta autenticada."""
    account = store.accounts.get(token.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account não encontrada")
    return resolve_domain(account.setor_primario)


@router.get("/setor-options")
def get_setor_options(_token: TokenData = Depends(get_token)):
    """Retorna todas as opções de setor_primario disponíveis."""
    return ALL_SETOR_OPTIONS


@router.get("/stats")
def get_stats(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    """Estatísticas operacionais do painel."""
    all_user_profiles: list[tuple] = []
    for account in store.accounts.list_all():
        for user in store.users.list_by(account_id=account.id):
            profile = store.profiles.find_one(user_id=user.id, account_id=account.id)
            all_user_profiles.append((user, profile))

    usuarios_ativos = sum(1 for u, _ in all_user_profiles if u.ativo)
    usuarios_portal = sum(
        1 for u, p in all_user_profiles
        if u.ativo and p and p.role == RolePerfil.PRODUTOR
    )

    today = datetime.now(UTC).date()
    mensagens_hoje = sum(
        1 for m in store.whatsapp_mensagens.list_all()
        if m.criado_em.date() == today
    )
    sessoes_wpp = len(store.whatsapp_sessoes.list_all())

    return {
        "usuarios_ativos": usuarios_ativos,
        "usuarios_portal": usuarios_portal,
        "sessoes_wpp": sessoes_wpp,
        "mensagens_hoje": mensagens_hoje,
    }


@router.get("/users")
def list_users(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    """Lista todos os usuários da plataforma com role e status de acesso ao portal."""
    result = []
    for account in store.accounts.list_all():
        for user in store.users.list_by(account_id=account.id):
            profile = store.profiles.find_one(user_id=user.id, account_id=account.id)
            result.append({
                "id": str(user.id),
                "nome": user.nome,
                "email": user.email,
                "ativo": user.ativo,
                "role": profile.role if profile else None,
                "portal_access": (profile.role == RolePerfil.PRODUTOR) if profile else False,
                "account_id": str(account.id),
                "account_nome": account.nome,
                "setor_primario": account.setor_primario,
                "whatsapp_phone": account.whatsapp_phone,
                "criado_em": user.criado_em.isoformat(),
            })
    return sorted(result, key=lambda r: r["criado_em"], reverse=True)


@router.post("/users", status_code=201)
def create_user(
    body: UsuarioCreate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    """
    Cria um usuário na plataforma.
    - PRODUTOR: recebe conta própria + acesso ao portal
    - Demais roles: adicionados à conta do admin autenticado
    """
    if store.users.find_one(email=body.email):
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    if body.role == RolePerfil.PRODUTOR:
        if not body.nome_conta or not body.documento or not body.setor_primario:
            raise HTTPException(
                status_code=422,
                detail="nome_conta, documento e setor_primario são obrigatórios para role PRODUTOR",
            )
        schema = resolve_domain(body.setor_primario)
        tipo_agente = (
            TipoAgente.PRODUTOR_RURAL if schema.domain == "rural" else TipoAgente.INDUSTRIAL
        )

        account = Account(
            nome=body.nome_conta,
            documento=body.documento,
            email=body.email,
            setor_primario=body.setor_primario,
            whatsapp_phone=body.whatsapp_phone,
        )
        store.accounts.save(account)

        user = User(
            account_id=account.id,
            nome=body.nome,
            email=body.email,
            tipo=tipo_agente,
            senha_hash=hash_password(body.senha),
        )
        store.users.save(user)

        profile = Profile(account_id=account.id, user_id=user.id, role=RolePerfil.PRODUTOR)
        store.profiles.save(profile)

        for u_data in body.unidades:
            unit = Unit(
                account_id=account.id,
                nome=u_data.nome,
                tipo=TipoUnidade(u_data.tipo),
                area_capacidade=u_data.area_capacidade,
                setor_template=body.setor_primario,
            )
            store.units.save(unit)

        return {
            "id": str(user.id),
            "nome": user.nome,
            "email": user.email,
            "role": RolePerfil.PRODUTOR,
            "portal_access": True,
            "account_id": str(account.id),
        }

    # Roles de plataforma (ADMIN, OPERADOR, CONSULTOR, CONSUMIDOR)
    admin_account = store.accounts.get(token.account_id)
    if not admin_account:
        raise HTTPException(status_code=404, detail="Account não encontrada")

    _TIPO_BY_ROLE = {
        RolePerfil.ADMIN: TipoAgente.ADMIN_PLATAFORMA,
        RolePerfil.OPERADOR: TipoAgente.OPERADOR,
        RolePerfil.CONSULTOR: TipoAgente.CONSULTOR_TECNICO,
        RolePerfil.CONSUMIDOR: TipoAgente.CONSUMIDOR,
    }

    user = User(
        account_id=token.account_id,
        nome=body.nome,
        email=body.email,
        tipo=_TIPO_BY_ROLE.get(body.role, TipoAgente.OPERADOR),
        senha_hash=hash_password(body.senha),
    )
    store.users.save(user)

    profile = Profile(account_id=token.account_id, user_id=user.id, role=body.role)
    store.profiles.save(profile)

    return {
        "id": str(user.id),
        "nome": user.nome,
        "email": user.email,
        "role": body.role,
        "portal_access": False,
        "account_id": str(token.account_id),
    }


# ── Portal do Produtor ────────────────────────────────────────────────────────

class AtividadeCreate(BaseModel):
    unit_id: UUID
    tipo_evento: TipoEvento
    descricao: str
    custo: float | None = None
    capturado_em: datetime = Field(default_factory=lambda: datetime.now(UTC))


def _open_or_create_cycle(account_id: UUID, unit: Unit, store: Store) -> Cycle:
    """Retorna o ciclo aberto da unidade ou cria um novo ciclo livre (sem protocolo)."""
    open_cycles = [
        c for c in store.cycles.list_by(unit_id=unit.id)
        if c.status in (StatusCiclo.ABERTO, StatusCiclo.EM_PRODUCAO)
    ]
    if open_cycles:
        return open_cycles[0]

    year = datetime.now(UTC).year
    unit_code = unit.nome[:3].upper()
    setor_code = unit.setor_template[:3].upper()
    seq_key = f"{setor_code}-{unit_code}-{year}"
    seq = store.next_lot_seq(seq_key)
    cycle = Cycle(
        account_id=account_id,
        unit_id=unit.id,
        protocol_id=None,
        codigo=f"{setor_code}-{unit_code}-{year}-{seq:04d}",
        produto="Registro Manual",
    )
    store.cycles.save(cycle)
    return cycle


@router.post("/portal/atividades", status_code=201)
def criar_atividade(
    body: AtividadeCreate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    """Registra uma atividade com custo no portal do produtor."""
    unit = store.units.get(body.unit_id)
    if not unit or unit.account_id != token.account_id:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    cycle = _open_or_create_cycle(token.account_id, unit, store)

    event = Event(
        ciclo_id=cycle.id,
        autor_user_id=token.user_id,
        tipo_evento=body.tipo_evento,
        descricao=body.descricao,
        custo=body.custo,
        origem=OrigemCaptura.MANUAL,
        capturado_em=body.capturado_em,
    )
    store.events.save(event)

    return {
        "id": str(event.id),
        "tipo_evento": event.tipo_evento,
        "descricao": event.descricao,
        "custo": event.custo,
        "capturado_em": event.capturado_em.isoformat(),
        "unit_id": str(unit.id),
        "unit_nome": unit.nome,
    }


@router.get("/portal/atividades")
def listar_atividades(
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    """Lista todas as atividades do produtor autenticado, mais recentes primeiro."""
    cycles = store.cycles.list_by(account_id=token.account_id)
    cycle_ids = {c.id for c in cycles}
    unit_map = {u.id: u for u in store.units.list_by(account_id=token.account_id)}
    cycle_unit_map = {c.id: c.unit_id for c in cycles}

    result = []
    for event in store.events.list_all():
        if event.ciclo_id not in cycle_ids:
            continue
        unit_id = cycle_unit_map.get(event.ciclo_id)
        unit = unit_map.get(unit_id) if unit_id else None
        result.append({
            "id": str(event.id),
            "tipo_evento": event.tipo_evento,
            "descricao": event.descricao,
            "custo": event.custo,
            "capturado_em": event.capturado_em.isoformat(),
            "unit_id": str(unit_id) if unit_id else None,
            "unit_nome": unit.nome if unit else "—",
        })

    return sorted(result, key=lambda e: e["capturado_em"], reverse=True)


@router.get("/portal/resumo")
def resumo_produtor(
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    """Totais financeiros e contagem de atividades por unidade."""
    cycles = store.cycles.list_by(account_id=token.account_id)
    cycle_ids = {c.id for c in cycles}
    unit_map = {u.id: u for u in store.units.list_by(account_id=token.account_id)}
    cycle_unit_map = {c.id: c.unit_id for c in cycles}

    total_custo = 0.0
    total_atividades = 0
    por_unidade: dict[str, dict] = {}

    for event in store.events.list_all():
        if event.ciclo_id not in cycle_ids:
            continue
        total_atividades += 1
        custo = event.custo or 0.0
        total_custo += custo

        unit_id = cycle_unit_map.get(event.ciclo_id)
        if unit_id:
            key = str(unit_id)
            unit = unit_map.get(unit_id)
            if key not in por_unidade:
                por_unidade[key] = {
                    "unit_id": key,
                    "unit_nome": unit.nome if unit else "—",
                    "custo": 0.0,
                    "atividades": 0,
                }
            por_unidade[key]["custo"] += custo
            por_unidade[key]["atividades"] += 1

    return {
        "total_custo": total_custo,
        "total_atividades": total_atividades,
        "por_unidade": list(por_unidade.values()),
    }


class LotePortalCreate(BaseModel):
    unit_id: UUID
    autodeclarado: bool = False


@router.post("/portal/lotes", status_code=201)
def gerar_lote_portal(
    body: LotePortalCreate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    """
    Fecha todos os ciclos abertos de uma unidade e gera o lote com QR code.
    Fluxo: ABERTO/EM_PRODUCAO → ENCERRADO → VALIDANDO → gerar → publicar.
    """
    unit = store.units.get(body.unit_id)
    if not unit or unit.account_id != token.account_id:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    open_cycles = [
        c for c in store.cycles.list_by(unit_id=body.unit_id)
        if c.status in (StatusCiclo.ABERTO, StatusCiclo.EM_PRODUCAO)
    ]
    if not open_cycles:
        raise HTTPException(status_code=422, detail="Nenhum ciclo aberto para esta unidade")

    svc = LotService(store)
    lotes = []

    for cycle in open_cycles:
        events = store.events.list_by(ciclo_id=cycle.id)
        if not events:
            continue

        # Transições de estado até VALIDANDO
        _TRANSITIONS = [StatusCiclo.EM_PRODUCAO, StatusCiclo.ENCERRADO, StatusCiclo.VALIDANDO]
        for status in _TRANSITIONS:
            if cycle.status != status:
                cycle.status = status
                if status == StatusCiclo.ENCERRADO:
                    cycle.encerrado_em = datetime.now(UTC)
                store.cycles.save(cycle)

        lot = svc.generate(cycle.id, token.user_id, autodeclarado=body.autodeclarado)
        svc.publish(lot.id, token.user_id)

        qr_asset = next((a for a in lot.assets if a.tipo.value == "QR_PNG"), None)
        lotes.append({
            "lot_id": str(lot.id),
            "codigo_lote": lot.codigo_lote,
            "qr_hash": lot.qr_hash,
            "qr_image": qr_asset.url if qr_asset else None,
            "gerado_em": lot.gerado_em.isoformat(),
            "unit_id": str(unit.id),
            "unit_nome": unit.nome,
            "autodeclarado": body.autodeclarado,
            "total_atividades": lot.snapshot_json.get("total_atividades", 0),
            "total_custo": lot.snapshot_json.get("total_custo", 0.0),
        })

    if not lotes:
        raise HTTPException(
            status_code=422,
            detail="Nenhum ciclo com atividades registradas para gerar lote",
        )

    return lotes[0] if len(lotes) == 1 else lotes


@router.get("/portal/lotes")
def listar_lotes_portal(
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    """Lista todos os lotes gerados pelo produtor autenticado."""
    cycles = store.cycles.list_by(account_id=token.account_id)
    cycle_ids = {c.id for c in cycles}
    unit_map = {u.id: u for u in store.units.list_by(account_id=token.account_id)}
    cycle_unit_map = {c.id: c.unit_id for c in cycles}

    result = []
    for lot in store.lots.list_all():
        if lot.ciclo_id not in cycle_ids:
            continue
        unit_id = cycle_unit_map.get(lot.ciclo_id)
        unit = unit_map.get(unit_id) if unit_id else None
        qr_asset = next((a for a in lot.assets if a.tipo.value == "QR_PNG"), None)
        result.append({
            "lot_id": str(lot.id),
            "codigo_lote": lot.codigo_lote,
            "qr_hash": lot.qr_hash,
            "qr_image": qr_asset.url if qr_asset else None,
            "status": lot.status,
            "unit_id": str(unit_id) if unit_id else None,
            "unit_nome": unit.nome if unit else "—",
            "gerado_em": lot.gerado_em.isoformat(),
            "autodeclarado": lot.snapshot_json.get("autodeclarado", False),
            "total_atividades": lot.snapshot_json.get("total_atividades", 0),
            "total_custo": lot.snapshot_json.get("total_custo", 0.0),
        })

    return sorted(result, key=lambda r: r["gerado_em"], reverse=True)
