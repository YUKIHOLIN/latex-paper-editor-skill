"""Loopback-only HTTP bridge for the PDF selection viewer."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .matcher import find_matches


def status_payload(root: Path) -> dict:
    return {"pdf": "build/paper.pdf", "sourceRoot": "."}


def match_payload(root: Path, payload: dict) -> dict:
    selected_text = payload.get("selectedText", "")
    if not isinstance(selected_text, str):
        selected_text = ""
    selected_text = selected_text[:20_000]
    return {"matches": find_matches(root, selected_text)}


class BridgeHandler(SimpleHTTPRequestHandler):
    server_version = "CodexPaperBridge/1.0"

    @property
    def root(self) -> Path:
        return Path(self.server.bridge_root)  # type: ignore[attr-defined]

    def _json(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _path_is_safe(self, requested: str) -> Path | None:
        relative = Path(requested.lstrip("/"))
        candidate = (self.root / relative).resolve()
        try:
            candidate.relative_to(self.root.resolve())
        except ValueError:
            return None
        return candidate

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlparse(self.path).path
        if path == "/api/status":
            self._json(200, status_payload(self.root))
            return
        if path == "/":
            path = "/bridge/web/index.html"
        candidate = self._path_is_safe(path)
        if candidate is None or not candidate.is_file():
            self._json(404, {"error": "not found"})
            return
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        data = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlparse(self.path).path
        if path not in {"/api/match", "/api/preview"}:
            self._json(404, {"error": "not found"})
            return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 1_000_000)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"error": "invalid JSON"})
            return
        result = match_payload(self.root, payload if isinstance(payload, dict) else {})
        if path == "/api/preview":
            result["replacementText"] = str(payload.get("replacementText", ""))[:20_000]
            result["writesPerformed"] = False
        self._json(200, result)


def make_server(root: Path, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    root = root.resolve()

    class ConfiguredServer(ThreadingHTTPServer):
        bridge_root = str(root)

    return ConfiguredServer((host, port), BridgeHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = make_server(args.root, args.host, args.port)
    print(f"Paper bridge running at http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
