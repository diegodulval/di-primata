from fastapi import APIRouter, Depends, Request

from producao.repositories.store import Store, get_store
from producao.services.lot_service import LotService

router = APIRouter()


@router.get("/{qr_hash}")
def public_view(qr_hash: str, request: Request, store: Store = Depends(get_store)):
    svc = LotService(store)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return svc.get_public_view(qr_hash, ip, ua)
