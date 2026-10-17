"""Verify an already-running combined container without credentials or private files."""
import argparse
import json
import time
from urllib.error import URLError, HTTPError
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    for attempt in range(30):
        try:
            with urlopen(base + "/api/health", timeout=3) as response:
                health = json.load(response)
                if response.status == 200 and health.get("status") == "ok":
                    break
        except (URLError, HTTPError, TimeoutError):
            pass
        time.sleep(2)
    else:
        raise RuntimeError("Combined web/API service failed readiness checks")
    for path in ("/", "/api/courses", "/api/study/course-demo-biologie/pdf?kind=all"):
        with urlopen(base + path, timeout=15) as response:
            body = response.read()
            assert response.status == 200, path
            if path == "/":
                assert b"4next" in body.lower() and b"Conturile" in body, "Free-demo reset notice missing"
            elif path == "/api/courses":
                assert len(json.loads(body)) >= 2, "Authored educational samples missing"
            else:
                assert body.startswith(b"%PDF-"), "Unicode PDF export unavailable"
    print("Combined image: readiness, frontend reset notice, public catalog and PDF passed")


if __name__ == "__main__":
    main()
