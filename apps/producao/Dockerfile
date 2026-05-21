FROM python:3.12-slim

WORKDIR /workspace

# Instalar uv
RUN pip install --no-cache-dir uv

# Copiar todo o workspace (root pyproject.toml + todos os packages)
COPY pyproject.toml .
COPY packages/ packages/
COPY apps/producao/ apps/producao/

# Instalar apenas o producao e suas dependências workspace
RUN uv sync --package producao --no-dev

WORKDIR /workspace/apps/producao

CMD ["uv", "run", "--package", "producao", \
     "uvicorn", "producao.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
