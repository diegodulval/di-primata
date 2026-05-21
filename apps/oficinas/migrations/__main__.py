"""
Runner de migrations — executa em ordem, idempotente.
Uso: python -m migrations               (aplica todos os pendentes)
     python -m migrations --dry-run     (lista o que seria aplicado)
     python -m migrations --status      (mostra o que já foi aplicado)

Requer DATABASE_URL no ambiente. Não roda no startup do app (Fator XII).
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg

MIGRATIONS_DIR = Path(__file__).parent
_SQL_FILES = sorted(
    f for f in MIGRATIONS_DIR.glob("*.sql")
    if not f.name.startswith("_")
)

_TRACKING_TABLE = "_schema_migrations"

_CREATE_TRACKING = f"""
CREATE TABLE IF NOT EXISTS {_TRACKING_TABLE} (
    filename    TEXT PRIMARY KEY,
    aplicado_em TIMESTAMPTZ DEFAULT now()
)
"""


async def _connect() -> asyncpg.Connection:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERRO: variável DATABASE_URL não definida.", file=sys.stderr)
        sys.exit(1)
    # asyncpg usa postgresql://, não postgresql+asyncpg://
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(url)


async def _aplicados(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch(f"SELECT filename FROM {_TRACKING_TABLE}")
    return {row["filename"] for row in rows}


async def cmd_status(conn: asyncpg.Connection) -> None:
    await conn.execute(_CREATE_TRACKING)
    aplicados = await _aplicados(conn)
    print(f"{'arquivo':<35} {'status'}")
    print("-" * 50)
    for f in _SQL_FILES:
        status = "aplicado" if f.name in aplicados else "PENDENTE"
        print(f"{f.name:<35} {status}")


async def cmd_apply(conn: asyncpg.Connection, dry_run: bool) -> None:
    await conn.execute(_CREATE_TRACKING)
    aplicados = await _aplicados(conn)

    pendentes = [f for f in _SQL_FILES if f.name not in aplicados]
    if not pendentes:
        print("Nenhuma migration pendente.")
        return

    for sql_file in pendentes:
        if dry_run:
            print(f"[dry-run] {sql_file.name}")
            continue

        sql = sql_file.read_text(encoding="utf-8")
        print(f"Aplicando {sql_file.name} ...", end=" ", flush=True)
        try:
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    f"INSERT INTO {_TRACKING_TABLE} (filename) VALUES ($1)",
                    sql_file.name,
                )
            print("ok")
        except Exception as exc:
            print(f"ERRO\n{exc}", file=sys.stderr)
            sys.exit(1)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Runner de migrations — DiAuto")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true",
                       help="Lista migrações pendentes sem aplicar")
    group.add_argument("--status", action="store_true",
                       help="Mostra o status de cada arquivo")
    args = parser.parse_args()

    conn = await _connect()
    try:
        if args.status:
            await cmd_status(conn)
        else:
            await cmd_apply(conn, dry_run=args.dry_run)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
