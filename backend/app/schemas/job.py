from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RangeType(str, Enum):
    time = "time"
    id = "id"
    last = "last"


class ExportThenDlPayload(BaseModel):
    chat: str = Field(..., description="Channel username, id, or t.me link")
    range_type: RangeType = RangeType.time
    range_args: list[int] | int = Field(
        ...,
        description="For time: [start_ts, end_ts]; for id: [low, high]; for last: single int",
    )
    filter_expr: Optional[str] = None
    topic_id: Optional[int] = None
    reply_post_id: Optional[int] = None
    extensions_include: Optional[str] = Field(
        default=None,
        description="Comma-separated extensions for tdl -i, e.g. jpg,png,mp4",
    )
    dest_subdir: str = Field(default="", description="Relative path under DOWNLOAD_DIR")
    takeout: bool = False
    desc: bool = False
    group: bool = False
    skip_same: bool = False

    @field_validator("range_args", mode="before")
    @classmethod
    def coerce_range(cls, v: Any) -> list[int] | int:
        if isinstance(v, int):
            return v
        if isinstance(v, list):
            return v
        raise ValueError("range_args must be int or list of ints")


class DlFromLinksPayload(BaseModel):
    links: list[str] = Field(..., min_length=1)
    extensions_include: Optional[str] = None
    dest_subdir: str = ""
    takeout: bool = False
    desc: bool = False
    group: bool = False
    skip_same: bool = False


class JobCreate(BaseModel):
    kind: Literal["export_then_dl", "dl_from_links"]
    payload: dict[str, Any]

    def parsed_payload(self) -> ExportThenDlPayload | DlFromLinksPayload:
        if self.kind == "export_then_dl":
            return ExportThenDlPayload.model_validate(self.payload)
        return DlFromLinksPayload.model_validate(self.payload)


class JobOut(BaseModel):
    id: str
    status: str
    kind: str
    payload: dict[str, Any]
    celery_task_id: Optional[str] = None
    error_message: Optional[str] = None
    log_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
