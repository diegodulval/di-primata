from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, accounts, units, cycles, events, lots, public

app = FastAPI(
    title="Di Mata",
    version="0.1.0",
    description="Plataforma de rastreabilidade de cadeia produtiva",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/auth",    tags=["auth"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(units.router,    prefix="/units",   tags=["units"])
app.include_router(cycles.router,   prefix="/cycles",  tags=["cycles"])
app.include_router(events.router,   prefix="/cycles",  tags=["events"])
app.include_router(lots.router,     prefix="/cycles",  tags=["lots"])
app.include_router(public.router,   prefix="/p",       tags=["public"])


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/hello", tags=["infra"])
def hello():
    return {"message": "Hello, World!", "service": "Di Mata", "timestamp": "2026-05-03"}
