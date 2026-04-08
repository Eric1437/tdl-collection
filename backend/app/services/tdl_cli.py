"""Build tdl CLI argument lists (no shell interpolation)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.schemas.job import DlFromLinksPayload, ExportThenDlPayload, RangeType


def _tdl_bin() -> str:
    return os.environ.get("TDL_BIN", "tdl")


def build_chat_export_args(
    payload: ExportThenDlPayload,
    output_json: Path,
) -> list[str]:
    cmd = [
        _tdl_bin(),
        "chat",
        "export",
        "-c",
        payload.chat.strip(),
        "-o",
        str(output_json),
    ]
    rt = payload.range_type
    if rt == RangeType.time:
        cmd.extend(["-T", "time"])
        if isinstance(payload.range_args, list) and len(payload.range_args) == 2:
            r = f"{payload.range_args[0]},{payload.range_args[1]}"
        else:
            raise ValueError("time range requires range_args as [start_ts, end_ts]")
    elif rt == RangeType.id:
        cmd.extend(["-T", "id"])
        if isinstance(payload.range_args, list) and len(payload.range_args) == 2:
            r = f"{payload.range_args[0]},{payload.range_args[1]}"
        else:
            raise ValueError("id range requires range_args as [low, high]")
    elif rt == RangeType.last:
        cmd.extend(["-T", "last"])
        ra = payload.range_args
        if isinstance(ra, int):
            last_n = ra
        elif isinstance(ra, list) and len(ra) >= 1:
            last_n = int(ra[0])
        else:
            raise ValueError("last range requires int or single-element list in range_args")
        r = str(last_n)
    else:
        raise ValueError(f"unknown range_type {rt}")
    cmd.extend(["-i", r])

    if payload.filter_expr:
        cmd.extend(["-f", payload.filter_expr])
    if payload.topic_id is not None:
        cmd.extend(["--topic", str(payload.topic_id)])
    if payload.reply_post_id is not None:
        cmd.extend(["--reply", str(payload.reply_post_id)])

    return cmd


def build_dl_from_json_args(
    json_path: Path,
    dest_dir: Path,
    payload: ExportThenDlPayload,
) -> list[str]:
    cmd = [_tdl_bin(), "dl", "-f", str(json_path), "-d", str(dest_dir)]
    _append_dl_flags(cmd, payload.model_dump())
    return cmd


def build_dl_from_links_args(payload: DlFromLinksPayload, dest_dir: Path) -> list[str]:
    cmd = [_tdl_bin(), "dl", "-d", str(dest_dir)]
    for u in payload.links:
        cmd.extend(["-u", u.strip()])
    _append_dl_flags(cmd, payload.model_dump())
    return cmd


def _append_dl_flags(cmd: list[str], data: dict[str, Any]) -> None:
    ext = data.get("extensions_include")
    if ext:
        cmd.extend(["-i", ext])
    if data.get("takeout"):
        cmd.append("--takeout")
    if data.get("desc"):
        cmd.append("--desc")
    if data.get("group"):
        cmd.append("--group")
    if data.get("skip_same"):
        cmd.append("--skip-same")


def job_work_dir(download_dir: str, job_id: str) -> Path:
    base = Path(download_dir) / ".jobs" / job_id
    return base


def ensure_job_log_path(download_dir: str, job_id: str) -> Path:
    logs = Path(download_dir) / ".logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs / f"job-{job_id}.log"
