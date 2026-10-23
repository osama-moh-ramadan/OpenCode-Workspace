#!/usr/bin/env python3
"""Local server for the .NET track app — zero dependencies (Python 3.8+ stdlib).

Serves the static app and mirrors your progress to progress.json so the data
lives as a real file on your machine, not only in the browser.

    python3 server.py              # http://127.0.0.1:8123
    PORT=9000 python3 server.py    # custom port

Everything stays local: no analytics, no accounts, no outbound calls.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
PROGRESS_PATH = os.path.join(ROOT, "progress.json")
MAX_BODY_BYTES = 4 * 1024 * 1024
API = "/api/progress"


class Handler(SimpleHTTPRequestHandler):
    """Static files + a tiny progress API."""

    server_version = "dotnet-track/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    # --- helpers ---------------------------------------------------------
    def end_headers(self):
        # Lesson JSON changes as content is authored; never serve stale files.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def _json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _is_api(self) -> bool:
        return urlparse(self.path).path.rstrip("/") == API.rstrip("/")

    # --- verbs -----------------------------------------------------------
    def do_GET(self):  # noqa: N802
        if self._is_api():
            if os.path.isfile(PROGRESS_PATH):
                try:
                    with open(PROGRESS_PATH, "r", encoding="utf-8") as fh:
                        self._json(200, json.load(fh))
                    return
                except (OSError, ValueError) as err:
                    self._json(500, {"ok": False, "error": f"unreadable progress.json: {err}"})
                    return
            self._json(200, {"version": 2, "lessons": {}, "notes": {}, "bookmarks": [], "activity": []})
            return
        super().do_GET()

    def do_POST(self):  # noqa: N802
        if not self._is_api():
            self.send_error(405, "Method Not Allowed")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            self._json(400, {"ok": False, "error": "empty body"})
            return
        if length > MAX_BODY_BYTES:
            self._json(413, {"ok": False, "error": "progress payload too large"})
            return

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as err:
            self._json(400, {"ok": False, "error": f"invalid JSON: {err}"})
            return
        if not isinstance(data, dict):
            self._json(400, {"ok": False, "error": "progress must be a JSON object"})
            return

        tmp = PROGRESS_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, PROGRESS_PATH)
        except OSError as err:
            self._json(500, {"ok": False, "error": f"write failed: {err}"})
            return

        lessons = len(data.get("lessons") or {})
        done = sum(1 for v in (data.get("lessons") or {}).values() if v.get("status") == "done")
        self._json(200, {"ok": True, "file": "progress.json", "lessons": lessons, "done": done})

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.end_headers()

    def log_message(self, fmt, *args):  # quieter console
        path = urlparse(self.path).path if hasattr(self, "path") else "-"
        if path.startswith("/api/"):
            sys.stderr.write("· progress %s\n" % self.address_string())
            return
        sys.stderr.write("%s\n" % (fmt % args))


class Server(ThreadingHTTPServer):
    """ThreadingHTTPServer already mixes in ThreadingMixIn — don't repeat it."""

    daemon_threads = True
    allow_reuse_address = True


def main() -> int:
    port = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8123))
    host = os.environ.get("HOST", "0.0.0.0")
    httpd = Server((host, port), Handler)
    shown = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print(f"مسار .NET — التطبيق شغال على  http://{shown}:{port}")
    print(f"  الجذر: {ROOT}")
    print(f"  التقدّم: {PROGRESS_PATH}")
    print("  اضغط Ctrl+C للإيقاف")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nاتقفل السيرفر.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
