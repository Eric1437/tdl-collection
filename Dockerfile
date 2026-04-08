# tdl：使用仓库内 docker/tdl/ 下的本地文件（避免构建时从网络下载）
# 请先将 tdl_Linux_64bit.tar.gz 或解压后的 tdl 放入 docker/tdl/，参见 docker/tdl/README.txt

FROM node:20-bookworm-slim AS frontend-build
WORKDIR /fe
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY docker/tdl/ /opt/tdl-in/
RUN set -e; \
    if [ -f /opt/tdl-in/tdl_Linux_64bit.tar.gz ]; then \
      tar -xzf /opt/tdl-in/tdl_Linux_64bit.tar.gz -C /usr/local/bin; \
    elif [ -f /opt/tdl-in/tdl ]; then \
      cp /opt/tdl-in/tdl /usr/local/bin/tdl; \
    else \
      echo "ERROR: 请先将 tdl_Linux_64bit.tar.gz 或 tdl 放入 docker/tdl/ 后再构建镜像。说明见 docker/tdl/README.txt" >&2; \
      exit 1; \
    fi && \
    chmod +x /usr/local/bin/tdl && \
    rm -rf /opt/tdl-in

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
