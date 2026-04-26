#!/usr/bin/env python3
"""
Local static site + POST /api/match for Gemini.

  pip install -r agent-matchmaker/requirements-app.txt
  export GEMINI_API_KEY="..."   # optional; can also send per-request from the UI
  python3 agent-matchmaker/webapp.py

Open http://127.0.0.1:8765/ — enable "Smart match (Gemini)" to use the API.
Heuristic matching works without a key or even without this server (open index.html).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from matchmaker_lib import (
    ensure_catalog_exists,
    fetch_registry_metadata,
    genai,
    load_dotenv_repo,
    run_match_request,
    run_plan_sequence_request,
)

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent

# Top-level dirs under repo that may contain agent markdown (keep in sync with build_agent_matchmaker.AGENT_DIRS).
_AGENT_MD_ROOTS = frozenset(
    {
        "academic",
        "design",
        "engineering",
        "finance",
        "game-development",
        "marketing",
        "paid-media",
        "product",
        "project-management",
        "sales",
        "spatial-computing",
        "specialized",
        "strategy",
        "support",
        "testing",
    }
)


def _safe_agent_md_path(rel: str) -> Path | None:
    raw = (rel or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None
    if not raw.endswith(".md"):
        return None
    top = raw.split("/", 1)[0]
    if top not in _AGENT_MD_ROOTS:
        return None
    full = (REPO_ROOT / raw).resolve()
    try:
        full.relative_to(REPO_ROOT.resolve())
    except ValueError:
        return None
    if not full.is_file():
        return None
    return full


def _api_key_from_environment() -> str:
    return (
        (os.environ.get("GEMINI_API_KEY") or "").strip()
        or (os.environ.get("GOOGLE_API_KEY") or "").strip()
        or (os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY") or "").strip()
        or (os.environ.get("GENAI_API_KEY") or "").strip()
        or (os.environ.get("GOOGLE_GENAI_API_KEY") or "").strip()
    )


def _read_first_nonempty_key_file() -> str:
    """One-line key files (same idea as Docker secrets) — survives Cursor/IDE launches without shell export."""
    candidates: list[Path] = []
    raw_path = (os.environ.get("GEMINI_API_KEY_FILE") or "").strip()
    if raw_path:
        candidates.append(Path(raw_path).expanduser())
    candidates.append(REPO_ROOT / ".gemini_api_key")
    candidates.append(APP_DIR / ".gemini_api_key")
    seen: set[Path] = set()
    for raw in candidates:
        try:
            key = raw.resolve()
        except OSError:
            key = raw
        if key in seen:
            continue
        seen.add(key)
        try:
            if not raw.is_file():
                continue
            text = raw.read_text(encoding="utf-8").strip()
            if not text or text.startswith("#"):
                continue
            text = text.strip().strip('"').strip("'")
            if text:
                return text
        except OSError:
            continue
    return ""


def _server_has_gemini_credentials() -> bool:
    load_dotenv_repo()
    return bool(_api_key_from_environment() or _read_first_nonempty_key_file())


def _resolve_api_key_for_request(body: dict) -> str:
    raw = body.get("api_key")
    k = (raw if isinstance(raw, str) else "") or ""
    k = k.strip()
    if k:
        return k
    k = _api_key_from_environment()
    if k:
        return k
    return _read_first_nonempty_key_file()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def handle(self) -> None:  # noqa: N802
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    @staticmethod
    def _is_quiet_static_get_path(path: str) -> bool:
        if path in ("/", "/index.html", "/favicon.ico"):
            return True
        if any(
            path.endswith(sfx)
            for sfx in (".js", ".css", ".map", ".json", ".ico", ".png", ".svg", ".gif", ".webp", ".woff", ".woff2", ".ttf", ".eot", ".html")
        ):
            return True
        if path in ("/catalog.json",) or path.startswith("/data/"):
            return True
        return False

    def log_request(self, code: object = "-", size: object = "-") -> None:  # noqa: N802
        """Omit 200/304 log lines for common static `GET` assets; keep API and errors visible."""
        if isinstance(code, HTTPStatus):
            cval: int = int(code.value)  # type: ignore[assignment]
        else:
            try:
                cval = int(str(code).split()[0]) if not isinstance(code, int) else int(code)  # type: ignore[union-attr]
            except (TypeError, ValueError, IndexError):
                cval = 0
        if cval not in (200, 204, 304):
            super().log_request(code, size)
            return
        line = (getattr(self, "requestline", None) or "").strip()
        parts = line.split()
        if len(parts) < 2 or parts[0].upper() != "GET":
            super().log_request(code, size)
            return
        if self._is_quiet_static_get_path(parts[1]):
            return
        super().log_request(code, size)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Quieter default (non–log_request messages)
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _json(self, code: int, body: object) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "gemini_installed": genai is not None,
                    "server_gemini_key": _server_has_gemini_credentials(),
                    "registry_items_count": len(fetch_registry_metadata()),
                },
            )
            return
        if path == "/api/registry-items":
            items = fetch_registry_metadata()
            self._json(HTTPStatus.OK, {"ok": True, "items": items})
            return
        if path == "/data/sources.json":
            src = REPO_ROOT / "data" / "sources.json"
            if not src.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            raw = src.read_text(encoding="utf-8")
            data = raw.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/agent-source":
            rel = (parse_qs(urlparse(self.path).query).get("path") or [""])[0]
            md_path = _safe_agent_md_path(rel)
            if md_path is None:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            raw = md_path.read_text(encoding="utf-8")
            data = raw.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in ("/api/match", "/api/plan-sequence"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if genai is None:
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "ok": False,
                    "error": "Install: pip install -r agent-matchmaker/requirements-app.txt (google-genai)",
                },
            )
            return

        load_dotenv_repo()

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Invalid JSON body"})
            return

        goal = (body.get("goal") or "").strip()
        if not goal:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Missing goal"})
            return

        api_key = _resolve_api_key_for_request(body)
        if not api_key:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": (
                        "No Gemini API key for this server process. Fix ONE of these, then restart webapp.py: "
                        "put your key in a file named `.gemini_api_key` at the repo root or in `agent-matchmaker/` "
                        "(single line, no quotes); or set env `GEMINI_API_KEY_FILE` to the path of a key file; "
                        "or add `GEMINI_API_KEY=...` to `.env` at the repo root; "
                        "or run `export GEMINI_API_KEY=...` in the same terminal before starting the server. "
                        "The UI key field is optional if one of the above is configured."
                    ),
                },
            )
            return

        categories = body.get("categories")
        if categories is not None and not isinstance(categories, list):
            categories = None
        elif isinstance(categories, list):
            categories = [str(c) for c in categories if isinstance(c, str)]

        extra = body.get("extra")
        if extra is not None and not isinstance(extra, str):
            extra = None

        model = (body.get("model") or "").strip() or None
        if not model:
            from matchmaker_lib import DEFAULT_MODEL

            model = DEFAULT_MODEL

        try:
            temperature = float(body.get("temperature", 0.25))
        except (TypeError, ValueError):
            temperature = 0.25

        raw_source_ids = body.get("source_ids")
        source_ids: list[str] | None = None
        if raw_source_ids is not None and isinstance(raw_source_ids, list):
            source_ids = [str(s).strip() for s in raw_source_ids if isinstance(s, str) and str(s).strip()]

        if path == "/api/plan-sequence":
            try:
                max_steps = int(body.get("max_steps", 20))
            except (TypeError, ValueError):
                max_steps = 20
            try:
                result = run_plan_sequence_request(
                    goal=goal,
                    categories=categories,
                    extra=extra,
                    api_key=api_key,
                    model_name=model,
                    temperature=temperature,
                    source_ids=source_ids,
                    max_steps=max_steps,
                )
            except Exception as e:  # noqa: BLE001
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(e)})
                return
            code = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
            self._json(code, result)
            return

        gh_base = (body.get("github_base") or "").strip()
        if not gh_base:
            gh_base = os.environ.get("AGENCY_GITHUB_BASE", "").strip() or (
                "https://github.com/msitarzewski/agency-agents/blob/main/"
            )

        try:
            result = run_match_request(
                goal=goal,
                categories=categories,
                extra=extra,
                api_key=api_key,
                model_name=model,
                temperature=temperature,
                github_base=gh_base,
                source_ids=source_ids,
            )
        except Exception as e:  # noqa: BLE001
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(e)})
            return

        code = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
        self._json(code, result)


def main() -> None:
    load_dotenv_repo()
    _gemini_ready = bool(_api_key_from_environment() or _read_first_nonempty_key_file())
    p = argparse.ArgumentParser(description="Agent Matchmaker local web server")
    p.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default 127.0.0.1)",
    )
    p.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port (default 8765)",
    )
    args = p.parse_args()

    try:
        ensure_catalog_exists()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        raise SystemExit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"Could not build catalog: {e}", file=sys.stderr)
        raise SystemExit(1) from e

    try:
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        if e.errno in (48, 98):  # EADDRINUSE on macOS / Linux
            print(
                f"Port {args.port} is already in use on {args.host}. "
                f"Stop the other process (e.g. `lsof -ti:{args.port} | xargs kill`) "
                f"or pass --port <n> to use a different port.",
                file=sys.stderr,
            )
            raise SystemExit(1) from e
        raise
    print(f"Serving {APP_DIR}")
    print(f"Open http://{args.host}:{args.port}/")
    if genai is None:
        pip_hint = (
            f"{sys.executable} -m pip install -r "
            f"{(REPO_ROOT / 'agent-matchmaker' / 'requirements-app.txt').as_posix()}"
        )
        print(
            "Google GenAI SDK (`google.genai`) not importable in this process — the UI will report “no sdk”.\n"
            f"  Interpreter: {sys.executable}\n"
            f"  Install: {pip_hint}\n"
            "  Or from repo root: ./scripts/run-agent-matchmaker.sh (uses .venv when present).\n"
            + (
                "  (API key already visible to this server from .env / env — only the SDK is missing.)\n"
                if _gemini_ready
                else ""
            ),
            file=sys.stderr,
            end="",
        )
    elif _gemini_ready:
        print("Gemini: API key found (.env, env, or .gemini_api_key) — enable “Use Gemini” in the UI.", file=sys.stderr)
    else:
        print(
            "Gemini: no key yet. Put your key in repo-root `.gemini_api_key` (one line) or set GEMINI_API_KEY in `.env`, "
            "then restart this server.",
            file=sys.stderr,
        )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
