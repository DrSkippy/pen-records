FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY alembic.ini ./
COPY migrations ./migrations
COPY pen_records ./pen_records
RUN uv sync --frozen --no-dev
CMD ["sh", "-c", "uv run alembic upgrade head && exec uv run uvicorn pen_records.main:app --host 0.0.0.0 --port 8000"]
