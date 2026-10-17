"""One Render process owns both services and keeps backend credentials out of Node."""
import importlib.util
import subprocess
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app


def runtime():
    path = Path(__file__).resolve().parents[2]/"scripts"/"run_render.py"
    spec = importlib.util.spec_from_file_location("run_render",path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RenderRuntimeTests(unittest.TestCase):
    def test_runtime_uses_same_origin_secure_sessions_and_backend_only_secrets(self):
        module = runtime()
        commands = module.service_commands({"RENDER_EXTERNAL_URL":"https://four-next.onrender.com",
            "ALLOWED_ORIGINS":"https://study.example.com","PORT":"12345","GEMINI_API_KEY":"private-test-key",
            "GOOGLE_API_KEY":"another-private-test-key","DEMO_PROXY_TOKEN":"obsolete-tunnel-key","PATH":"tools"})
        backend,frontend = commands
        self.assertIn("127.0.0.1",backend["args"])
        self.assertIn("8000",backend["args"])
        self.assertIn("--workers",backend["args"])
        self.assertEqual(backend["env"]["GEMINI_API_KEY"],"private-test-key")
        self.assertEqual(backend["env"]["COOKIE_SECURE"],"true")
        self.assertEqual(backend["env"]["DATA_DIR"],"/var/data")
        self.assertEqual(set(backend["env"]["ALLOWED_ORIGINS"].split(",")),
            {"https://four-next.onrender.com","https://study.example.com"})
        self.assertEqual(frontend["env"]["BACKEND_ORIGIN"],"http://127.0.0.1:8000")
        self.assertEqual(frontend["env"]["PORT"],"12345")
        self.assertEqual(frontend["env"]["HOSTNAME"],"0.0.0.0")
        self.assertFalse(any("KEY" in key or "TOKEN" in key for key in frontend["env"]))

    def test_invalid_public_origins_and_port_collisions_fail_before_starting(self):
        module = runtime()
        for overrides in ({},{"RENDER_EXTERNAL_URL":"http://public.example.com"},
            {"ALLOWED_ORIGINS":"*"},{"RENDER_EXTERNAL_URL":"https://user:pass@public.example.com"},
            {"RENDER_EXTERNAL_URL":"https://public.example.com/path"},{"RENDER_EXTERNAL_URL":"https://public.example.com","PORT":"8000"},
            {"RENDER_EXTERNAL_URL":"https://public.example.com","PORT":"not-a-port"}):
            with self.subTest(settings=overrides),self.assertRaises(ValueError):
                module.service_commands(overrides)

    def test_peer_failure_terminates_other_service_and_returns_failure(self):
        module = runtime()
        first,second = FakeProcess(exit_code=7),FakeProcess()
        with patch.object(module.subprocess,"Popen",side_effect=[first,second]):
            code = module.supervise(fake_commands(),shutdown_timeout=.01)
        self.assertEqual(code,7)
        self.assertTrue(second.terminated)
        self.assertTrue(second.waited)

    def test_stop_request_gracefully_terminates_both_services(self):
        module = runtime()
        stop = threading.Event()
        first,second = FakeProcess(),FakeProcess()
        first.on_poll = stop.set
        with patch.object(module.subprocess,"Popen",side_effect=[first,second]):
            code = module.supervise(fake_commands(),stop=stop,shutdown_timeout=.01)
        self.assertEqual(code,0)
        self.assertTrue(first.terminated)
        self.assertTrue(second.terminated)

    def test_start_failure_stops_the_already_started_peer(self):
        module = runtime()
        first = FakeProcess()
        with patch.object(module.subprocess,"Popen",side_effect=[first,OSError("cannot start node")]):
            code = module.supervise(fake_commands(),shutdown_timeout=.01)
        self.assertEqual(code,1)
        self.assertTrue(first.terminated)

    def test_unresponsive_service_is_killed_after_grace_period(self):
        module = runtime()
        first,second = FakeProcess(exit_code=0),FakeProcess(stuck=True)
        with patch.object(module.subprocess,"Popen",side_effect=[first,second]):
            code = module.supervise(fake_commands(),shutdown_timeout=.01)
        self.assertEqual(code,1,"an unsolicited clean exit must still restart the whole application")
        self.assertTrue(second.killed)

    def test_health_checks_only_database_and_hides_database_errors(self):
        class Connection:
            def execute(self,query):
                self.query = query
                return self
            def fetchone(self):
                return [1]
            def close(self):
                pass

        connection = Connection()
        with patch("app.routers.health.get_db_connection",return_value=connection):
            response = TestClient(app).get("/api/health")
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json(),{"status":"ok","database":"ok"})
        self.assertEqual(connection.query,"SELECT 1")
        import sqlite3
        with patch("app.routers.health.get_db_connection",side_effect=sqlite3.OperationalError("secret-path")):
            response = TestClient(app).get("/api/health")
        self.assertEqual(response.status_code,503)
        self.assertNotIn("secret-path",response.text)


class FakeProcess:
    def __init__(self,exit_code=None,stuck=False):
        self.exit_code,self.stuck,self.on_poll = exit_code,stuck,None
        self.terminated = self.killed = self.waited = False
    def poll(self):
        if self.on_poll:
            self.on_poll()
        return self.exit_code
    def terminate(self):
        self.terminated = True
        if not self.stuck:
            self.exit_code = 0
    def wait(self,timeout=None):
        self.waited = True
        if self.stuck and not self.killed:
            raise subprocess.TimeoutExpired("fake",timeout)
        return self.exit_code
    def kill(self):
        self.killed,self.exit_code = True,-9


def fake_commands():
    return [{"name":name,"args":[name],"cwd":".","env":{}} for name in ("backend","frontend")]
