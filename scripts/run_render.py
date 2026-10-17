"""Run Next publicly and one FastAPI worker on loopback in a single Render service."""
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit


def _public_origin(value):
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
        or parsed.path or parsed.query or parsed.fragment or any(char.isspace() for char in value)):
        raise ValueError("Public origins must be explicit HTTPS origins without paths or credentials.")
    if parsed.port == 0:
        raise ValueError("Public origin port must be valid.")
    return value


def service_commands(environment=None,root=None):
    environment = dict(os.environ if environment is None else environment)
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    port = environment.get("PORT","10000")
    if not port.isdigit() or not 1 <= int(port) <= 65535 or int(port) in {8000,18012,18013,19099}:
        raise ValueError("PORT must be a valid public port distinct from backend port 8000 and Render reserved ports.")
    origins = [value for value in environment.get("ALLOWED_ORIGINS","").split(",") if value.strip()]
    if environment.get("RENDER_EXTERNAL_URL"):
        origins.append(environment["RENDER_EXTERNAL_URL"])
    if not origins:
        raise ValueError("Set RENDER_EXTERNAL_URL or explicit HTTPS ALLOWED_ORIGINS before starting.")
    origins = list(dict.fromkeys(_public_origin(value) for value in origins))
    data_dir = environment.get("DATA_DIR") or "/var/data"
    backend_env = {**environment,"DATA_DIR":data_dir,
        "DATABASE_PATH":environment.get("DATABASE_PATH") or str(Path(data_dir)/"book2course.db"),
        "ALLOWED_ORIGINS":",".join(origins),"COOKIE_SECURE":"true","PORT":"8000",
        "PYTHONUNBUFFERED":"1","WEB_CONCURRENCY":"1"}
    # Node gets an allowlist, not backend credentials or Render/provider API tokens.
    frontend_env = {key:environment[key] for key in ("PATH","HOME","LANG","LC_ALL","TZ","TMPDIR","NODE_OPTIONS") if key in environment}
    frontend_env.update({"NODE_ENV":"production","PORT":port,"HOSTNAME":"0.0.0.0",
        "BACKEND_ORIGIN":"http://127.0.0.1:8000","NEXT_TELEMETRY_DISABLED":"1"})
    return [
        {"name":"backend","args":[sys.executable,"-m","uvicorn","app.main:app","--host","127.0.0.1",
            "--port","8000","--workers","1","--timeout-graceful-shutdown","18"],"cwd":root/"backend","env":backend_env},
        {"name":"frontend","args":["node","server.js"],"cwd":root/"frontend","env":frontend_env},
    ]


def supervise(commands,stop=None,shutdown_timeout=20):
    stop = stop if stop is not None else threading.Event()
    children, exit_code = [],0
    try:
        for command in commands:
            process = subprocess.Popen(command["args"],cwd=command["cwd"],env=command["env"])
            children.append((command["name"],process))
        while not stop.is_set():
            for name,process in children:
                code = process.poll()
                if code is not None:
                    print(f"{name} exited ({code}); stopping both services.",flush=True)
                    exit_code = code if code > 0 else 1
                    stop.set()
                    break
            stop.wait(.25)
    except OSError as exc:
        # Error type only: avoid printing commands/environment or any provider secrets.
        print(f"Could not start application ({type(exc).__name__}).",file=sys.stderr,flush=True)
        exit_code = 1
    finally:
        for _,process in children:
            if process.poll() is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
        deadline = time.monotonic()+shutdown_timeout
        for _,process in children:
            try:
                process.wait(timeout=max(0,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return exit_code


def main():
    stop = threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig,lambda signum,frame:stop.set())
    try:
        commands = service_commands()
    except ValueError as exc:
        print(str(exc),file=sys.stderr)
        return 1
    return supervise(commands,stop)


if __name__ == "__main__":
    raise SystemExit(main())
