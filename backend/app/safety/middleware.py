"""Bound raw request bytes before JSON parsing, including chunked bodies."""

from __future__ import annotations

import asyncio
import re
import time
import uuid

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestBoundsMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = 65536) -> None:
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def reject(code: int, message: str) -> None:
            request_id = scope.get("state", {}).get("request_id", uuid.uuid4().hex)
            response = JSONResponse(
                {"error": {"code": code, "message": message, "request_id": request_id}},
                status_code=code,
                headers={
                    "X-Request-ID": request_id,
                    "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                },
            )
            await response(scope, receive, send)

        headers = scope.get("headers", [])
        sessions = [v for k, v in headers if k.lower() == b"x-session-id"]
        if len(sessions) > 1 or (
            sessions and not re.fullmatch(rb"[A-Za-z0-9_-]{1,64}", sessions[0])
        ):
            await reject(400, "Invalid session identifier")
            return
        lengths = [v for k, v in headers if k.lower() == b"content-length"]
        if lengths:
            if len(lengths) != 1 or not re.fullmatch(rb"[0-9]{1,12}", lengths[0]):
                await reject(400, "Invalid content length")
                return
            if int(lengths[0]) > self.max_bytes:
                await reject(413, "Request body is too large")
                return
        body = bytearray()
        deadline = time.monotonic() + 10
        while True:
            try:
                message = await asyncio.wait_for(
                    receive(), max(0, deadline - time.monotonic())
                )
            except TimeoutError:
                await reject(408, "Request body timed out")
                return
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_bytes:
                await reject(413, "Request body is too large")
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        replayed = False

        async def bounded_receive() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)
