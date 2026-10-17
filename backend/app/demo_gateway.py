"""Optional outer ASGI boundary for an isolated temporary demo, never the local database."""
import hmac
import os
from pathlib import Path


class DemoGateway:
    def __init__(self, app, token):
        if len(token) < 40:
            raise RuntimeError("DEMO_PROXY_TOKEN must contain at least 40 characters.")
        self.app, self.token = app, token.encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            supplied = dict(scope.get("headers", [])).get(b"x-4next-proxy-key", b"")
            if not hmac.compare_digest(supplied, self.token):
                # Reject before reading a body or dispatching an application route.
                await send({"type": "http.response.start", "status": 404,
                            "headers": [(b"content-type", b"application/json"), (b"cache-control", b"no-store")]})
                await send({"type": "http.response.body", "body": b'{"detail":"Not found"}'})
                return
        await self.app(scope, receive, send)


def create_demo_app():
    # Fail closed: launch this entrypoint only with a separate storage directory.
    from app.config import BASE_DIR, DATA_DIR, DB_PATH, UPLOAD_DIR, MEDIA_DIR
    data, base = DATA_DIR.resolve(), BASE_DIR.resolve()
    storage = [path.resolve() for path in (DB_PATH,UPLOAD_DIR,MEDIA_DIR)]
    storage.extend((MEDIA_DIR / kind).resolve() for kind in ("audio","video","diagrams","covers"))
    if data == base or base.is_relative_to(data) or not all(path.is_relative_to(data) for path in storage):
        raise RuntimeError("The demo requires a separate DATA_DIR containing its database, uploads and media.")
    local_db = base / "book2course.db"
    if storage[0].exists() and local_db.exists() and storage[0].samefile(local_db):
        raise RuntimeError("The demo database must not be a link to the local database.")
    token = os.getenv("DEMO_PROXY_TOKEN", "")
    if not token and os.getenv("DEMO_PROXY_TOKEN_FILE"):
        token = Path(os.environ["DEMO_PROXY_TOKEN_FILE"]).read_text(encoding="utf-8").strip()
    from app.main import app
    return DemoGateway(app, token)
