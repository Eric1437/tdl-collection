from __future__ import annotations

import os
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import DownloadJob, JobKind, JobStatus
from app.db.session import SessionLocal
from app.schemas.job import DlFromLinksPayload, ExportThenDlPayload
from app.services import tdl_cli
from app.services.pathutil import safe_under_root
from app.workers.celery_app import celery_app


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = settings.data_home
    return env


def _append_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", errors="replace") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def _run_cmd(cmd: list[str], log_file: Path, env: dict[str, str]) -> int:
    _append_log(log_file, f"$ {' '.join(cmd)}")
    with open(log_file, "a", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
            bufsize=1,
        )
        assert p.stdout is not None
        for line in p.stdout:
            lf.write(line)
            lf.flush()
        return p.wait()


def _fail(db: Session, job: DownloadJob, log_file: Path, msg: str) -> None:
    job.status = JobStatus.failed.value
    job.error_message = msg[:8000]
    db.commit()
    _append_log(log_file, f"[ERROR] {msg}")


@celery_app.task(bind=True, name="tdl.run_job")
def run_tdl_job(self, job_id: str) -> None:
    db = SessionLocal()
    log_file = tdl_cli.ensure_job_log_path(settings.download_dir, job_id)
    env = _env()

    try:
        job = db.get(DownloadJob, job_id)
        if not job:
            _append_log(log_file, f"[ERROR] job not found: {job_id}")
            return
        if job.status == JobStatus.cancelled.value:
            _append_log(log_file, "skipped: job already cancelled")
            return

        job.status = JobStatus.running.value
        job.celery_task_id = self.request.id
        job.log_path = str(log_file)
        db.commit()

        if job.kind == JobKind.export_then_dl.value:
            payload = ExportThenDlPayload.model_validate(job.payload)
            wdir = tdl_cli.job_work_dir(settings.download_dir, job_id)
            wdir.mkdir(parents=True, exist_ok=True)
            export_json = wdir / "export.json"

            cmd_export = tdl_cli.build_chat_export_args(payload, export_json)
            rc = _run_cmd(cmd_export, log_file, env)
            if rc != 0:
                _fail(db, job, log_file, f"tdl chat export exited with code {rc}")
                return

            sub = (payload.dest_subdir or "").strip()
            try:
                dest = safe_under_root(Path(settings.download_dir), sub) if sub else Path(settings.download_dir)
            except ValueError as e:
                _fail(db, job, log_file, str(e))
                return
            dest.mkdir(parents=True, exist_ok=True)

            cmd_dl = tdl_cli.build_dl_from_json_args(export_json, dest, payload)
            rc = _run_cmd(cmd_dl, log_file, env)
            if rc != 0:
                _fail(db, job, log_file, f"tdl dl exited with code {rc}")
                return

        elif job.kind == JobKind.dl_from_links.value:
            payload = DlFromLinksPayload.model_validate(job.payload)
            sub = (payload.dest_subdir or "").strip()
            try:
                dest = safe_under_root(Path(settings.download_dir), sub) if sub else Path(settings.download_dir)
            except ValueError as e:
                _fail(db, job, log_file, str(e))
                return
            dest.mkdir(parents=True, exist_ok=True)

            cmd_dl = tdl_cli.build_dl_from_links_args(payload, dest)
            rc = _run_cmd(cmd_dl, log_file, env)
            if rc != 0:
                _fail(db, job, log_file, f"tdl dl exited with code {rc}")
                return
        else:
            _fail(db, job, log_file, f"unknown job kind {job.kind}")
            return

        job = db.get(DownloadJob, job_id)
        if job and job.status != JobStatus.cancelled.value:
            job.status = JobStatus.succeeded.value
            job.error_message = None
            db.commit()
        _append_log(log_file, "[done] ok")
    except Exception as e:  # noqa: BLE001
        _append_log(log_file, f"[ERROR] {e!r}")
        job = db.get(DownloadJob, job_id)
        if job:
            job.status = JobStatus.failed.value
            job.error_message = str(e)[:8000]
            db.commit()
    finally:
        db.close()


def revoke_job_task(celery_task_id: str) -> None:
    celery_app.control.revoke(celery_task_id, terminate=True)
