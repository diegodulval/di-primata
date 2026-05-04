from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import TokenData
from app.core.deps import get_token
from app.models.protocol import Protocol, ProtocolCreate
from app.models.unit import Unit, UnitCreate
from app.repositories.store import Store, get_store

router = APIRouter()


@router.post("", response_model=Unit, status_code=201)
def create_unit(
    body: UnitCreate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    unit = Unit(account_id=token.account_id, **body.model_dump())
    return store.units.save(unit)


@router.get("", response_model=list[Unit])
def list_units(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    return store.units.list_by(account_id=token.account_id)


@router.get("/{unit_id}", response_model=Unit)
def get_unit(unit_id: UUID, token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    unit = store.units.get(unit_id)
    if not unit or unit.account_id != token.account_id:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    return unit


@router.post("/protocols", response_model=Protocol, status_code=201)
def create_protocol(
    body: ProtocolCreate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    protocol = Protocol(**body.model_dump())
    return store.protocols.save(protocol)


@router.get("/protocols", response_model=list[Protocol])
def list_protocols(
    setor: str | None = None,
    store: Store = Depends(get_store),
):
    if setor:
        return store.protocols.list_by(setor_template=setor)
    return store.protocols.list_all()
