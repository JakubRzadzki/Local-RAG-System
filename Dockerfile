FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv \
    && useradd --create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev \
    && chown -R app:app /app

# The application does not need root: drop privileges for everything that runs.
USER app

EXPOSE 8000
CMD [".venv/bin/uvicorn", "local_rag_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
