from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import DownloadJob, JobStatus
from app.schemas.job import DlFromLinksPayload, ExportThenDlPayload, JobCreate


def create_job(db: Session, body: JobCreate) -> DownloadJob:
    parsed = body.parsed_payload()
    payload_dict: dict
    if isinstance(parsed, ExportThenDlPayload):
        payload_dict = parsed.model_dump(mode="json")
    else:
        payload_dict = parsed.model_dump(mode="json")

    job = DownloadJob(
        status=JobStatus.pending.value,
        kind=body.kind,
        payload=payload_dict,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
