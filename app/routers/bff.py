from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import TokenData, hash_password
from app.core.deps import get_token
from app.domains.registry import ALL_SETOR_OPTIONS, resolve_domain
from app.models.account import Account
from app.models.enums import RolePerfil, TipoAgente, TipoUnidade
from app.models.unit import Unit
from app.models.user import Profile, User
from app.repositories.store import Store, get_store

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
