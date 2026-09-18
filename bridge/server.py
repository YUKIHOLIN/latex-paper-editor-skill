"""Loopback-only HTTP bridge for the PDF selection viewer."""

from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import tempfile
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


def apply_match(root: Path, match: dict, replacement_text: str) -> dict:
    """Apply one previously returned match after rechecking its source text."""
    relative = Path(str(match.get("file", "")))
    source_path = (root / relative).resolve()
    try:
        source_path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("source path escapes workspace") from exc
    if source_path.suffix != ".tex" or not source_path.is_file():
        raise ValueError("source file is not an existing .tex file")
    try:
        start = int(match["startLine"])
        end = int(match["endLine"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid source line span") from exc
    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    if start < 1 or end < start or end > len(lines):
        raise ValueError("source line span is out of range")
    current = "".join(lines[start - 1 : end]).rstrip("\r\n")
    expected = str(match.get("sourceText", "")).rstrip("\r\n")
    if current != expected:
        raise ValueError("source changed since the PDF selection was made")
    had_newline = "".join(lines[start - 1 : end]).endswith(("\n", "\r"))
    replacement = str(replacement_text).replace("\r\n", "\n").rstrip("\n")
    if had_newline:
        replacement += "\n"
    updated = lines[: start - 1] + [replacement] + lines[end:]
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=source_path.parent, delete=False) as handle:
        handle.writelines(updated)
        temporary = Path(handle.name)
    temporary.replace(source_path)
    return {"file": relative.as_posix(), "startLine": start, "endLine": end}


def run_preview(root: Path) -> dict:
    preview = root / "scripts" / "preview.py"
    if not preview.is_file():
        return {"status": "skipped", "message": "scripts/preview.py is not present"}
    result = subprocess.run([sys.executable, str(preview)], cwd=root, capture_output=True, text=True, check=False)
    return {
        "status": "ok" if result.returncode == 0 else "failed",
        "exitCode": result.returncode,
        "output": (result.stdout + result.stderr)[-6000:],
    }


def publish_changes(root: Path, relative_file: str) -> dict:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)

    root_check = run("rev-parse", "--show-toplevel")
    if root_check.returncode != 0:
        return {"status": "skipped", "message": "workspace is not a git repository"}
    add = run("add", "--", relative_file)
    if add.returncode != 0:
        return {"status": "failed", "message": add.stderr[-2000:]}
    commit = run("commit", "-m", f"paper: apply PDF annotation to {relative_file}")
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr).lower():
        return {"status": "failed", "message": commit.stderr[-2000:]}
    push = run("push")
    if push.returncode != 0:
        return {"status": "failed", "message": push.stderr[-2000:]}
    return {"status": "ok", "message": "committed and pushed"}


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
        if path not in {"/api/match", "/api/preview", "/api/apply"}:
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
        if path == "/api/apply":
            try:
                applied = apply_match(self.root, payload.get("match", {}), str(payload.get("replacementText", ""))[:20_000])
                result = {"applied": applied, "preview": run_preview(self.root)}
                if payload.get("publish", True):
                    result["publish"] = publish_changes(self.root, applied["file"])
                else:
                    result["publish"] = {"status": "skipped", "message": "publish disabled"}
            except (ValueError, OSError) as exc:
                self._json(409, {"error": str(exc)})
                return
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
