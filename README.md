# tdl-web

基于 **[tdl](https://github.com/iyear/tdl)**（Telegram 下载器）的 Web 界面与 HTTP API：用 **Celery + Redis** 排队长时间下载，在 **Vue** 单页应用中管理任务，并浏览已下载的媒体。

**免责声明：** 请仅在遵守 Telegram 服务条款及适用法律的前提下使用。您需自行对账号与数据负责。本项目与 Telegram 官方无关。

## 功能

- **Docker Compose**：`api`（FastAPI + 静态前端）、`worker`（Celery）、`Redis`，共享卷 `/data` 存放 tdl 会话（`~/.tdl`）、SQLite 数据库与下载内容。
- **任务**：`export_then_dl` 依次执行 `tdl chat export` 与 `tdl dl`；`dl_from_links` 执行 `tdl dl -u ...`。
- **登录**：通过 WebSocket 桥接 `tdl login`（二维码 / 验证码 / 桌面端导入），将标准输出流式推到浏览器。
- **图库**：在下载目录下列表并预览图片/视频（媒体 URL 使用 Bearer 或查询参数 `token`）。

## 快速开始（Docker）

### 离线准备 tdl（网络不佳时）

镜像**不再在构建时从 GitHub 下载** tdl。请在本机用浏览器或其他方式下载 Linux amd64 制品后，任选其一放入 `docker/tdl/`：

- `tdl_Linux_64bit.tar.gz`（官方 Release 压缩包，推荐），或  
- 解压后的可执行文件，命名为 `tdl`（无后缀）

详细说明见 [docker/tdl/README.txt](docker/tdl/README.txt)。然后再执行下面的 `docker compose build`。

1. 复制环境文件：

   ```bash
   cp .env.example .env
   ```

2. 在 `.env` 中将 `API_TOKEN` 设为一串足够长的随机字符（一旦设置，则 API/前端均需携带该令牌）。

3. 构建并启动：

   ```bash
   docker compose up --build -d
   ```

4. 浏览器打开 `http://localhost:8000` —— 单页应用由 API 容器一并提供。

5. **Telegram 登录**：进入 **Telegram login** 页面，填写相同的 API 令牌，选择模式后点击 **Connect**，按日志提示完成流程（二维码或验证码等，以 tdl 实际输出为准）。

6. **任务**：在 **Jobs** 中创建任务并查看状态与日志；在 **Gallery** 中浏览容器内 `/data/downloads` 下的文件（对应卷 `tdl_data`）。

### 数据卷

- `tdl_data` → 容器内 `/data`：包含 `.tdl` 会话、`app.db` 与 `downloads/`。

### 服务说明

| 服务 | 作用 |
|------|------|
| `api` | Uvicorn；启动时执行 Alembic 迁移；提供 `/api/*`、`/health`、`/ws/*` 与静态前端 |
| `worker` | `celery -A app.workers.celery_app worker --concurrency=1` |
| `redis` | Celery 消息代理与结果后端 |

## 本地开发（不用 Docker）

环境要求：Python 3.12+、Node 20+、可通过 `REDIS_URL` 访问的 Redis。

```bash
# 后端
cd backend
pip install -r requirements.txt
set PYTHONPATH=.   # Windows；Unix 使用 export PYTHONPATH=.
copy ..\\.env.example ..\\.env   # 编辑 API_TOKEN、REDIS_URL=redis://localhost:6379/0、DATABASE_URL=sqlite:///./app.db
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# Celery Worker（第二个终端）
cd backend
set PYTHONPATH=.
celery -A app.workers.celery_app worker --loglevel=INFO --concurrency=1
```

```bash
# 前端（第三个终端）
cd frontend
npm install
npm run dev
```

Vite 将 `/api`、`/health`、`/ws` 代理到 `http://127.0.0.1:8000`。请在本机 PATH 中安装 **tdl**，并正确设置 `HOME` 或会话目录，以便 tdl 写入配置（参见 [tdl 文档](https://docs.iyear.me/tdl/)）。

## API 概览

- `GET /health` —— 存活检查。
- `POST /api/jobs` —— 创建任务（JSON 体见 [backend/app/schemas/job.py](backend/app/schemas/job.py) 中的 `JobCreate`）。
- `GET /api/jobs`、`GET /api/jobs/{id}`、`GET /api/jobs/{id}/log`、`POST /api/jobs/{id}/cancel`。
- `GET /api/files/browse?path=` —— 目录列表（路径相对于下载根目录）。
- `GET /api/files/media?path=` —— 返回文件（`<img>` / `<video>` 可使用 `Authorization: Bearer …` 或 `?token=`）。
- `WS /ws/tdl-login?mode=qr|code|desktop&token=` —— 交互式登录。

## 安全提示

- 使用足够强的 `API_TOKEN`；在未配置 TLS 与反向代理时，不要将 Redis 或 API 端口直接暴露到公网。
- 优先部署在 VPN 或私有网络之后。

## 仓库结构

- [backend/](backend/) —— FastAPI、Celery 任务、Alembic。
- [frontend/](frontend/) —— Vite + Vue 3 单页应用（构建后打入镜像为 `/app/static`）。
- [docker/tdl/](docker/tdl/) —— **构建前**放入本机下载的 `tdl` 或 `tdl_Linux_64bit.tar.gz`（见上文「离线准备 tdl」）。
- [Dockerfile](Dockerfile)、[docker-compose.yml](docker-compose.yml)、[docker-entrypoint.sh](docker-entrypoint.sh)。
