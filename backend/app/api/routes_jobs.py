from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_api_token
from app.db.models import DownloadJob, JobStatus
from app.db.session import get_db
from app.schemas.job import JobCreate, JobOut
from app.services.job_service import create_job
from app.workers.tasks.tdl_tasks import revoke_job_task, run_tdl_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def post_job(
    body: JobCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_api_token)],
) -> JobOut:
    job = create_job(db, body)
    run_tdl_job.delay(job.id)
    return JobOut.model_validate(job)


@router.get("", response_model=list[JobOut])
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_api_token)],
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
) -> list[JobOut]:
    rows = db.scalars(select(DownloadJob).order_by(DownloadJob.created_at.desc()).offset(skip).limit(limit))
    return [JobOut.model_validate(r) for r in rows.all()]


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_api_token)],
) -> JobOut:
    job = db.get(DownloadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut.model_validate(job)


@router.get("/{job_id}/log")
def get_job_log(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_api_token)],
    tail: int = Query(500, ge=1, le=50000),
) -> dict[str, str]:
    job = db.get(DownloadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if not job.log_path:
        return {"content": ""}
    path = Path(job.log_path)
    if not path.is_file():
        return {"content": ""}
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    content = "\n".join(lines[-tail:])
    return {"content": content}


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_api_token)],
) -> JobOut:
    job = db.get(DownloadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status in (JobStatus.succeeded.value, JobStatus.failed.value, JobStatus.cancelled.value):
        return JobOut.model_validate(job)
    if job.celery_task_id:
        try:
            revoke_job_task(job.celery_task_id)
        except Exception:
            pass
    job.status = JobStatus.cancelled.value
    db.commit()
    db.refresh(job)
    return JobOut.model_validate(job)
