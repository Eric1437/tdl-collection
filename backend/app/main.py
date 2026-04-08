from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_files import router as files_router
from app.api.routes_health import router as health_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_login_ws import router as login_ws_router
from app.config import settings

app = FastAPI(title="tdl-web", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(jobs_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(login_ws_router)

_static = Path(__file__).resolve().parent.parent / "static"
if _static.is_dir() and any(_static.iterdir()):
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="spa")
