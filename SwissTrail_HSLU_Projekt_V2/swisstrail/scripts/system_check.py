"""Run while SwissTrail is running: python scripts/system_check.py [base-url]"""
import sys
from urllib.request import urlopen

base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
for path, expected in [("/", b"SwissTrail"), ("/api/health", b'"status":"ok"'), ("/docs", b"Swagger")]:
    with urlopen(base + path, timeout=8) as response:
        body = response.read()
        assert response.status == 200 and expected in body, path
        print(f"OK: {path}")
print("HTTP smoke tests passed. Check map tiles manually in the browser too.")
