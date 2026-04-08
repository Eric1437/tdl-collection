# tdl-web

Web UI and HTTP API around **[tdl](https://github.com/iyear/tdl)** (Telegram Downloader): queue long downloads with **Celery + Redis**, manage jobs from a **Vue** SPA, and browse downloaded media.

**Disclaimer:** Use only in compliance with Telegram’s Terms of Service and applicable law. You are responsible for your account and data. This project is not affiliated with Telegram.

## Features

- **Docker Compose**: `api` (FastAPI + static UI), `worker` (Celery), `Redis`, shared volume `/data` for tdl session (`~/.tdl`), SQLite DB, and downloads.
- **Jobs**: `export_then_dl` runs `tdl chat export` then `tdl dl`; `dl_from_links` runs `tdl dl -u ...`.
- **Login**: WebSocket bridge to `tdl login` (QR / code / desktop), streaming stdout to the browser.
- **Gallery**: List and preview images/videos under the download directory (Bearer or `token` query for media URLs).

## Quick start (Docker)

1. Copy environment file:

   ```bash
   cp .env.example .env
   ```

2. Set `API_TOKEN` in `.env` to a long random string (required for API/UI when set).

3. Build and run:

   ```bash
   docker compose up --build -d
   ```

4. Open `http://localhost:8000` — the SPA is served from the API container.

5. **Telegram login**: open **Telegram login**, set the same API token in the page, choose mode, **Connect**, and complete the flow in the log (QR or verification code as prompted by tdl).

6. **Jobs**: create a job under **Jobs**; monitor status and logs; use **Gallery** to browse files under `/data/downloads` in the container (mapped to the `tdl_data` volume).

### Volumes

- `tdl_data` → `/data` inside containers: `.tdl` session, `app.db`, and `downloads/`.

### Services

| Service | Purpose |
|--------|---------|
| `api` | Uvicorn, Alembic migrations on start, serves `/api/*`, `/health`, `/ws/*`, and static UI |
| `worker` | `celery -A app.workers.celery_app worker --concurrency=1` |
| `redis` | Celery broker and result backend |

## Local development (without Docker)

Requirements: Python 3.12+, Node 20+, Redis reachable at `REDIS_URL`.

```bash
# Backend
cd backend
pip install -r requirements.txt
set PYTHONPATH=.   # Windows; export PYTHONPATH=. on Unix
copy ..\\.env.example ..\\.env   # edit API_TOKEN, REDIS_URL=redis://localhost:6379/0, DATABASE_URL=sqlite:///./app.db
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# Celery worker (second terminal)
cd backend
set PYTHONPATH=.
celery -A app.workers.celery_app worker --loglevel=INFO --concurrency=1
```

```bash
# Frontend (third terminal)
cd frontend
npm install
npm run dev
```

Vite proxies `/api`, `/health`, and `/ws` to `http://127.0.0.1:8000`. Install **tdl** on your PATH and set `HOME` or session directory so `tdl` can write its config (see [tdl docs](https://docs.iyear.me/tdl/)).

## API overview

- `GET /health` — liveness.
- `POST /api/jobs` — create job (JSON body per `JobCreate` in [backend/app/schemas/job.py](backend/app/schemas/job.py)).
- `GET /api/jobs`, `GET /api/jobs/{id}`, `GET /api/jobs/{id}/log`, `POST /api/jobs/{id}/cancel`.
- `GET /api/files/browse?path=` — directory listing (paths relative to download root).
- `GET /api/files/media?path=` — file response (use `Authorization: Bearer …` or `?token=` for `<img>` / `<video>`).
- `WS /ws/tdl-login?mode=qr|code|desktop&token=` — interactive login.

## Security notes

- Set a strong `API_TOKEN` and do not expose Redis or the API port to the public internet without TLS and a reverse proxy.
- Prefer deploying behind a VPN or private network.

## Build arguments

The image downloads tdl from GitHub releases. Override version:

```bash
docker compose build --build-arg TDL_VERSION=v0.20.2
```

## Repository layout

- [backend/](backend/) — FastAPI, Celery tasks, Alembic.
- [frontend/](frontend/) — Vite + Vue 3 SPA (built into the image as `/app/static`).
- [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml), [docker-entrypoint.sh](docker-entrypoint.sh).
