# Stage 1: Install GCC for numpy
FROM python:3.14-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential


# Stage 2: Base image with uv installer
FROM build AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /backend


FROM base AS python-deps

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./

# Install deps.
RUN uv sync --frozen --no-cache


FROM python-deps AS sources

# Copy project sources
COPY . .


# Stage 3: Development image
FROM sources AS dev
CMD ["uv", "run" ,"uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Stage 4: Production image
FROM sources AS prod
CMD ["uv", "run" ,"uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
