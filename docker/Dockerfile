ARG PYTHON_VERSION=3.13-slim-bookworm

FROM python:${PYTHON_VERSION} as builder

WORKDIR /app

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install wheel poetry==1.8.5

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential git

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev,docs --no-root

FROM python:${PYTHON_VERSION} as runtime

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

RUN addgroup --system salute \
    && adduser --system --ingroup salute salute

COPY ./docker/entrypoint.sh /entrypoint
RUN chmod +x /entrypoint
RUN chown salute /entrypoint

COPY ./docker/start.sh /start
RUN chmod +x /start
RUN chown salute /start

RUN mkdir /app/staticfiles
RUN chown salute:salute /app/staticfiles

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY --chown=salute:salute salute /app/salute
COPY --chown=salute:salute manage.py /app/manage.py

USER salute

ENTRYPOINT ["/entrypoint"]