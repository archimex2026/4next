"""Exercise pre-parser body limits without real databases, uploads or services."""
import asyncio
import json
import unittest
from unittest.mock import patch

from fastapi import FastAPI, File, UploadFile

from app.request_limits import RequestBodyLimitsMiddleware


def request_scope(path="/api/books/upload", method="POST", headers=()):
    return {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "scheme": "http", "method": method, "path": path, "raw_path": path.encode(),
            "query_string": b"", "root_path": "", "headers": list(headers),
            "client": ("127.0.0.1", 4321), "server": ("testserver", 80)}


class RequestBodyLimitTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, middleware, scope, messages):
        pending = list(messages)
        sent, received = [], []

        async def receive():
            received.append(True)
            if pending:
                return pending.pop(0)
            return {"type": "http.disconnect"}

        async def send(message):
            sent.append(message)

        await middleware(scope, receive, send)
        return sent, received

    def multipart_app(self):
        app = FastAPI()

        @app.post("/api/books/upload")
        async def upload(file: UploadFile = File(...)):
            return {"size": len(await file.read())}

        return app

    def status(self, messages):
        return next(message["status"] for message in messages if message["type"] == "http.response.start")

    async def test_anonymous_and_invalid_sessions_rejected_before_reading(self):
        for path in ["/api/books/upload", "/api/books/inspect", "/api/books/upload/"]:
            for cookie in [b"", b"four_next_session=invalid"]:
                middleware = RequestBodyLimitsMiddleware(self.multipart_app(), authenticate_upload=lambda request: None)
                with patch("starlette.formparsers.SpooledTemporaryFile") as spool:
                    sent, received = await self.invoke(middleware, request_scope(path, headers=[(b"cookie", cookie)]),
                                                      [{"type": "http.request", "body": b"a" * 2048}])
                self.assertEqual(self.status(sent), 401)
                self.assertEqual(received, [])
                spool.assert_not_called()

    async def test_declared_oversize_rejected_before_reading_or_spooling(self):
        middleware = RequestBodyLimitsMiddleware(self.multipart_app(), max_body_bytes=1024, authenticate_upload=lambda request: {"id": "user"})
        with patch("starlette.formparsers.SpooledTemporaryFile") as spool:
            sent, received = await self.invoke(middleware, request_scope(headers=[(b"content-length", b"1025")]), [])
        self.assertEqual(self.status(sent), 413)
        self.assertEqual(received, [])
        spool.assert_not_called()

    async def test_chunked_oversize_rejected_before_multipart_spooling(self):
        middleware = RequestBodyLimitsMiddleware(self.multipart_app(), max_body_bytes=1024, authenticate_upload=lambda request: {"id": "user"})
        with patch("starlette.formparsers.SpooledTemporaryFile") as spool:
            sent, received = await self.invoke(middleware,
                request_scope(headers=[(b"content-type", b"multipart/form-data; boundary=test"), (b"transfer-encoding", b"chunked")]),
                [{"type": "http.request", "body": b"a" * 800, "more_body": True},
                 {"type": "http.request", "body": b"b" * 300, "more_body": True}])
        self.assertEqual(self.status(sent), 413)
        self.assertEqual(len(received), 2)
        spool.assert_not_called()

    async def test_actual_bytes_enforced_even_when_declared_length_is_smaller(self):
        middleware = RequestBodyLimitsMiddleware(self.multipart_app(), max_body_bytes=100, authenticate_upload=lambda request: True)
        sent, _ = await self.invoke(middleware, request_scope(headers=[(b"content-length", b"1")]),
                                   [{"type": "http.request", "body": b"a" * 101}])
        self.assertEqual(self.status(sent), 413)

    async def test_valid_multipart_body_is_replayed_to_parser(self):
        payload = b'--test\r\nContent-Disposition: form-data; name="file"; filename="notes.txt"\r\nContent-Type: text/plain\r\n\r\nhello\r\n--test--\r\n'
        middleware = RequestBodyLimitsMiddleware(self.multipart_app(), max_body_bytes=1024, authenticate_upload=lambda request: True)
        sent, _ = await self.invoke(middleware, request_scope(headers=[(b"content-type", b"multipart/form-data; boundary=test")]),
                                   [{"type": "http.request", "body": payload[:30], "more_body": True},
                                    {"type": "http.request", "body": payload[30:], "more_body": False}])
        self.assertEqual(self.status(sent), 200)
        content = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
        self.assertEqual(json.loads(content), {"size": 5})

    async def test_replay_preserves_bodies_larger_than_one_chunk(self):
        file_bytes = b"x" * 100_000
        payload = (b'--test\r\nContent-Disposition: form-data; name="file"; filename="notes.txt"\r\n\r\n'
                   + file_bytes + b'\r\n--test--\r\n')
        middleware = RequestBodyLimitsMiddleware(self.multipart_app(), max_body_bytes=len(payload),
                                                  authenticate_upload=lambda request: True)
        sent, _ = await self.invoke(middleware, request_scope(headers=[(b"content-type", b"multipart/form-data; boundary=test")]),
                                   [{"type": "http.request", "body": payload, "more_body": False}])
        self.assertEqual(self.status(sent), 200)
        content = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
        self.assertEqual(json.loads(content), {"size": len(file_bytes)})

    async def test_other_mutations_are_limited_without_requiring_upload_session(self):
        middleware = RequestBodyLimitsMiddleware(self.multipart_app(), max_body_bytes=100,
                                                  authenticate_upload=lambda request: self.fail("Unrelated route checked upload auth"))
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            sent, received = await self.invoke(middleware, request_scope("/api/auth/register", method, [(b"content-length", b"101")]), [])
            self.assertEqual(self.status(sent), 413)
            self.assertEqual(received, [])

    async def test_slow_request_times_out_before_application_runs(self):
        reached = []

        async def downstream(scope, receive, send):
            reached.append(True)

        async def stalled_receive():
            await asyncio.sleep(1)
            return {"type": "http.request", "body": b""}

        sent = []

        async def send(message):
            sent.append(message)

        middleware = RequestBodyLimitsMiddleware(downstream, read_timeout=.01, authenticate_upload=lambda request: True)
        await middleware(request_scope(), stalled_receive, send)
        self.assertEqual(self.status(sent), 408)
        self.assertEqual(reached, [])

    async def test_conflicting_or_invalid_lengths_are_rejected(self):
        middleware = RequestBodyLimitsMiddleware(self.multipart_app(), authenticate_upload=lambda request: True)
        for headers in [[(b"content-length", b"-1")], [(b"content-length", b"abc")],
                        [(b"content-length", b"1"), (b"content-length", b"2")]]:
            sent, received = await self.invoke(middleware, request_scope(headers=headers), [])
            self.assertEqual(self.status(sent), 400)
            self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
