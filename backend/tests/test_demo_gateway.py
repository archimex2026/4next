"""The public tunnel cannot dispatch even a public API route without the server secret."""
import unittest
import tempfile
import os
from unittest.mock import patch
from pathlib import Path
from fastapi.testclient import TestClient
from app.demo_gateway import DemoGateway, create_demo_app


async def upstream(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"upstream"})


class DemoGatewayTests(unittest.TestCase):
    def test_unauthorized_requests_never_reach_upstream(self):
        client = TestClient(DemoGateway(upstream, "t" * 64))
        for path in ("/", "/docs", "/api/courses", "/media/audio/example.mp3"):
            for headers in ({}, {"x-4next-proxy-key": "incorrect"}):
                response = client.post(path, headers=headers, content=b"private input")
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("upstream", response.text)
                self.assertEqual(response.headers["cache-control"], "no-store")

    def test_valid_proxy_secret_is_upstream_only(self):
        response = TestClient(DemoGateway(upstream, "t" * 64)).get("/api/courses", headers={"x-4next-proxy-key": "t" * 64})
        self.assertEqual(response.text, "upstream")
        self.assertNotIn("x-4next-proxy-key", response.headers)

    def test_weak_secret_and_shared_local_storage_are_rejected(self):
        with self.assertRaises(RuntimeError):
            DemoGateway(upstream, "")
        with patch("app.config.DATA_DIR", Path("/same")), patch("app.config.BASE_DIR", Path("/same")):
            with self.assertRaises(RuntimeError):
                create_demo_app()

    def test_demo_rejects_storage_root_that_contains_the_local_backend(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            base = root/"backend"
            with patch("app.config.DATA_DIR",root),patch("app.config.BASE_DIR",base),\
                patch("app.config.DB_PATH",base/"book2course.db"),\
                patch("app.config.UPLOAD_DIR",base/"uploads"),patch("app.config.MEDIA_DIR",base/"media"),\
                patch.dict("os.environ",{"DEMO_PROXY_TOKEN":"t"*64}):
                with self.assertRaises(RuntimeError):
                    create_demo_app()

    def test_demo_rejects_upload_directory_resolving_outside_demo_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            base,data = root/"backend",root/"demo"
            upload = data/"uploads"
            resolve = Path.resolve

            def resolve_link(path,*args,**kwargs):
                return base/"uploads" if path == upload else resolve(path,*args,**kwargs)

            with patch("app.config.DATA_DIR",data),patch("app.config.BASE_DIR",base),\
                patch("app.config.DB_PATH",data/"demo.db"),patch("app.config.UPLOAD_DIR",upload),\
                patch("app.config.MEDIA_DIR",data/"media"),patch.dict("os.environ",{"DEMO_PROXY_TOKEN":"t"*64}),\
                patch.object(Path,"resolve",autospec=True,side_effect=resolve_link):
                with self.assertRaises(RuntimeError):
                    create_demo_app()

    def test_demo_rejects_hardlinked_local_database(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            base,data = root/"backend",root/"demo"
            base.mkdir()
            data.mkdir()
            local_db, demo_db = base/"book2course.db",data/"demo.db"
            local_db.write_bytes(b"local private database")
            os.link(local_db,demo_db)
            with patch("app.config.DATA_DIR",data),patch("app.config.BASE_DIR",base),\
                patch("app.config.DB_PATH",demo_db),patch("app.config.UPLOAD_DIR",data/"uploads"),\
                patch("app.config.MEDIA_DIR",data/"media"),patch.dict("os.environ",{"DEMO_PROXY_TOKEN":"t"*64}):
                with self.assertRaises(RuntimeError):
                    create_demo_app()

    def test_demo_rejects_media_subdirectory_resolving_outside_demo_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            base,data = root/"backend",root/"demo"
            audio = data/"media"/"audio"
            resolve = Path.resolve

            def resolve_link(path,*args,**kwargs):
                return base/"media"/"audio" if path == audio else resolve(path,*args,**kwargs)

            with patch("app.config.DATA_DIR",data),patch("app.config.BASE_DIR",base),\
                patch("app.config.DB_PATH",data/"demo.db"),patch("app.config.UPLOAD_DIR",data/"uploads"),\
                patch("app.config.MEDIA_DIR",data/"media"),patch.dict("os.environ",{"DEMO_PROXY_TOKEN":"t"*64}),\
                patch.object(Path,"resolve",autospec=True,side_effect=resolve_link):
                with self.assertRaises(RuntimeError):
                    create_demo_app()
