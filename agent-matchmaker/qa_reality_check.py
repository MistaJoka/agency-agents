#!/usr/bin/env python3
"""
Reality check for the Agent Matchmaker: HTTP + marker evidence, optional Playwright PNGs.
Writes agent-matchmaker/qa-screenshots/test-results.json (and screenshots when available).

  python3 agent-matchmaker/qa_reality_check.py
  python3 agent-matchmaker/qa_reality_check.py --base-url http://127.0.0.1:9999
  python3 agent-matchmaker/qa_reality_check.py --http-only
  python3 agent-matchmaker/qa_reality_check.py --match-smoke
  python3 agent-matchmaker/qa_reality_check.py --match-smoke --match-smoke-strict
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
DEFAULT_OUT = APP_DIR / "qa-screenshots"
DEFAULT_BASE = "http://127.0.0.1:8765"


def _rel_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)

# Markers that prove the built UI is the matchmaker (not a stub page).
REQUIRED_SUBSTRINGS = [
    'id="main-content"',
    'id="btn-match"',
    "/api/match",
    "catalog.json",
]

# “Fantasy claim” terms from the old Laravel template — if these appear, flag for human review.
SPECulative_PATTERN = re.compile(
    r"luxury|premium\b|glassmorphism|morphism",
    re.IGNORECASE,
)


def _http_get(url: str, timeout: float = 30.0) -> tuple[int, bytes, float]:
    t0 = time.perf_counter()
    req = urllib.request.Request(url, headers={"User-Agent": "agent-matchmaker-qa/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = int(resp.status)
            body = resp.read()
    except urllib.error.HTTPError as e:
        code = int(e.code)
        body = e.read() if getattr(e, "fp", None) else b""
    ms = (time.perf_counter() - t0) * 1000.0
    return code, body, ms


def _http_post_json(
    url: str, payload: dict[str, Any], timeout: float = 120.0
) -> tuple[int, Any, float]:
    t0 = time.perf_counter()
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "agent-matchmaker-qa/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = int(resp.status)
            body = resp.read()
    except urllib.error.HTTPError as e:
        code = int(e.code)
        body = e.read() if getattr(e, "fp", None) else b""
    except (urllib.error.URLError, OSError) as e:
        ms = (time.perf_counter() - t0) * 1000.0
        return -1, {"_qa_error": str(e)}, ms
    ms = (time.perf_counter() - t0) * 1000.0
    try:
        parsed: Any = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        parsed = body.decode("utf-8", errors="replace")[:2000]
    return code, parsed, ms


def _qa_client_api_key() -> str:
    for name in ("MATCH_SMOKE_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        v = (os.environ.get(name) or "").strip()
        if v:
            return v
    return ""


def _check_match_smoke(base: str, health: dict[str, Any]) -> dict[str, Any]:
    """
    POST /api/match with a tiny goal. Skips when server has no Gemini stack or no resolvable API key.
    Set GEMINI_API_KEY (or MATCH_SMOKE_API_KEY) in the environment so the QA process can pass api_key
    in the JSON body when the server process has no key (server_gemini_key false).
    """
    url = base.rstrip("/") + "/api/match"
    if not health.get("ok"):
        return {
            "status": "skipped",
            "reason": "Health check failed; cannot run match smoke",
            "url": url,
        }

    hj = health.get("json") if isinstance(health.get("json"), dict) else {}
    if not hj.get("gemini_installed"):
        return {
            "status": "skipped",
            "reason": (
                "Server reports gemini_installed: false — use the same Python as "
                "`pip install -r agent-matchmaker/requirements-app.txt` when starting webapp.py"
            ),
            "url": url,
        }

    client_key = _qa_client_api_key()
    if not hj.get("server_gemini_key") and not client_key:
        return {
            "status": "skipped",
            "reason": (
                "No API key visible to the server (server_gemini_key false) and no "
                "GEMINI_API_KEY / GOOGLE_API_KEY / MATCH_SMOKE_API_KEY in this QA environment "
                "to send in the POST body"
            ),
            "url": url,
        }

    body: dict[str, Any] = {
        "goal": (
            "QA smoke test: pick exactly one agent from the catalog who fits "
            "writing internal developer documentation. One sentence summary only."
        ),
    }
    if client_key:
        body["api_key"] = client_key

    code, parsed, ms = _http_post_json(url, body)
    out = {
        "status": "error",
        "http_status": code,
        "latency_ms": round(ms, 2),
        "url": url,
    }
    if isinstance(parsed, dict) and "_qa_error" in parsed:
        out["status"] = "error"
        out["error"] = parsed["_qa_error"]
        return out

    excerpt: dict[str, Any] = {}
    if isinstance(parsed, dict):
        for k in ("ok", "error", "summary"):
            if k in parsed:
                excerpt[k] = parsed[k]
        if isinstance(parsed.get("matches"), list):
            excerpt["matches_n"] = len(parsed["matches"])
        out["response_excerpt"] = excerpt
    else:
        out["response_excerpt"] = str(parsed)[:800]

    if code == 200 and isinstance(parsed, dict) and parsed.get("ok") is True:
        matches = parsed.get("matches")
        n = len(matches) if isinstance(matches, list) else 0
        if n >= 1:
            out["status"] = "ok"
            out["matches_count"] = n
            return out
        out["status"] = "error"
        out["error"] = "HTTP 200 but ok!=true or no matches in response"
        return out

    if isinstance(parsed, dict):
        out["error"] = parsed.get("error", f"HTTP {code}")
    else:
        out["error"] = f"HTTP {code}, non-JSON body"
    out["status"] = "error"
    return out


def _check_health(base: str) -> dict[str, Any]:
    url = base.rstrip("/") + "/api/health"
    try:
        code, body, ms = _http_get(url)
    except (urllib.error.URLError, OSError) as e:
        return {
            "ok": False,
            "error": str(e),
            "latency_ms": None,
            "url": url,
        }
    out: dict[str, Any] = {
        "ok": code == 200,
        "status": code,
        "latency_ms": round(ms, 2),
        "url": url,
    }
    if code == 200:
        try:
            out["json"] = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            out["ok"] = False
            out["json_error"] = str(e)
    return out


def _check_index(base: str) -> dict[str, Any]:
    url = base.rstrip("/") + "/"
    try:
        code, body, ms = _http_get(url)
    except (urllib.error.URLError, OSError) as e:
        return {
            "ok": False,
            "error": str(e),
            "latency_ms": None,
            "url": url,
        }
    text = body.decode("utf-8", errors="replace")
    markers = {s: (s in text) for s in REQUIRED_SUBSTRINGS}
    markers_ok = all(s in text for s in REQUIRED_SUBSTRINGS)
    hits = SPECulative_PATTERN.findall(text)
    return {
        "ok": code == 200 and markers_ok,
        "status": code,
        "latency_ms": round(ms, 2),
        "size_bytes": len(body),
        "url": url,
        "markers": markers,
        "markers_all_present": markers_ok,
        "speculative_style_terms_hits": list(dict.fromkeys(hits)),
    }


def _screenshots_playwright(base: str, out_dir: Path) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "status": "skipped",
            "reason": "playwright not installed (pip install -r agent-matchmaker/requirements-qa.txt)",
        }

    out_dir.mkdir(parents=True, exist_ok=True)
    sizes = [
        ("responsive-desktop", 1920, 1080),
        ("responsive-short-desktop", 1280, 600),
        ("responsive-tablet", 768, 1024),
        ("responsive-tablet-portrait", 834, 400),
        ("responsive-mobile", 375, 667),
        ("responsive-mobile-narrow", 320, 568),
    ]
    per_view: dict[str, Any] = {}
    files: list[str] = []
    errors: list[str] = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:  # noqa: BLE001
            return {
                "status": "error",
                "error": f"chromium launch: {e}",
                "hint": "Run: playwright install chromium",
            }
        try:
            for name, w, h in sizes:
                page = browser.new_page(viewport={"width": w, "height": h})
                try:
                    t0 = time.perf_counter()
                    page.goto(
                        base.rstrip("/") + "/",
                        wait_until="load",
                        timeout=60000,
                    )
                    load_ms = (time.perf_counter() - t0) * 1000.0
                    overflow_ok = page.evaluate(
                        """() => {
                          const el = document.documentElement;
                          return el.scrollWidth <= el.clientWidth + 2;
                        }"""
                    )
                    path = out_dir / f"{name}.png"
                    page.screenshot(path=str(path), full_page=True)
                    rel = path.name
                    files.append(rel)
                    per_view[name] = {
                        "viewport": {"width": w, "height": h},
                        "load_to_paint_ms": round(load_ms, 2),
                        "no_horizontal_overflow": bool(overflow_ok),
                        "file": rel,
                    }
                    if not overflow_ok:
                        errors.append(f"{name}: horizontal overflow (scrollWidth > clientWidth)")
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{name}: {e}")
                finally:
                    page.close()
        finally:
            browser.close()

    d = _rel_to_repo(out_dir)
    if errors:
        return {
            "status": "partial" if files else "error",
            "dir": d,
            "files": files,
            "per_view": per_view,
            "errors": errors,
        }
    return {
        "status": "ok",
        "dir": d,
        "files": files,
        "per_view": per_view,
    }


def _verdict(checks: dict[str, Any], shots: dict[str, Any], http_only: bool) -> dict[str, Any]:
    health_ok = checks.get("api_health", {}).get("ok") is True
    index_ok = checks.get("index", {}).get("ok") is True
    base_pass = health_ok and index_ok

    shot_status = shots.get("status")
    if not base_pass:
        return {
            "production_readiness": "NEEDS_WORK",
            "reason": "HTTP health or index markers failed",
        }
    if http_only or shot_status == "skipped":
        return {
            "production_readiness": "NEEDS_WORK",
            "reason": "HTTP evidence only; add Playwright for visual proof (see requirements-qa.txt)",
            "http_checks": "pass",
        }
    if shot_status in ("ok", "partial") and not shots.get("errors"):
        return {
            "production_readiness": "EVIDENCE_OK",
            "reason": "Health, index, and screenshot run completed without errors",
        }
    if shot_status == "partial":
        return {
            "production_readiness": "NEEDS_WORK",
            "reason": "Partial screenshot failure",
        }
    if shot_status == "error":
        return {
            "production_readiness": "NEEDS_WORK",
            "reason": shots.get("error", "screenshot error"),
        }
    return {
        "production_readiness": "NEEDS_WORK",
        "reason": "unknown screenshot state",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Agent Matchmaker reality check")
    p.add_argument("--base-url", default=DEFAULT_BASE, help=f"Base URL (default {DEFAULT_BASE})")
    p.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory for test-results.json and PNGs",
    )
    p.add_argument(
        "--http-only",
        action="store_true",
        help="Skip Playwright; JSON + HTTP evidence only",
    )
    p.add_argument(
        "--match-smoke",
        action="store_true",
        help="POST /api/match with a minimal goal (needs Gemini on server + API key on server or in env)",
    )
    p.add_argument(
        "--match-smoke-strict",
        action="store_true",
        help="With --match-smoke: exit non-zero if smoke is skipped or errors (for CI full-stack checks)",
    )
    args = p.parse_args()
    if args.match_smoke_strict and not args.match_smoke:
        p.error("--match-smoke-strict requires --match-smoke")
    base = args.base_url.rstrip("/")

    checks = {
        "api_health": _check_health(base),
        "index": _check_index(base),
    }
    if args.http_only:
        shots: dict[str, Any] = {"status": "skipped", "reason": "--http-only"}
    else:
        shots = _screenshots_playwright(base, args.out_dir)

    match_smoke: dict[str, Any] | None = None
    if args.match_smoke:
        match_smoke = _check_match_smoke(base, checks["api_health"])

    verdict = _verdict(checks, shots, args.http_only or shots.get("status") == "skipped")
    if args.match_smoke and match_smoke is not None:
        st = match_smoke.get("status")
        if args.match_smoke_strict and st != "ok":
            verdict = {
                "production_readiness": "NEEDS_WORK",
                "reason": (
                    "match smoke "
                    + ("skipped: " if st == "skipped" else "failed: ")
                    + str(match_smoke.get("reason") or match_smoke.get("error") or st)
                ),
            }
        elif not args.match_smoke_strict and st == "error":
            verdict = {
                "production_readiness": "NEEDS_WORK",
                "reason": "match smoke failed: "
                + str(match_smoke.get("error") or match_smoke.get("http_status")),
            }

    result: dict[str, Any] = {
        "tool": "agent-matchmaker-qa",
        "base_url": base,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "screenshots": shots,
        "verdict": verdict,
    }
    if match_smoke is not None:
        result["match_smoke"] = match_smoke
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.out_dir / "test-results.json"
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["verdict"], indent=2, ensure_ascii=False))
    print(f"Wrote {out_json}", file=sys.stderr)

    ok = checks["api_health"].get("ok") and checks["index"].get("ok")
    if not ok:
        return 1
    if result["verdict"]["production_readiness"] == "NEEDS_WORK" and "HTTP evidence only" in str(
        result["verdict"].get("reason", "")
    ):
        # Still success exit for CI when only verifying HTTP; strict callers can inspect JSON.
        return 0
    if shots.get("status") == "error" and not args.http_only:
        return 1
    if shots.get("status") == "partial" and shots.get("errors"):
        return 1
    if args.match_smoke and match_smoke is not None:
        st = match_smoke.get("status")
        if args.match_smoke_strict and st != "ok":
            return 1
        if not args.match_smoke_strict and st == "error":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
