# Stage 1: Base image with uv installer
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /backend

# Copy uv from the official image (efficient and standard)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Stage 2: Install python dependencies
FROM base AS python-deps
COPY pyproject.toml uv.lock ./

# --frozen ensures we use the lockfile exactly
# --no-cache keeps the image small
RUN uv sync --frozen --no-cache


# Stage 3: Copy project sources
FROM python-deps AS sources
COPY . .


# Stage 4: Development image
FROM sources AS dev
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Stage 5: Production image
FROM sources AS prod
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
