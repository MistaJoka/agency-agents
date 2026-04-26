"""
Shared logic for the Agent Matchmaker: catalog loading and Gemini calls.
Used by the local webapp (no Streamlit).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from functools import lru_cache
import sqlite3
from pathlib import Path

# Prefer `google-genai` (Gemini API). Legacy `google-generativeai` is deprecated.
try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover
    genai = None
    genai_types = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
CATALOG_PATH = APP_DIR / "catalog.json"
REGISTRY_DB_PATH = REPO_ROOT / "data" / "registry.sqlite"

GITHUB_BASE_DEFAULT = "https://github.com/msitarzewski/agency-agents/blob/main/"

DEFAULT_MODEL = "gemini-2.5-flash"
MODEL_CHOICES = (
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
)

DESC_MAX = 700

SYSTEM_INSTRUCTION = """You help users pick specialist AI agents from a fixed catalog (markdown agents in a git repo).
You receive JSON with the user's goal, optional category filters, optional notes, and a list of agents.
Each agent has: path (unique id), category, subcategory (folder under division / pack, or empty), name, description, vibe, emoji.

Rules:
- Recommend only agents that appear in the provided list. Use each agent's exact "path" string.
- Order recommendations by fit: most useful first.
- Return 6–12 agents unless the goal is extremely narrow (then fewer is OK).
- fit_score is 0–100 (integer) for how well the agent fits the stated goal.
- If coordination across multiple specialists or a full pipeline is implied, set suggest_agents_orchestrator true and name specialized/agents-orchestrator.md in orchestrator_path (it is in the catalog when present).
- Be practical: prefer fewer, stronger matches over padding the list.

Respond with JSON only, no markdown fences. Schema:
{
  "summary": "1–3 sentences for the user",
  "suggest_agents_orchestrator": false,
  "orchestrator_rationale": "string or null",
  "matches": [
    {
      "path": "category/file.md",
      "fit_score": 0,
      "why": "one or two sentences",
      "caveat": "string or null"
    }
  ]
}
"""

PLAN_SEQUENCE_INSTRUCTION = """You help users build an ordered sequence of specialist AI agents and skills for a goal.
You receive JSON with the user's goal, optional context, a list of catalog agents (each has path, name, description), and a list of registry items (each has id, name, description, item_type, source_path). Registry items are often skills or imported agents not in the main catalog.

Rules:
- Order steps from first to run → last. Each step is one agent (catalog path) OR one registry item (registry id).
- Use exact "path" strings for catalog agents and exact "id" strings for registry items — only from the provided lists.
- Return 4–15 steps unless the goal is very narrow (then fewer is OK). Do not pad with weak fits.
- Prefer a practical pipeline: research → design → build → verify when that fits the goal.
- If the goal needs coordination across many roles, you may start with a short discovery step then specialists.

Respond with JSON only, no markdown fences. Schema:
{
  "summary": "1–3 sentences explaining the overall sequence",
  "steps": [
    {
      "ref_id": "either agent path or registry id",
      "kind": "agent",
      "why_next": "one sentence — what this step produces for the next"
    }
  ]
}

