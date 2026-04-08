from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.api.deps import require_api_token
from app.config import settings
from app.services.pathutil import safe_under_root

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/browse")
def browse(
    _: Annotated[None, Depends(require_api_token)],
    path: str = "",
) -> list[dict]:
    root = Path(settings.download_dir).resolve()
    try:
        target = safe_under_root(root, path) if path.strip() else root
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not target.exists():
        raise HTTPException(status_code=404, detail="path not found")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="not a directory")

    items: list[dict] = []
    for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        try:
            st = child.stat()
            size = st.st_size if child.is_file() else None
        except OSError:
            size = None
        items.append(
            {
                "name": child.name,
                "path": str(child.relative_to(root)).replace("\\", "/"),
                "is_dir": child.is_dir(),
                "size": size,
            }
        )
    return items


@router.get("/media")
def media_file(
    _: Annotated[None, Depends(require_api_token)],
    path: str = Query(..., description="Path relative to download root"),
) -> FileResponse:
    root = Path(settings.download_dir).resolve()
    try:
        target = safe_under_root(root, path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(
        path=target,
        filename=target.name,
        headers={"Accept-Ranges": "bytes"},
    )
