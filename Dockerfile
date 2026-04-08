# tdl binary (Linux amd64)
ARG TDL_VERSION=v0.20.2
FROM debian:bookworm-slim AS tdl-fetch
ARG TDL_VERSION
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget \
    && wget -q "https://github.com/iyear/tdl/releases/download/${TDL_VERSION}/tdl_Linux_64bit.tar.gz" -O /tmp/tdl.tgz \
    && tar -xzf /tmp/tdl.tgz -C /usr/local/bin \
    && chmod +x /usr/local/bin/tdl \
    && rm /tmp/tdl.tgz \
    && apt-get purge -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

FROM node:20-bookworm-slim AS frontend-build
WORKDIR /fe
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=tdl-fetch /usr/local/bin/tdl /usr/local/bin/tdl

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_HOME=/data \
    TDL_HOME=/data/.tdl \
    DOWNLOAD_DIR=/data/downloads \
    HOME=/data

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY backend/alembic.ini .
COPY backend/alembic ./alembic

COPY --from=frontend-build /fe/dist ./static

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
