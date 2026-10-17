FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD [".venv/bin/uvicorn", "local_rag_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