For each step, set "kind" to "agent" when using a catalog path, or "skill" when using a registry item id (including imported agents stored only in registry).
"""


def _expand_env_value(val: str) -> str:
    """Expand ``$VAR`` / ``${VAR}`` when the whole value is a single reference (dotenv-style)."""
    m = re.fullmatch(r"\$\{([^}]+)\}", val)
    if m:
        return os.environ.get(m.group(1).strip(), "")
    m = re.fullmatch(r"\$([A-Za-z_][A-Za-z0-9_]*)", val)
    if m:
        return os.environ.get(m.group(1), "")
    return val


def _apply_env_file(path: Path) -> None:
    """Load KEY=VAL assignments into ``os.environ`` (last assignment wins). No python-dotenv required."""
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError:
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        quoted = len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'"
        if quoted:
            val = val[1:-1]
        else:
            val = re.sub(r"\s+#.*$", "", val).strip()
        val = _expand_env_value(val)
        os.environ[key] = val


def load_dotenv_repo() -> None:
    """Merge env files so a later file can set GEMINI_API_KEY if an earlier one left it blank.

    Order: repo ``.env`` → ``.env.local`` → ``agent-matchmaker/.env``. Later files
    override (``override=True``) so a key saved next to the webapp wins. Call from
    ``webapp.py`` before each match so edits apply without restarting the server.
    """
    candidates = (
        REPO_ROOT / ".env",
        REPO_ROOT / ".env.local",
        APP_DIR / ".env",
    )
    seen: set[Path] = set()
    for path in candidates:
        if not path.is_file():
            continue
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen:
            continue
        seen.add(key)
        if load_dotenv:
            load_dotenv(path, override=True)
        else:
            _apply_env_file(path)


def _build_catalog_script() -> Path:
    return REPO_ROOT / "scripts" / "build_agent_matchmaker.py"


def ensure_catalog_exists() -> None:
    if CATALOG_PATH.is_file():
        return
    script = _build_catalog_script()
    if not script.is_file():
        raise FileNotFoundError(
            f"Missing {CATALOG_PATH} and build script {script}. "
            "Restore scripts/build_agent_matchmaker.py or add catalog.json."
        )
    subprocess.run(
        [sys.executable, str(script)],
        cwd=str(REPO_ROOT),
        check=True,
    )
    load_catalog.cache_clear()


@lru_cache(maxsize=1)
def load_catalog() -> tuple[dict, ...]:
    if not CATALOG_PATH.is_file():
        raise FileNotFoundError(
            f"Missing {CATALOG_PATH}. Run: python3 scripts/build_agent_matchmaker.py"
        )
    raw = CATALOG_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("catalog.json must contain a JSON array")
    return tuple(data)


def compact_agents(rows: list[dict]) -> list[dict]:
    out = []
    for a in rows:
        desc = a.get("description") or ""
        if len(desc) > DESC_MAX:
            desc = desc[: DESC_MAX - 1] + "…"
        out.append(
            {
                "path": a["path"],
                "source_id": a.get("source_id") or "local-agency-agents",
                "category": a.get("category", ""),
                "name": a.get("name", ""),
                "description": desc,
                "vibe": a.get("vibe") or "",
                "emoji": a.get("emoji") or "",
            }
        )
    return out


def github_url(path: str, base: str) -> str:
    base = base.rstrip("/") + "/"
    return base + "/".join(quote_segment(p) for p in path.split("/"))


def quote_segment(seg: str) -> str:
    from urllib.parse import quote

    return quote(seg, safe="")


def local_url(path: str) -> str:
    try:
        return str((APP_DIR / ".." / path).resolve().as_uri())
    except Exception:
        return "../" + path


def call_gemini(
    api_key: str,
    model_name: str,
    user_payload: dict,
    temperature: float,
    *,
    system_instruction: str | None = None,
) -> dict:
    if genai is None or genai_types is None:
        raise RuntimeError("google-genai is not installed (pip install -r agent-matchmaker/requirements-app.txt)")
    client = genai.Client(api_key=api_key)
    prompt = (
        "User request payload (JSON):\n"
        + json.dumps(user_payload, ensure_ascii=False)
        + "\n\nReturn JSON matching the schema in your instructions."
    )
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction=system_instruction or SYSTEM_INSTRUCTION,
            temperature=temperature,
            response_mime_type="application/json",
        ),
    )
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise RuntimeError("No response from model (blocked or empty)")
    return json.loads(text)


def fetch_registry_metadata() -> list[dict]:
    """Lightweight rows from registry.sqlite (no raw markdown). Empty list if DB missing."""
    if not REGISTRY_DB_PATH.is_file():
        return []
    try:
        conn = sqlite3.connect(str(REGISTRY_DB_PATH))
    except OSError:
        return []
    try:
        cur = conn.execute(
            """
            SELECT id, source_id, item_type, name, category, description, source_path
            FROM registry_items
            ORDER BY source_id, source_path
            """
        )
        out: list[dict] = []
        for row in cur.fetchall():
            desc = row[5] or ""
            if len(desc) > DESC_MAX:
                desc = desc[: DESC_MAX - 1] + "…"
            out.append(
                {
                    "id": row[0],
                    "source_id": row[1] or "",
                    "item_type": row[2] or "",
                    "name": row[3] or "",
                    "category": row[4] or "",
                    "description": desc,
                    "source_path": row[6] or "",
                }
            )
        return out
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def compact_registry_for_plan(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "name": r.get("name", ""),
                "description": r.get("description", ""),
                "item_type": r.get("item_type", ""),
                "source_path": r.get("source_path", ""),
            }
        )
    return out


def validate_and_merge(
    parsed: dict,
    catalog_by_path: dict[str, dict],
) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    matches_in = parsed.get("matches") if isinstance(parsed, dict) else None
    if not isinstance(matches_in, list):
        warnings.append("Model returned no matches array; showing raw summary only.")
        return parsed, warnings

    merged: list[dict] = []
    seen: set[str] = set()
    for m in matches_in:
        if not isinstance(m, dict):
            continue
        path = m.get("path")
        if not isinstance(path, str) or not path.endswith(".md"):
            continue
        path = path.strip().lstrip("./")
        if path in seen:
            continue
        if path not in catalog_by_path:
            warnings.append(f"Ignored unknown path from model: {path}")
            continue
        seen.add(path)
        agent = catalog_by_path[path]
        merged.append(
            {
                "path": path,
                "fit_score": _clamp_int(m.get("fit_score"), 0, 100),
                "why": str(m.get("why", "")).strip(),
                "caveat": m.get("caveat"),
                "name": agent.get("name", path),
                "emoji": agent.get("emoji") or "📄",
                "vibe": agent.get("vibe") or "",
            }
        )

    parsed = dict(parsed)
    parsed["matches"] = merged
    return parsed, warnings


def validate_plan_sequence(
    parsed: dict,
    catalog_by_path: dict[str, dict],
    registry_by_id: dict[str, dict],
    *,
    max_steps: int = 20,
) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    steps_in = parsed.get("steps") if isinstance(parsed, dict) else None
    if not isinstance(steps_in, list):
        warnings.append("Model returned no steps array.")
        out = dict(parsed) if isinstance(parsed, dict) else {}
        out["steps"] = []
        return out, warnings

    merged: list[dict] = []
    seen: set[str] = set()
    for s in steps_in:
        if len(merged) >= max_steps:
            warnings.append(f"Truncated plan at {max_steps} steps.")
            break
        if not isinstance(s, dict):
            continue
        ref = s.get("ref_id")
        if not isinstance(ref, str):
            ref = s.get("refId")  # type: ignore[assignment]
        if not isinstance(ref, str) or not ref.strip():
            continue
        ref = ref.strip().lstrip("./")
        if ref in seen:
            continue

        why = str(s.get("why_next", "")).strip()

        if ref in catalog_by_path:
            agent = catalog_by_path[ref]
            merged.append(
                {
                    "ordinal": len(merged),
                    "kind": "agent",
                    "refId": ref,
                    "titleSnapshot": agent.get("name", ref),
                    "why_next": why,
                }
            )
            seen.add(ref)
            continue

        if ref in registry_by_id:
            row = registry_by_id[ref]
            itype = str(row.get("item_type") or "").lower()
            step_kind = "agent" if itype == "agent" else "skill"
            merged.append(
                {
                    "ordinal": len(merged),
                    "kind": step_kind,
                    "refId": ref,
                    "titleSnapshot": row.get("name") or ref,
                    "why_next": why,
                }
            )
            seen.add(ref)
            continue

        warnings.append(f"Ignored unknown ref_id from model: {ref}")

    out = dict(parsed) if isinstance(parsed, dict) else {}
    out["steps"] = merged
    return out, warnings


def _clamp_int(v: object, lo: int, hi: int) -> int:
    try:
        x = int(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, x))


def run_match_request(
    *,
    goal: str,
    categories: list[str] | None,
    extra: str | None,
    api_key: str,
    model_name: str,
    temperature: float,
    github_base: str,
    source_ids: list[str] | None = None,
) -> dict:
    """Run a full Gemini match; returns JSON-serializable result for the API."""
    catalog = list(load_catalog())
    by_path = {a["path"]: a for a in catalog if "path" in a}

    pool = catalog
    if categories:
        sel = set(categories)
        pool = [a for a in pool if a.get("category") in sel]
    if source_ids:
        allow = {str(s).strip() for s in source_ids if isinstance(s, str) and s.strip()}
        if allow:

            def _sid(a: dict) -> str:
                return (a.get("source_id") if isinstance(a.get("source_id"), str) else None) or "local-agency-agents"

            pool = [a for a in pool if _sid(a) in allow]
    if not pool:
        return {
            "ok": False,
            "error": "No agents in the current source and division filter. Widen filters or clear source scope.",
        }

    payload = {
        "user_goal": goal.strip(),
        "only_categories": categories if categories else None,
        "extra_context": (extra or "").strip() or None,
        "agents": compact_agents(pool),
        "agents_in_prompt_count": len(pool),
    }

    try:
        parsed = call_gemini(
            api_key.strip(),
            model_name,
            payload,
            float(temperature),
        )
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Model returned invalid JSON: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"Request failed: {e}"}

    merged, warns = validate_and_merge(parsed, by_path)
    return {
        "ok": True,
        "summary": merged.get("summary"),
        "suggest_agents_orchestrator": merged.get("suggest_agents_orchestrator"),
        "orchestrator_rationale": merged.get("orchestrator_rationale"),
        "matches": merged.get("matches") or [],
        "warnings": warns,
        "github_base": github_base.rstrip("/") + "/",
    }


REGISTRY_PLAN_CAP = 450


def run_plan_sequence_request(
    *,
    goal: str,
    categories: list[str] | None,
    extra: str | None,
    api_key: str,
    model_name: str,
    temperature: float,
    source_ids: list[str] | None = None,
    max_steps: int = 20,
) -> dict:
    """Gemini-ordered agent/skill sequence with hallucination guard on paths and registry ids."""
    catalog = list(load_catalog())
    by_path = {a["path"]: a for a in catalog if "path" in a}

    pool = catalog
    if categories:
        sel = set(categories)
        pool = [a for a in pool if a.get("category") in sel]
    if source_ids:
        allow = {str(s).strip() for s in source_ids if isinstance(s, str) and s.strip()}
        if allow:

            def _sid(a: dict) -> str:
                return (a.get("source_id") if isinstance(a.get("source_id"), str) else None) or "local-agency-agents"

            pool = [a for a in pool if _sid(a) in allow]
    if not pool:
        return {
            "ok": False,
            "error": "No agents in the current source and division filter. Widen filters or clear source scope.",
        }

    reg_rows = fetch_registry_metadata()
    pre_warns: list[str] = []
    if source_ids:
        allow = {str(s).strip() for s in source_ids if isinstance(s, str) and s.strip()}
        if allow:
            reg_rows = [r for r in reg_rows if r.get("source_id") in allow]
    if len(reg_rows) > REGISTRY_PLAN_CAP:
        reg_rows = reg_rows[:REGISTRY_PLAN_CAP]
        pre_warns.append(f"Registry listing truncated to {REGISTRY_PLAN_CAP} items for the model prompt.")

    registry_by_id = {r["id"]: r for r in reg_rows if r.get("id")}

    payload = {
        "user_goal": goal.strip(),
        "only_categories": categories if categories else None,
        "extra_context": (extra or "").strip() or None,
        "agents": compact_agents(pool),
        "agents_in_prompt_count": len(pool),
        "registry_items": compact_registry_for_plan(reg_rows),
        "registry_in_prompt_count": len(reg_rows),
    }

    try:
        ms = int(max_steps)
    except (TypeError, ValueError):
        ms = 20
    ms = max(4, min(30, ms))

    try:
        parsed = call_gemini(
            api_key.strip(),
            model_name,
            payload,
            float(temperature),
            system_instruction=PLAN_SEQUENCE_INSTRUCTION,
        )
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Model returned invalid JSON: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"Request failed: {e}"}

    merged, warns = validate_plan_sequence(parsed, by_path, registry_by_id, max_steps=ms)
    all_warns = pre_warns + warns
    return {
        "ok": True,
        "summary": merged.get("summary"),
        "steps": merged.get("steps") or [],
        "warnings": all_warns,
    }
