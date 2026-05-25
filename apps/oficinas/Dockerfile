FROM python:3.12-slim

WORKDIR /workspace

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY apps/oficinas/ apps/oficinas/
# uv precisa enxergar todos os membros do workspace para resolver o grafo
COPY apps/producao/pyproject.toml apps/producao/pyproject.toml

RUN uv sync --package oficinas --no-dev

CMD ["uv", "run", "--package", "oficinas", \
     "uvicorn", "oficinas.main:app", \
     "--host", "0.0.0.0", "--port", "8001"]
