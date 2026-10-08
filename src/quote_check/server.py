"""Локальная страница проверки. Слушает только этот компьютер."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from quote_check.check import field_status, match_span

STATIC = Path(__file__).resolve().parent / "static"
MAX_BODY = 1_000_000


def evaluate(payload):
    """Ответ для формы: статус и, если цитата нашлась, где она в тексте."""
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
    if span:
        result["start"], result["end"] = span
    else:
        result["start"] = None
        result["end"] = None
    return 200, result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
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
        if self.path.split("?", 1)[0] != "/api/check":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > MAX_BODY:
            body = json.dumps({"error": "Слишком длинный запрос"}).encode("utf-8")
            self._send(413, body, "application/json; charset=utf-8")
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            body = json.dumps({"error": "Не разобрал JSON"}).encode("utf-8")
            self._send(400, body, "application/json; charset=utf-8")
            return
        status, result = evaluate(payload)
        self._send(status, json.dumps(result, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def log_message(self, fmt, *args):
        return

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host="127.0.0.1", port=8765, open_browser=True):
    import threading
    import webbrowser

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
    print(f"Интерфейс: {url}")
    print("Закрыть: Ctrl+C")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        bound.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено")
    finally:
        bound.server_close()
