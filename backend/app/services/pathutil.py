from pathlib import Path


def safe_under_root(root: Path, *relative_parts: str) -> Path:
    """Join path segments under root; reject .. and absolute segments."""
    root = root.resolve()
    if not relative_parts or all(not p for p in relative_parts):
        return root
    cur = root
    for part in relative_parts:
        if not part:
            continue
        for seg in part.replace("\\", "/").split("/"):
            if seg in ("", "."):
                continue
            if seg == "..":
                raise ValueError("invalid path segment")
            cur = cur / seg
    out = cur.resolve()
    try:
        out.relative_to(root)
    except ValueError as e:
        raise ValueError("path escapes download root") from e
    return out
