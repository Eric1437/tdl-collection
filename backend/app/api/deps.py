from typing import Annotated, Optional

from fastapi import Header, HTTPException, Query, status

from app.config import settings


async def require_api_token(
    authorization: Annotated[Optional[str], Header()] = None,
    token: Annotated[Optional[str], Query()] = None,
) -> None:
    tok = settings.api_token
    if not tok:
        return
    if authorization == f"Bearer {tok}":
        return
    if token == tok:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing token (use Authorization header or token query)",
    )


def ws_token_ok(token: Optional[str]) -> bool:
    tok = settings.api_token
    if not tok:
        return True
    return token == tok
