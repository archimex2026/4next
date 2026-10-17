"""Bound request bodies before FastAPI's multipart parser can spool files.

The local prototype owns at most ``max_body_bytes`` of prebuffered request data
per request, plus a 64 KiB replay chunk. Production also needs proxy connection
limits and a shared/global concurrency limit; per-request bounds are not quotas.
"""
import asyncio
from collections.abc import Callable

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.security import optional_user


class RequestBodyLimitsMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int = 16 * 1024 * 1024,
                 read_timeout: float = 60.0, authenticate_upload: Callable | None = None):
        if max_body_bytes <= 0 or read_timeout <= 0:
            raise ValueError("Request body and timeout limits must be positive")
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.read_timeout = read_timeout
        self.authenticate_upload = authenticate_upload or optional_user

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            await self.app(scope, receive, send)
            return

        async def reject(status: int, detail: str):
            response = JSONResponse({"detail": detail}, status_code=status,
                                    headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
            await response(scope, receive, send)

        if scope["method"] == "POST" and scope["path"].rstrip("/") in {"/api/books/upload", "/api/books/inspect"}:
            if not self.authenticate_upload(Request(scope)):
                await reject(401, "Conectează-te pentru a încărca un material.")
                return

        lengths = [value.strip() for key, value in scope.get("headers", []) if key.lower() == b"content-length"]
        if lengths:
            try:
                if any(not value.isdigit() for value in lengths):
                    raise ValueError()
                parsed_lengths = {int(value) for value in lengths}
                if len(parsed_lengths) != 1:
                    raise ValueError()
                if parsed_lengths.pop() > self.max_body_bytes:
                    await reject(413, "Cererea depășește limita totală de încărcare.")
                    return
            except ValueError:
                await reject(400, "Dimensiunea declarată a cererii nu este validă.")
                return

        body = bytearray()
        try:
            async with asyncio.timeout(self.read_timeout):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    if len(chunk) > self.max_body_bytes - len(body):
                        await reject(413, "Cererea depășește limita totală de încărcare.")
                        return
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            await reject(408, "Încărcarea a durat prea mult. Încearcă din nou.")
            return

        offset = 0
        delivered_end = False

        async def replay() -> Message:
            nonlocal offset, delivered_end
            if delivered_end:
                return await receive()
            end = min(offset + 64 * 1024, len(body))
            chunk = bytes(memoryview(body)[offset:end])
            offset = end
            more = offset < len(body)
            if not more:
                delivered_end = True
            return {"type": "http.request", "body": chunk, "more_body": more}

        await self.app(scope, replay, send)
