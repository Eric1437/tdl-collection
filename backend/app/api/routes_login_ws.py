import asyncio
import os
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.deps import ws_token_ok
from app.config import settings

router = APIRouter(tags=["login"])


def _login_cmd(mode: str) -> list[str]:
    exe = os.environ.get("TDL_BIN", "tdl")
    if mode == "desktop":
        return [exe, "login"]
    if mode in ("qr", "code"):
        return [exe, "login", "-T", mode]
    raise ValueError("mode must be desktop, qr, or code")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = settings.data_home
    return env


@router.websocket("/ws/tdl-login")
async def tdl_login_ws(
    websocket: WebSocket,
    mode: str = Query("qr"),
    token: Optional[str] = Query(None),
) -> None:
    if not ws_token_ok(token):
        await websocket.close(code=4401)
        return

    try:
        cmd = _login_cmd(mode)
    except ValueError:
        await websocket.close(code=4400)
        return

    await websocket.accept()
    await websocket.send_text(f"[system] running: {' '.join(cmd)}\n")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
            env=_env(),
        )
    except FileNotFoundError:
        await websocket.send_text("[error] tdl binary not found in PATH\n")
        await websocket.close()
        return

    async def pump_stdout() -> None:
        assert process.stdout is not None
        while True:
            chunk = await process.stdout.read(4096)
            if not chunk:
                break
            await websocket.send_text(chunk.decode("utf-8", errors="replace"))

    async def pump_stdin() -> None:
        assert process.stdin is not None
        try:
            while True:
                msg = await websocket.receive_text()
                data = msg.encode("utf-8")
                if not data.endswith(b"\n"):
                    data += b"\n"
                process.stdin.write(data)
                await process.stdin.drain()
        except WebSocketDisconnect:
            pass

    out_task = asyncio.create_task(pump_stdout())
    in_task = asyncio.create_task(pump_stdin())
    rc, _ = await asyncio.gather(process.wait(), out_task)
    in_task.cancel()
    try:
        await in_task
    except asyncio.CancelledError:
        pass
    try:
        await websocket.send_text(f"\n[system] process exited with code {rc}\n")
    except Exception:
        pass
    await websocket.close()
