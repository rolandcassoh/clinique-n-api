FROM python:3.12.8-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-interaction --no-ansi

COPY . .

# ------- development -------
FROM base AS development
RUN poetry install --no-interaction --no-ansi
# weasyprint 62.3 is incompatible with pydyf>=0.11 (AttributeError: 'super'
# object has no attribute 'transform' in weasyprint/pdf/stream.py). There is
# no poetry.lock in this project, so poetry re-resolves on every install and
# the `pydyf = "0.10.0"` pin in pyproject.toml does not reliably survive the
# dev-group reinstall above — force the compatible version explicitly.
RUN pip install "pydyf==0.10.0"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ------- production -------
FROM base AS production
RUN pip install "pydyf==0.10.0"
RUN addgroup --system app && adduser --system --group app
USER app
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
