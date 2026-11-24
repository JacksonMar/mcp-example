# uv + Python as in .python-version; uv version as in the local uv that wrote uv.lock.
FROM ghcr.io/astral-sh/uv:0.13.9-python3.15-trixie-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    COLUMNS=160

# 1. Dependencies only (cached layer: rebuilds only when pyproject.toml / uv.lock change).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. The project itself (README.md is needed: pyproject.toml references it).
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 1000 app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["python", "-m", "qauto_mcp"]
