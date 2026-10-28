"""Локальный помощник: черновик, библиотека, чат по своим статьям."""

from __future__ import annotations

import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from quote_check.check import field_status, match_span
from quote_check.library import Library, seed_library
from quote_check.pdfs import pages_from_pdf
from quote_check.writer import (
    DEMO_DRAFT,
    autocomplete,
    chat,
    cite_for,
    continue_writing,
    outline,
    paraphrase,
)

STATIC = Path(__file__).resolve().parent / "static"
MAX_BODY = 8_000_000


class Workspace:
    def __init__(self) -> None:
        self.library = Library()
        seed_library(self.library)
        self.draft = DEMO_DRAFT
        self.title = "Помощник для научной работы"

    def snapshot(self) -> dict:
        return {
            "title": self.title,
            "draft": self.draft,
            "papers": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "authors": p["authors"],
                    "year": p["year"],
                    "chars": p["chars"],
                    "page_count": len(p["pages"]),
                }
                for p in self.library.to_list()
            ],
        }


WORK = Workspace()


def evaluate(payload):
    if not isinstance(payload, dict):
        return 400, {"error": "Нужен JSON-объект"}
    page_text = payload.get("page_text", "")
    quote = payload.get("quote", "")
    if not isinstance(page_text, str) or not isinstance(quote, str):
        return 400, {"error": "Текст страницы и цитата должны быть строками"}
    try:
        page = int(payload.get("page"))
    except (TypeError, ValueError):
        return 400, {"error": "Номер страницы должен быть целым числом"}
    if page < 1:
        return 400, {"error": "Номер страницы должен быть больше нуля"}
    result = field_status(page_text, quote, page)
    span = match_span(page_text, quote) if result["found"] else None
    result["start"], result["end"] = (span if span else (None, None))
    return 200, result


def add_paper(payload):
    title = str(payload.get("title") or "").strip()
    authors = str(payload.get("authors") or "").strip()
    year = str(payload.get("year") or "").strip()
    text = str(payload.get("text") or "").strip()
    raw_b64 = payload.get("file_b64")
    filename = str(payload.get("filename") or "")
    if raw_b64:
        try:
            data = base64.b64decode(raw_b64)
        except Exception:
            return 400, {"error": "Не разобрал файл"}
        if filename.lower().endswith(".pdf"):
            try:
                pages = pages_from_pdf(data)
            except Exception as error:
                return 400, {"error": str(error)}
            paper = WORK.library.add_pages(title or filename, authors, year, pages)
        else:
            text = data.decode("utf-8", errors="replace")
            paper = WORK.library.add(title or filename, authors, year, text)
    else:
        paper = WORK.library.add(title, authors, year, text)
    return 200, {"paper": paper.to_dict(), "state": WORK.snapshot()}


def run_ai(payload):
    action = str(payload.get("action") or "")
    query = str(payload.get("query") or "")
    if payload.get("draft") is not None:
        WORK.draft = str(payload.get("draft") or "")
    if payload.get("title") is not None:
        WORK.title = str(payload.get("title") or WORK.title)
    actions = {
        "continue": lambda: continue_writing(WORK.library, WORK.draft),
        "chat": lambda: chat(WORK.library, query),
        "outline": lambda: outline(WORK.library, query or WORK.title),
        "paraphrase": lambda: paraphrase(WORK.library, query),
        "cite": lambda: cite_for(WORK.library, query or WORK.draft[-400:]),
        "complete": lambda: autocomplete(WORK.library, query or WORK.draft),
    }
    if action not in actions:
        return 400, {"error": "Неизвестное действие"}
    return 200, actions[action]()


def dispatch(path, payload):
    if path == "/api/state":
        return 200, WORK.snapshot()
    if path == "/api/reset":
        WORK.__init__()
        return 200, WORK.snapshot()
    if path == "/api/draft":
        WORK.draft = str(payload.get("draft") or "")
        WORK.title = str(payload.get("title") or WORK.title)
        return 200, {"ok": True}
    if path == "/api/papers":
        try:
            return add_paper(payload)
        except ValueError as error:
            return 400, {"error": str(error)}
    if path == "/api/papers/remove":
        WORK.library.remove(str(payload.get("id") or ""))
        return 200, WORK.snapshot()
    if path == "/api/ai":
        return run_ai(payload)
    if path == "/api/check":
        return evaluate(payload)
    return 404, {"error": "not found"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/state":
            self._json(200, WORK.snapshot())
            return
        if path in ("", "/"):
            path = "/index.html"
        file_path = (STATIC / path.lstrip("/")).resolve()
        if STATIC not in file_path.parents or not file_path.is_file():
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        kind = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
        }.get(file_path.suffix, "application/octet-stream")
        self._send(200, file_path.read_bytes(), kind)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > MAX_BODY:
            self._json(413, {"error": "Слишком длинный запрос"})
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "Не разобрал JSON"})
            return
        status, result = dispatch(path, payload if isinstance(payload, dict) else {})
        self._json(status, result)

    def log_message(self, fmt, *args):
        return

    def _json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self._send(status, raw, "application/json; charset=utf-8")

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host=None, port=None, open_browser=None):
    import os
    import threading
    import webbrowser

    if host is None:
        host = os.environ.get("QUOTE_CHECK_HOST", "127.0.0.1")
    if port is None:
        port = int(os.environ.get("QUOTE_CHECK_PORT", "8765"))
    if open_browser is None:
        open_browser = os.environ.get("QUOTE_CHECK_OPEN_BROWSER", "1") not in ("0", "false", "no")

    bound = None
    last_error = None
    for candidate in range(port, port + 10):
        try:
            bound = ThreadingHTTPServer((host, candidate), Handler)
            port = candidate
            break
        except OSError as error:
            last_error = error
    if bound is None:
        raise last_error

    url = f"http://{host}:{port}/"
    print(f"Интерфейс: {url}", flush=True)
    print("Закрыть: Ctrl+C", flush=True)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        bound.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено")
    finally:
        bound.server_close()
