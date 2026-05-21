FROM python:3.12-slim

WORKDIR /workspace

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY packages/ packages/
COPY apps/oficinas/ apps/oficinas/

RUN uv sync --package oficinas --no-dev

WORKDIR /workspace/apps/oficinas

CMD ["uv", "run", "--package", "oficinas", \
     "uvicorn", "oficinas.main:app", \
     "--host", "0.0.0.0", "--port", "8001"]
