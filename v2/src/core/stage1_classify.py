#!/usr/bin/env python3
"""v2 Stage 1: Classify all deduplicated survey questions through USAi harness pool.

Confirmation run. Mirrors v1's classification artifact exactly except for
model identity. Everything that affects results lives in v2/config/stage1.yaml.

Run from v2/ directory:
    python src/core/stage1_classify.py                # initial run
    python src/core/stage1_classify.py --retry-failed # rerun only failed batches

Retry mode:
    Reads the most recent checkpoint files. For each rater, identifies failed
    task IDs (request failures, parse failures, and length truncations).
    Re-runs ONLY those batches with batch_size halved (10 -> 5) and max_tokens
    doubled. Successes append to the existing JSONL. Checkpoint is updated.

What this script does NOT do:
    - Hardcode any model name, max_tokens, temperature, or count.
    - Call vendor SDKs directly. All LLM calls go through usai_harness.
    - Modify anything outside v2/.
    - Implement its own retry/concurrency. The harness owns that.
    - Drop records based on taxonomy validation. v1 didn't, neither does v2.
    - Tolerate partial success. 100% or FAIL — failures get inspected.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

# _smoke is a sibling module in src/core/. Guarantee it is importable no
# matter how this script is launched.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _smoke  # noqa: E402


# =============================================================================
# CONFIG LOADING
# =============================================================================

CONFIG_PATH = Path("config/stage1.yaml")
THIS_SCRIPT = Path(__file__).resolve()


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        die(f"Config not found at {CONFIG_PATH.resolve()}. "
            f"Run from the v2/ directory.")
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    required_top = {"raters", "pipeline", "preflight", "data", "expected",
                    "output", "harness"}
    missing = required_top - set(cfg.keys())
    if missing:
        die(f"Config missing required top-level keys: {missing}")

    if set(cfg["raters"].keys()) != {"rater_a", "rater_b"}:
        die(f"Config 'raters' must define exactly rater_a and rater_b. "
            f"Got: {set(cfg['raters'].keys())}")

    return cfg


# =============================================================================
# DATA LOADING
# =============================================================================

def load_taxonomy(cfg: dict[str, Any]) -> dict:
    path = Path(cfg["data"]["taxonomy_json"])
    if not path.exists():
        die(f"Taxonomy file not found at {path.resolve()}")
    with open(path) as f:
        data = json.load(f)
    root_key = cfg["data"]["taxonomy_root_key"]
    if root_key not in data:
        die(f"Taxonomy JSON missing top-level key {root_key!r}")
    return data[root_key]


def load_questions(cfg: dict[str, Any]) -> pd.DataFrame:
    """Load the questions CSV. Iterates ALL rows, including NaN-question rows.

    Mirrors v1 (src/core/categorize_claude.py:load_questions) byte-for-byte:
      - Read CSV.
      - For each row (NO filtering), take the first non-null survey-column
        name as 'survey'.
      - Build records: {id: int(idx), survey, question}.
      - 'id' is the raw iterrows() index — the CSV row number. NaN-question
        rows ARE included; the model decides what to do with them at
        inference time. v1 sends them too.

    The verification anchor below asserts on ROWS ITERATED (= CSV row count),
    NOT records-eventually-written. v1's results_claude.jsonl has 6,946
    records for 6,987 input rows because the model skips NaN-question rows
    in its responses. See cc_tasks/2026-05-06_v2_stage1_load_logic_fix.md.
    """
    path = Path(cfg["data"]["questions_csv"])
    if not path.exists():
        die(f"Questions CSV not found at {path.resolve()}")

    df = pd.read_csv(path)
    records = []
    for idx, row in df.iterrows():
        question = row["Question"]
        surveys = [c for c in df.columns if c != "Question" and pd.notna(row[c])]
        records.append({
            "id": int(idx),
            "survey": surveys[0] if surveys else "Unknown",
            "question": question,
        })
    out = pd.DataFrame(records)

    expected = cfg["expected"]["question_count"]
    if len(out) != expected:
        die(f"Row count mismatch: iterated {len(out)} CSV rows, config expects "
            f"{expected}. Either the CSV changed or expected.question_count is "
            f"stale. Stop and investigate.")

    return out


# =============================================================================
# PROMPT (lifted byte-identical from v1 categorize_claude.py)
# =============================================================================

def create_prompt(batch: list[dict], taxonomy: dict) -> str:
    return f"""You are categorizing federal survey questions using the official U.S. Census Bureau taxonomy.

TAXONOMY:
{json.dumps(taxonomy, indent=2)}

TASK:
For each question below, assign:
1. Primary concept: The most relevant Topic and Subtopic
2. Secondary concepts: 0-3 additional relevant subtopics (if applicable)
3. Confidence: 0-1 score for primary assignment
4. Reasoning: Brief explanation (1-2 sentences)

QUESTIONS TO CATEGORIZE:
{json.dumps(batch, indent=2)}

Return a JSON array with one object per question, in the same order. Format:
[
  {{
    "id": 0,
    "primary_topic": "Economic",
    "primary_subtopic": "Income",
    "confidence": 0.95,
    "secondary_concepts": [
      {{"topic": "Economic", "subtopic": "Employment Status"}},
      {{"topic": "Demographic", "subtopic": "Age"}}
    ],
    "reasoning": "Question asks about household income sources."
  }},
  ...
]

Return ONLY the JSON array, no other text."""


# =============================================================================
# RESPONSE PARSING
# =============================================================================
# Combines v1's two parsers (claude + openai) into one tolerant parser. Strictly
# more permissive than either v1 parser, so anything v1 could parse, v2 can.

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def parse_response(content: str) -> tuple[list[dict] | None, str | None]:
    if not isinstance(content, str) or not content.strip():
        return None, "empty content"

    text = content
    if text.startswith("```json"):
        text = text.split("```json", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    text = _CONTROL_CHARS.sub("", text)

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                result = json.loads(text[start:end + 1])
            except json.JSONDecodeError as e:
                return None, f"json decode failed even after bracket recovery: {e}"
        else:
            return None, "json decode failed and no bracket recovery possible"

    if not isinstance(result, list):
        if isinstance(result, dict) and "categorizations" in result:
            result = result["categorizations"]
        elif isinstance(result, dict) and len(result) == 1:
            result = list(result.values())[0]
        else:
            return None, f"response is {type(result).__name__}, expected list"

    if not isinstance(result, list):
        return None, f"unwrapped value is {type(result).__name__}, not a list"

    return result, None


def extract_response_text(harness_response: dict) -> str | None:
    if not isinstance(harness_response, dict):
        return None
    choices = harness_response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return None
    return message.get("content")


def extract_finish_reason(harness_response: dict) -> str | None:
    if not isinstance(harness_response, dict):
        return None
    choices = harness_response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    return choices[0].get("finish_reason")


# =============================================================================
# UTILITIES
# =============================================================================

def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_")


def chunk(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def ensure_dirs(cfg: dict[str, Any], smoke: bool = False) -> dict[str, Path]:
    # A --smoke run redirects the whole output tree under output_dir/smoke/ so
    # it never clobbers real results, checkpoints, or raw responses. The root
    # is derived from cfg; nothing is hardcoded.
    out_root = (smoke_output_dir(cfg) if smoke
                else Path(cfg["output"]["output_dir"]))
    raw_dir = out_root / cfg["output"]["raw_responses_subdir"]
    ckpt_dir = out_root / cfg["output"]["checkpoints_subdir"]
    out_root.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    return {"out_root": out_root, "raw_dir": raw_dir, "ckpt_dir": ckpt_dir}


def looks_like_unknown_model_error(harness_response: dict) -> bool:
    if not isinstance(harness_response, dict):
        return False
    body = harness_response.get("error_body")
    if not isinstance(body, str):
        return False
    body_lower = body.lower()
    needles = ("model not found", "model_not_found", "unknown model",
               "invalid model", "does not exist")
    return any(n in body_lower for n in needles)


def parse_batch_index(task_id: str) -> int | None:
    """Extract the integer batch index from a task_id like 'stage1_rater_a_b0042'
    or 'stage1_rater_a_b0042_r0'. Returns None if it doesn't match."""
    m = re.search(r"_b(\d{4,})(?:_r\d+)?$", task_id)
    if not m:
        return None
    return int(m.group(1))


def _count_jsonl_records(path_str: str | None) -> int:
    """Return the number of lines in a JSONL file, or 0 if it doesn't exist.

    Used by the retry-mode run report. The retry-pass outcome's record count
    reflects only what was written during THIS pass; the file on disk is the
    cumulative truth across initial + N retry passes.
    """
    if not path_str:
        return 0
    p = Path(path_str)
    if not p.exists():
        return 0
    with open(p) as f:
        return sum(1 for _ in f)


def _read_jsonl_keys(path_str: str | Path | None) -> tuple[int, list[Any]]:
    """Return (line_count, [id per line]) for the round-trip check.

    Counts every written line. `written` is the raw line count; the silent-drop
    bug writes lines whose `id` is null/missing, which then vanish when the
    downstream merge keys on `id`. `key_values` carries those ids so
    check_roundtrip can flag null/empty keys.
    """
    p = Path(path_str) if path_str else None
    n = 0
    keys: list[Any] = []
    if not p or not p.exists():
        return n, keys
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                keys.append(json.loads(line).get("id"))
            except json.JSONDecodeError:
                keys.append(None)
    return n, keys


def _load_jsonl_ids(path_str: str | Path | None) -> set:
    """Return the set of non-null `id` values readable from a JSONL file.

    Mirrors how a downstream consumer keys records on `id`; its size is the
    `loaded` count for the round-trip invariant (loaded == written means no
    record was dropped on read-back due to a missing/duplicate key)."""
    p = Path(path_str) if path_str else None
    out: set = set()
    if not p or not p.exists():
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = rec.get("id")
            if rid is not None:
                out.add(rid)
    return out


def smoke_output_dir(cfg: dict[str, Any]) -> Path:
    """Where a --smoke run writes its working files. Kept under a dedicated
    smoke/ subdir of the stage1 output_dir so it never clobbers real results."""
    return Path(cfg["output"]["output_dir"]) / "smoke"


def smoke_stamp_path(cfg: dict[str, Any]) -> Path:
    """Stage-level smoke-pass stamp. The gate is keyed on the script source
    hash (current code), not on any single rater, so the stamp lives once
    under the smoke/ subdir."""
    return smoke_output_dir(cfg) / "smoke_pass.json"


def _wipe_rater_output(rater_label: str, cfg: dict, dirs: dict[str, Path]) -> None:
    """Delete a rater's JSONL, raw_responses subdir, and checkpoint.

    Used in --rater single-rater initial mode to guarantee no stale data
    (mismatched task_ids, half-written records, old checkpoint schema) leaks
    into a fresh run. The both-rater path keeps its existing behavior of only
    truncating the JSONL at the start of `run_rater_initial`.
    """
    pattern = cfg["output"]["results_filename_pattern"].format(
        rater_label=rater_label, model_slug="*",
    )
    jsonl_paths = sorted(dirs["out_root"].glob(pattern))
    raw_subdir = dirs["raw_dir"] / rater_label
    ckpt_path = dirs["ckpt_dir"] / f"{rater_label}.json"

    wiped: list[str] = []
    for p in jsonl_paths:
        p.unlink()
        wiped.append(str(p))
    if raw_subdir.exists():
        shutil.rmtree(raw_subdir)
        wiped.append(str(raw_subdir))
    if ckpt_path.exists():
        ckpt_path.unlink()
        wiped.append(str(ckpt_path))

    if wiped:
        print(f"[{rater_label}] Wiped stale output before fresh run:")
        for w in wiped:
            print(f"  - {w}")
    else:
        print(f"[{rater_label}] No prior output to wipe.")


def _build_prior_outcome(
    rater_label: str, cfg: dict, dirs: dict[str, Path],
) -> dict:
    """Synthesize a run-report outcome for a rater whose state lives on disk
    from a prior session. Used in --rater mode so the combined report still
    reflects the rater that wasn't executed this session."""
    rater_cfg = cfg["raters"][rater_label]
    default_max_tokens = cfg["pipeline"]["max_tokens"]
    default_batch_size = cfg["pipeline"]["batch_size"]
    batch_size = rater_cfg.get("batch_size", default_batch_size)
    max_tokens = rater_cfg.get("max_tokens", default_max_tokens)

    ckpt_path = dirs["ckpt_dir"] / f"{rater_label}.json"
    if not ckpt_path.exists():
        return {
            "rater_label": rater_label,
            "mode": "not_run",
            "model_requested": rater_cfg["model"],
            "model_slug": slugify(rater_cfg["model"]),
            "served_models": [],
            "wall_seconds": 0.0,
            "tasks_total": 0,
            "request_failed": [],
            "parse_failed": [],
            "truncated_and_unparseable": [],
            "succeeded_task_ids": [],
            "records_written": 0,
            "results_path": "",
            "unknown_model_seen": False,
            "summaries": [],
            "batch_size": batch_size,
            "max_tokens": max_tokens,
        }

    ckpt = json.loads(ckpt_path.read_text())
    results_path = ckpt.get("results_path", "")
    jsonl_count = _count_jsonl_records(results_path)
    return {
        "rater_label": rater_label,
        "mode": "prior_run",
        "model_requested": ckpt.get("model_requested", rater_cfg["model"]),
        "model_slug": slugify(ckpt.get("model_requested", rater_cfg["model"])),
        "served_models": ckpt.get("served_models", []),
        "wall_seconds": ckpt.get("wall_seconds_initial", 0.0),
        "tasks_total": (
            len(ckpt.get("succeeded_task_ids", []))
            + len(ckpt.get("request_failed", []))
            + len(ckpt.get("parse_failed", []))
            + len(ckpt.get("truncated_and_unparseable", []))
        ),
        "request_failed": ckpt.get("request_failed", []),
        "parse_failed": ckpt.get("parse_failed", []),
        "truncated_and_unparseable": ckpt.get("truncated_and_unparseable", []),
        "succeeded_task_ids": ckpt.get("succeeded_task_ids", []),
        "records_written": jsonl_count,
        "results_path": results_path,
        "unknown_model_seen": False,
        "summaries": [],
        "batch_size": batch_size,
        "max_tokens": max_tokens,
    }


# =============================================================================
# PER-TASK CALLBACK (writes raw response, JSONL records, and live checkpoint
# the moment each task completes — replaces the old post-batch loop)
# =============================================================================

def _fmt_time(seconds: float) -> str:
    """Format a duration as Hh:MM:SS, MM:SS, or NNs."""
    if seconds < 60:
        return f"{int(seconds)}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}:{s:02d}"
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


def make_result_handler(
    *,
    rater_label: str,
    raw_subdir: Path,
    results_path: Path,
    checkpoint_path: Path,
    tracker: dict,
    expected_ids_by_task: dict[str, list[int]] | None = None,
):
    """Build a per-task progress callback for `client.batch(progress=...)`.

    Each completed task fires this with a `ProgressEvent` whose `.result` is
    the task's `BatchResult`. The callback persists the raw response, parses
    and appends records to the JSONL, prints a one-line progress update, and
    rewrites the checkpoint file. Per-task summaries accumulate in
    `tracker["summaries"]` for downstream report rendering.

    `expected_ids_by_task` maps task_id → ordered list of question IDs sent
    in that task's prompt. When provided, returned records' `id` fields are
    validated against the expected IDs. Same-count-but-wrong-IDs is treated
    as a positional ordering error and remapped (the prompt requires same
    order, so the i-th returned record corresponds to the i-th sent question
    regardless of what `id` the model wrote). Count mismatches are treated
    as parse failures — the data can't be safely recovered.
    """
    raw_subdir.mkdir(parents=True, exist_ok=True)

    def handler(event) -> None:
        r = event.result

        # 1. Persist raw response (every task, success or fail).
        raw_path = raw_subdir / f"{r.task_id}.json"
        raw_path.write_text(json.dumps({
            "task_id": r.task_id,
            "success": r.success,
            "status_code": r.status_code,
            "latency_ms": r.latency_ms,
            "error": r.error,
            "response": r.response,
        }, indent=2, default=str))

        # 2. Build per-task summary (same shape downstream report consumes).
        summary = {
            "task_id": r.task_id,
            "outcome": None,
            "status_code": r.status_code,
            "error": r.error,
            "error_body": None,
            "finish_reason": None,
            "served_model": None,
            "parse_error": None,
            "response_text_snippet": None,
            "records": 0,
            "unknown_model": False,
        }

        if not r.success:
            summary["outcome"] = "request_failed"
            if isinstance(r.response, dict):
                summary["error_body"] = r.response.get("error_body")
            if looks_like_unknown_model_error(r.response or {}):
                summary["unknown_model"] = True
                tracker["unknown_model"] = True
            tracker["request_failed"].append(r.task_id)
        else:
            response = r.response or {}
            summary["served_model"] = (
                response.get("model") if isinstance(response, dict) else None
            )
            if summary["served_model"]:
                tracker["served_models"].add(summary["served_model"])
            summary["finish_reason"] = extract_finish_reason(response)

            text = extract_response_text(response) or ""
            if text:
                summary["response_text_snippet"] = text[:200]

            records, perr = parse_response(text)
            if records is None:
                summary["parse_error"] = perr
                if summary["finish_reason"] == "length":
                    summary["outcome"] = "truncated_and_unparseable"
                    tracker["truncated"].append(r.task_id)
                else:
                    summary["outcome"] = "parse_failed"
                    tracker["parse_failed"].append(r.task_id)
            else:
                # ID validation. The prompt sends each question with its CSV
                # row index as `id` and demands "Return a JSON array with one
                # object per question, in the same order." Some models (seen
                # with Gemini) ignore the sent IDs and emit their own internal
                # numbering. With same count + same order, the records are
                # still valid — overwrite the model's IDs positionally. Count
                # mismatches mean we can't recover the mapping; fail the task.
                expected = (
                    expected_ids_by_task.get(r.task_id)
                    if expected_ids_by_task else None
                )
                returned_ids = [rec.get("id") for rec in records]
                if expected is not None and returned_ids != expected:
                    if len(records) == len(expected):
                        for rec, eid in zip(records, expected):
                            rec["id"] = eid
                        summary["id_remapped"] = True
                        summary["original_ids"] = returned_ids
                    else:
                        summary["outcome"] = "parse_failed"
                        summary["parse_error"] = (
                            f"ID count mismatch: sent {len(expected)} "
                            f"questions, got {len(records)} records back. "
                            f"Expected IDs: {expected}, got: {returned_ids}"
                        )
                        tracker["parse_failed"].append(r.task_id)

                if summary["outcome"] is None:
                    with open(results_path, "a") as f:
                        for rec in records:
                            f.write(json.dumps(rec) + "\n")
                    summary["records"] = len(records)
                    summary["outcome"] = "success"
                    tracker["records_written"] += len(records)
                    tracker["succeeded"].append(r.task_id)

        tracker["summaries"].append(summary)

        # 3. One-line progress with data-write confirmation.
        pct = (event.completed / event.total * 100.0) if event.total else 0.0
        eta = (
            (event.elapsed_seconds / event.completed)
            * (event.total - event.completed)
            if event.completed > 0
            else 0.0
        )
        status = "OK" if summary["outcome"] == "success" else "FAIL"
        ts = datetime.now().strftime("%H:%M:%S")
        print(
            f"[{ts}] [{rater_label}] {event.completed}/{event.total} "
            f"({pct:.1f}%)  elapsed {_fmt_time(event.elapsed_seconds)}  "
            f"eta {_fmt_time(eta)}  {status}: {r.task_id}",
            flush=True,
        )

        # 4. Rewrite live checkpoint after every task — same key names as
        #    finalize_rater_outcome writes, so retry logic can read either.
        checkpoint_path.write_text(json.dumps({
            "rater_label": rater_label,
            "completed": event.completed,
            "total": event.total,
            "records_written": tracker["records_written"],
            "succeeded_task_ids": list(tracker["succeeded"]),
            "request_failed": list(tracker["request_failed"]),
            "parse_failed": list(tracker["parse_failed"]),
            "truncated_and_unparseable": list(tracker["truncated"]),
            "served_models": sorted(tracker["served_models"]),
        }, indent=2))

    return handler


def _empty_tracker() -> dict:
    """Mutable accumulator for the result handler. One per rater per pass."""
    return {
        "summaries": [],
        "succeeded": [],
        "request_failed": [],
        "parse_failed": [],
        "truncated": [],
        "served_models": set(),
        "unknown_model": False,
        "records_written": 0,
    }


# =============================================================================
# PRE-FLIGHT
# =============================================================================

async def preflight(client, cfg: dict[str, Any], dirs: dict[str, Path]) -> dict:
    pf_cfg = cfg["preflight"]
    if not pf_cfg.get("enabled", True):
        return {"skipped": True}

    print("Pre-flight: probing harness default model...")
    t0 = time.monotonic()
    response = await client.complete(
        messages=[{"role": "user", "content": pf_cfg["prompt"]}],
        max_tokens=pf_cfg["max_tokens"],
        task_id="stage1_preflight",
    )
    dt_ms = (time.monotonic() - t0) * 1000.0

    text = extract_response_text(response)
    finish = extract_finish_reason(response)
    served_model = response.get("model") if isinstance(response, dict) else None
    error_body = response.get("error_body") if isinstance(response, dict) else None

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "default_model_requested": client.config.default_model.name,
        "served_model": served_model,
        "latency_ms": dt_ms,
        "finish_reason": finish,
        "response_text": text,
        "error_body": error_body,
    }

    pf_path = dirs["out_root"] / cfg["output"]["preflight_report"]
    pf_path.write_text(json.dumps(record, indent=2))

    if not text or error_body:
        die(f"Pre-flight failed. See {pf_path}. error_body={error_body!r}")

    print(f"Pre-flight OK: served by {served_model!r} in {dt_ms:.0f}ms")
    return record


# =============================================================================
# INITIAL RUN
# =============================================================================

async def run_rater_initial(
    *,
    client,
    rater_label: str,
    rater_cfg: dict,
    questions: list[dict],
    taxonomy: dict,
    cfg: dict[str, Any],
    dirs: dict[str, Path],
    smoke: bool = False,
) -> dict:
    model = rater_cfg["model"]
    temperature = rater_cfg["temperature"]
    # Per-rater overrides win over pipeline defaults. Lets one verbose model
    # (e.g., gemini) run with larger max_tokens / smaller batches without
    # forcing the entire pipeline to those values.
    default_max_tokens = cfg["pipeline"]["max_tokens"]
    default_batch_size = cfg["pipeline"]["batch_size"]
    max_tokens = rater_cfg.get("max_tokens", default_max_tokens)
    batch_size = rater_cfg.get("batch_size", default_batch_size)
    job_name = f"{cfg['pipeline']['job_name_prefix']}_{rater_label}"

    if not client.config.has_model(model):
        die(f"Rater {rater_label}: model {model!r} not in v2/usai_harness.yaml pool. "
            f"Pool: {[m.name for m in client.config.models]}. "
            f"Fix v2/config/stage1.yaml or v2/usai_harness.yaml — do not hardcode in script.")

    batches = chunk(questions, batch_size)
    # Batch count assertion only applies when the rater uses the default
    # batch_size. With a per-rater override, batch count is derived and the
    # config.expected.batch_count value reflects the default-config layout
    # only. The question_count assertion in load_questions() still catches
    # data drift.
    # The expected-batch-count assertion only makes sense for a full run over
    # all questions. A smoke run deliberately submits SMOKE_N questions, so the
    # batch count is tiny by design; skip the assertion there.
    if batch_size == default_batch_size and not smoke:
        expected_batches = cfg["expected"]["batch_count"]
        if len(batches) != expected_batches:
            die(f"Rater {rater_label}: built {len(batches)} batches, config expects {expected_batches}.")

    tasks = [
        {
            "task_id": f"stage1_{rater_label}_b{i:04d}",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": create_prompt(batch, taxonomy)}],
            "_expected_ids": [int(q["id"]) for q in batch],
        }
        for i, batch in enumerate(batches)
    ]
    expected_ids_by_task = {t["task_id"]: t["_expected_ids"] for t in tasks}

    # Output paths — fresh JSONL for an initial run.
    model_slug = slugify(model)
    results_path = dirs["out_root"] / cfg["output"]["results_filename_pattern"].format(
        rater_label=rater_label, model_slug=model_slug,
    )
    if results_path.exists():
        results_path.unlink()
    raw_subdir = dirs["raw_dir"] / rater_label
    checkpoint_path = dirs["ckpt_dir"] / f"{rater_label}.json"

    # Per-task callback writes raw_response/, JSONL records, and the live
    # checkpoint as each task completes. No post-batch loop.
    tracker = _empty_tracker()
    handler = make_result_handler(
        rater_label=rater_label,
        raw_subdir=raw_subdir,
        results_path=results_path,
        checkpoint_path=checkpoint_path,
        tracker=tracker,
        expected_ids_by_task=expected_ids_by_task,
    )

    # Strip bookkeeping fields (anything `_`-prefixed) before submitting.
    api_tasks = [
        {k: v for k, v in t.items() if not k.startswith("_")}
        for t in tasks
    ]

    print(f"\n[{rater_label}] Submitting {len(tasks)} batch tasks against {model!r}...")
    t0 = time.monotonic()
    await client.batch(api_tasks, job_name=job_name, progress=handler)
    wall_s = time.monotonic() - t0
    print(f"[{rater_label}] Batch returned in {wall_s:.1f}s")

    # Sort accumulated summaries by task_id for stable downstream order.
    tracker["summaries"].sort(key=lambda s: s["task_id"])

    outcome = finalize_rater_outcome(
        rater_label=rater_label, model=model, model_slug=model_slug,
        summaries=tracker["summaries"], wall_s=wall_s, results_path=results_path,
        dirs=dirs, mode="initial",
    )
    outcome["batch_size"] = batch_size
    outcome["max_tokens"] = max_tokens
    # `requested` is the number of questions submitted for this rater (one
    # record expected back per question). The round-trip gate compares this
    # against JSONL lines written and ids read back.
    outcome["requested"] = len(questions)
    return outcome


# =============================================================================
# RETRY RUN
# =============================================================================

async def run_rater_retry(
    *,
    client,
    rater_label: str,
    rater_cfg: dict,
    questions: list[dict],
    taxonomy: dict,
    cfg: dict[str, Any],
    dirs: dict[str, Path],
) -> dict:
    """Retry only previously-failed batches, with batch_size halved and
    max_tokens doubled. Appends to the existing JSONL. Updates checkpoint."""
    model = rater_cfg["model"]
    temperature = rater_cfg["temperature"]
    base_max_tokens = cfg["pipeline"]["max_tokens"]
    base_batch_size = cfg["pipeline"]["batch_size"]
    job_name = f"{cfg['pipeline']['job_name_prefix']}_{rater_label}_retry"

    if not client.config.has_model(model):
        die(f"Rater {rater_label}: model {model!r} not in v2/usai_harness.yaml pool.")

    # Load previous checkpoint to find failed batch indices.
    ckpt_path = dirs["ckpt_dir"] / f"{rater_label}.json"
    if not ckpt_path.exists():
        die(f"Rater {rater_label}: no checkpoint at {ckpt_path}. "
            f"Run the initial pass before --retry-failed.")
    ckpt = json.loads(ckpt_path.read_text())

    # Escalate from the previous retry's params, not the base config. Repeated
    # --retry-failed calls must keep halving batch_size and doubling max_tokens
    # instead of replaying the same 10→5 / 4096→8192 step every time.
    # First retry: prev=base. Subsequent retries: prev=last_retry_*.
    prev_batch_size = ckpt.get("last_retry_batch_size", base_batch_size)
    prev_max_tokens = ckpt.get("last_retry_max_tokens", base_max_tokens)
    retry_batch_size = max(1, prev_batch_size // 2)
    retry_max_tokens = prev_max_tokens * 2

    failed_task_ids: list[str] = sorted(set(
        ckpt.get("request_failed", []) +
        ckpt.get("parse_failed", []) +
        ckpt.get("truncated_and_unparseable", [])
    ))

    # batch_size=1 already failed: a single question that won't fit at the
    # previous max_tokens won't fit at 2x either (the response would still
    # truncate; we'd just truncate further along). Surface and stop.
    if prev_batch_size == 1 and failed_task_ids:
        sample = ", ".join(failed_task_ids[:5])
        more = "..." if len(failed_task_ids) > 5 else ""
        die(f"Rater {rater_label}: batch_size=1 and still failing. These "
            f"{len(failed_task_ids)} task(s) cannot be classified at any "
            f"token budget tried (last attempt: max_tokens={prev_max_tokens}). "
            f"Manual review required. See output/stage1/raw_responses/"
            f"{rater_label}/ for: {sample}{more}")

    # Detect "never-ran" tasks — submitted but interrupted before returning.
    # Any task ID in the expected set that is NOT in succeeded/failed lists
    # gets re-submitted as a full original-shape task (not halved).
    expected_task_ids = {
        f"stage1_{rater_label}_b{i:04d}"
        for i in range(cfg["expected"]["batch_count"])
    }
    accounted_for = set(ckpt.get("succeeded_task_ids", [])) | set(failed_task_ids)
    never_ran_task_ids = sorted(expected_task_ids - accounted_for)

    if not failed_task_ids and not never_ran_task_ids:
        print(f"[{rater_label}] No failed or never-ran batches to retry. Skipping.")
        return {
            "rater_label": rater_label, "model_requested": model,
            "model_slug": slugify(model), "wall_seconds": 0.0,
            "mode": "retry_noop",
            "tasks_total": 0, "request_failed": [], "parse_failed": [],
            "truncated_and_unparseable": [], "succeeded_task_ids": [],
            "records_written_this_pass": 0,
            "served_models": ckpt.get("served_models", []),
            "results_path": ckpt.get("results_path", ""),
            "unknown_model_seen": False,
            "summaries": [],
            "originals_attempted": [],
            "originals_recovered": [],
            "originals_still_failing": [],
            "never_ran_attempted": [],
            "never_ran_succeeded": [],
            "never_ran_still_failing": [],
        }

    original_batches = chunk(questions, base_batch_size)

    # Halves of previously-failed originals (doubled max_tokens, halved batch).
    retry_tasks: list[dict] = []
    for tid in failed_task_ids:
        idx = parse_batch_index(tid)
        if idx is None or idx >= len(original_batches):
            print(f"[{rater_label}] WARNING: cannot map task_id {tid!r} to a batch index. Skipping.",
                  file=sys.stderr)
            continue
        original_batch = original_batches[idx]
        halves = chunk(original_batch, retry_batch_size)
        for h, half in enumerate(halves):
            retry_tasks.append({
                "task_id": f"stage1_{rater_label}_b{idx:04d}_r{h}",
                "model": model,
                "temperature": temperature,
                "max_tokens": retry_max_tokens,
                "messages": [{"role": "user",
                              "content": create_prompt(half, taxonomy)}],
                "_original_task_id": tid,  # local bookkeeping, not sent to API
                "_expected_ids": [int(q["id"]) for q in half],
            })

    # Never-ran originals: re-submit as full batches with base parameters.
    rerun_tasks: list[dict] = []
    for tid in never_ran_task_ids:
        idx = parse_batch_index(tid)
        if idx is None or idx >= len(original_batches):
            print(f"[{rater_label}] WARNING: cannot map never-ran task {tid!r} to a batch index. Skipping.",
                  file=sys.stderr)
            continue
        rerun_tasks.append({
            "task_id": tid,
            "model": model,
            "temperature": temperature,
            "max_tokens": base_max_tokens,
            "messages": [{"role": "user",
                          "content": create_prompt(original_batches[idx], taxonomy)}],
            "_expected_ids": [int(q["id"]) for q in original_batches[idx]],
        })

    print(f"\n[{rater_label}] Retry pass:")
    if failed_task_ids:
        print(f"  - {len(failed_task_ids)} previously-failed batches → "
              f"{len(retry_tasks)} smaller tasks "
              f"(batch_size={retry_batch_size}, max_tokens={retry_max_tokens})")
    if never_ran_task_ids:
        print(f"  - {len(never_ran_task_ids)} never-ran batches → "
              f"resubmitted as full batches "
              f"(batch_size={base_batch_size}, max_tokens={base_max_tokens})")

    # Append to existing JSONL — do NOT clear.
    model_slug = slugify(model)
    results_path = dirs["out_root"] / cfg["output"]["results_filename_pattern"].format(
        rater_label=rater_label, model_slug=model_slug,
    )
    raw_subdir = dirs["raw_dir"] / rater_label

    # Live progress for the retry pass goes to a transient file; the canonical
    # checkpoint is written by the post-batch reconciliation below.
    retry_progress_path = dirs["ckpt_dir"] / f"{rater_label}.retry_progress.json"

    expected_ids_by_task = {
        t["task_id"]: t["_expected_ids"]
        for t in (retry_tasks + rerun_tasks)
    }

    tracker = _empty_tracker()
    handler = make_result_handler(
        rater_label=rater_label,
        raw_subdir=raw_subdir,
        results_path=results_path,
        checkpoint_path=retry_progress_path,
        tracker=tracker,
        expected_ids_by_task=expected_ids_by_task,
    )

    # Strip bookkeeping fields before submitting.
    api_tasks = [
        {k: v for k, v in t.items() if not k.startswith("_")}
        for t in (retry_tasks + rerun_tasks)
    ]

    t0 = time.monotonic()
    await client.batch(api_tasks, job_name=job_name, progress=handler)
    wall_s = time.monotonic() - t0
    print(f"[{rater_label}] Retry returned in {wall_s:.1f}s")

    tracker["summaries"].sort(key=lambda s: s["task_id"])

    # Map summaries back to original task IDs.
    half_summaries_by_orig: dict[str, list[dict]] = {}
    rerun_summary_by_orig: dict[str, dict] = {}
    for s in tracker["summaries"]:
        m = re.match(r"^(stage1_[a-z_]+_b\d{4})_r\d+$", s["task_id"])
        if m:
            half_summaries_by_orig.setdefault(m.group(1), []).append(s)
        else:
            rerun_summary_by_orig[s["task_id"]] = s

    # A failed original is recovered iff ALL of its retry halves succeeded.
    recovered_from_failed: list[str] = []
    still_failing: list[str] = []
    for orig_tid, half_summaries in half_summaries_by_orig.items():
        if all(s["outcome"] == "success" for s in half_summaries):
            recovered_from_failed.append(orig_tid)
        else:
            still_failing.append(orig_tid)

    # Never-ran reruns: each is its own original task ID.
    never_ran_succeeded: list[str] = []
    never_ran_still_failing: list[str] = []
    for orig_tid, s in rerun_summary_by_orig.items():
        if s["outcome"] == "success":
            never_ran_succeeded.append(orig_tid)
        else:
            never_ran_still_failing.append(orig_tid)

    # Build canonical checkpoint update.
    new_ckpt = dict(ckpt)
    for key in ("request_failed", "parse_failed", "truncated_and_unparseable"):
        new_ckpt[key] = sorted(set(ckpt.get(key, [])) - set(recovered_from_failed))
    new_ckpt.setdefault("succeeded_task_ids", [])
    new_ckpt["succeeded_task_ids"] = sorted(
        set(new_ckpt["succeeded_task_ids"]) | set(never_ran_succeeded)
    )
    # Bucket never-ran failures into the right list per outcome.
    for orig_tid in never_ran_still_failing:
        s = rerun_summary_by_orig[orig_tid]
        target_key = {
            "request_failed": "request_failed",
            "parse_failed": "parse_failed",
            "truncated_and_unparseable": "truncated_and_unparseable",
        }.get(s["outcome"], "request_failed")
        new_ckpt[target_key] = sorted(set(new_ckpt.get(target_key, [])) | {orig_tid})
    new_ckpt.setdefault("recovered_via_retry", [])
    new_ckpt["recovered_via_retry"] = sorted(
        set(new_ckpt["recovered_via_retry"])
        | set(recovered_from_failed)
        | set(never_ran_succeeded)
    )
    new_ckpt["last_retry_at"] = datetime.now(timezone.utc).isoformat()
    new_ckpt["last_retry_max_tokens"] = retry_max_tokens
    new_ckpt["last_retry_batch_size"] = retry_batch_size
    if results_path.exists():
        with open(results_path) as f:
            new_ckpt["records_written"] = sum(1 for _ in f)
    ckpt_path.write_text(json.dumps(new_ckpt, indent=2))

    if retry_progress_path.exists():
        retry_progress_path.unlink()

    return {
        "rater_label": rater_label,
        "model_requested": model,
        "model_slug": model_slug,
        "wall_seconds": wall_s,
        "mode": "retry",
        "tasks_total": len(retry_tasks) + len(rerun_tasks),
        "retry_max_tokens": retry_max_tokens,
        "retry_batch_size": retry_batch_size,
        "originals_attempted": failed_task_ids,
        "originals_recovered": sorted(recovered_from_failed),
        "originals_still_failing": sorted(still_failing),
        "never_ran_attempted": never_ran_task_ids,
        "never_ran_succeeded": sorted(never_ran_succeeded),
        "never_ran_still_failing": sorted(never_ran_still_failing),
        "summaries": tracker["summaries"],
        "records_in_jsonl": new_ckpt.get("records_written", 0),
        "results_path": str(results_path),
        "unknown_model_seen": tracker["unknown_model"],
    }


# =============================================================================
# CHECKPOINT FINALIZATION
# =============================================================================

def finalize_rater_outcome(
    *,
    rater_label: str,
    model: str,
    model_slug: str,
    summaries: list[dict],
    wall_s: float,
    results_path: Path,
    dirs: dict[str, Path],
    mode: str,
) -> dict:
    """Compute checkpoint and outcome dicts from a list of per-task summaries."""
    request_failed = [s["task_id"] for s in summaries if s["outcome"] == "request_failed"]
    parse_failed = [s["task_id"] for s in summaries if s["outcome"] == "parse_failed"]
    truncated = [s["task_id"] for s in summaries if s["outcome"] == "truncated_and_unparseable"]
    succeeded = [s["task_id"] for s in summaries if s["outcome"] == "success"]
    served_models = sorted({s["served_model"] for s in summaries if s["served_model"]})
    unknown_model_seen = any(s["unknown_model"] for s in summaries)
    records_written = sum(s["records"] for s in summaries)

    ckpt = {
        "rater_label": rater_label,
        "model_requested": model,
        "served_models": served_models,
        "succeeded_task_ids": succeeded,
        "request_failed": request_failed,
        "parse_failed": parse_failed,
        "truncated_and_unparseable": truncated,
        "records_written": records_written,
        "wall_seconds_initial": wall_s,
        "results_path": str(results_path),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    ckpt_path = dirs["ckpt_dir"] / f"{rater_label}.json"
    ckpt_path.write_text(json.dumps(ckpt, indent=2))

    if unknown_model_seen:
        print(f"\n[{rater_label}] WARNING: at least one batch failed with what "
              f"looks like an unknown-model error. Verify {model!r} in v2/usai_harness.yaml.\n",
              file=sys.stderr)

    return {
        "rater_label": rater_label,
        "model_requested": model,
        "model_slug": model_slug,
        "served_models": served_models,
        "wall_seconds": wall_s,
        "mode": mode,
        "tasks_total": len(summaries),
        "request_failed": request_failed,
        "parse_failed": parse_failed,
        "truncated_and_unparseable": truncated,
        "succeeded_task_ids": succeeded,
        "records_written": records_written,
        "results_path": str(results_path),
        "unknown_model_seen": unknown_model_seen,
        "summaries": summaries,
    }


# =============================================================================
# RUN REPORT
# =============================================================================

def write_run_report(
    cfg: dict[str, Any],
    dirs: dict[str, Path],
    n_questions: int,
    n_batches: int,
    preflight_record: dict,
    outcomes: list[dict],
    mode: str,
) -> Path:
    report_path = dirs["out_root"] / cfg["output"]["run_report"]
    L: list[str] = []
    L.append("# v2 Stage 1 Classification — Run Report")
    L.append("")
    L.append(f"- **Mode:** {mode}")
    L.append(f"- **Generated:** {datetime.now(timezone.utc).isoformat()}")
    L.append(f"- **Config:** `{CONFIG_PATH}`")
    L.append(f"- **Questions loaded:** {n_questions} (expected {cfg['expected']['question_count']})")
    L.append(f"- **Batches per rater (at default batch_size):** {n_batches} (expected {cfg['expected']['batch_count']})")
    L.append(f"- **Pipeline default batch_size:** {cfg['pipeline']['batch_size']}")
    L.append(f"- **Pipeline default max_tokens:** {cfg['pipeline']['max_tokens']}")
    L.append("  (Per-rater overrides, if any, are listed in each rater's section.)")
    L.append("")
    L.append("## Pre-flight")
    if preflight_record.get("skipped"):
        L.append("Skipped (config disabled).")
    else:
        L.append(f"- Default model requested: `{preflight_record.get('default_model_requested')}`")
        L.append(f"- Served by: `{preflight_record.get('served_model')}`")
        L.append(f"- Latency: {preflight_record.get('latency_ms', 0):.0f} ms")
    L.append("")

    for o in outcomes:
        L.append(f"## Rater: `{o['rater_label']}`")
        L.append("")
        L.append(f"- **Mode:** {o.get('mode', mode)}")
        L.append(f"- **Model requested:** `{o['model_requested']}`")
        served = o.get("served_models") or []
        if served:
            L.append(f"- **Served by:** {', '.join(f'`{s}`' for s in served)}")
        if "batch_size" in o:
            L.append(f"- **batch_size:** {o['batch_size']}")
        if "max_tokens" in o:
            L.append(f"- **max_tokens:** {o['max_tokens']}")
        L.append(f"- **Wall time:** {o['wall_seconds']:.1f} s")
        L.append(f"- **Tasks total:** {o['tasks_total']}")
        L.append(f"- **Results path:** `{o['results_path']}`")

        if o.get("mode") == "retry" or o.get("mode") == "retry_noop":
            # Retry-mode reporting. JSONL line count comes from disk — the
            # outcome's own counter only knows about THIS pass's writes, so
            # retry_noop outcomes (rater had no failures, wrote nothing this
            # pass) would otherwise render as "0 records" even when complete.
            jsonl_count = _count_jsonl_records(o.get("results_path"))
            L.append(f"- **Retry batch_size:** {o.get('retry_batch_size', 'n/a')}")
            L.append(f"- **Retry max_tokens:** {o.get('retry_max_tokens', 'n/a')}")
            L.append(f"- **Originals attempted:** {len(o.get('originals_attempted', []))}")
            L.append(f"- **Originals recovered:** {len(o.get('originals_recovered', []))}")
            L.append(f"- **Originals still failing:** {len(o.get('originals_still_failing', []))}")
            L.append(f"- **Records in JSONL (on disk):** {jsonl_count}")
            L.append("")
            L.append("> Note: The harness reports all API calls as successful "
                     "(HTTP 200). Truncation (`finish_reason=length`) is "
                     "detected by the parser, not the harness. A batch can be "
                     "\"harness-ok\" but \"parser-failed,\" which is why this "
                     "report can show failures while the harness summary "
                     "shows all OK.")

            remap_summaries = [s for s in o.get("summaries", [])
                               if s.get("id_remapped")]
            if remap_summaries:
                L.append("")
                L.append("### ID remaps (model returned wrong IDs, positionally corrected)")
                for s in remap_summaries:
                    L.append(f"  - `{s['task_id']}`: model returned "
                             f"{s.get('original_ids')}")

            if o.get("originals_recovered"):
                L.append("")
                L.append("### Recovered on retry")
                for tid in o["originals_recovered"]:
                    L.append(f"  - `{tid}`")

            if o.get("originals_still_failing"):
                L.append("")
                L.append("### STILL FAILING after retry — needs manual investigation")
                # For each still-failing original, show its retry-half summaries.
                halves_by_orig: dict[str, list[dict]] = {}
                for s in o.get("summaries", []):
                    # Map retry task_id back to original by stripping _r\d+
                    m = re.match(r"^(stage1_[a-z_]+_b\d{4})_r\d+$", s["task_id"])
                    orig = m.group(1) if m else s["task_id"]
                    halves_by_orig.setdefault(orig, []).append(s)
                for tid in o["originals_still_failing"]:
                    L.append(f"  - **`{tid}`** — halves:")
                    for s in halves_by_orig.get(tid, []):
                        L.append(f"    - `{s['task_id']}`: {s['outcome']} "
                                 f"(finish_reason={s['finish_reason']}, status={s['status_code']})")
                        if s.get("parse_error"):
                            L.append(f"      parse_error: {s['parse_error']}")
                        if s.get("error_body"):
                            L.append(f"      error_body: {s['error_body'][:200]}")
                        if s.get("response_text_snippet"):
                            L.append(f"      response_snippet: {s['response_text_snippet']!r}")
        else:
            # Initial-mode reporting
            L.append(f"- **Succeeded:** {len(o['succeeded_task_ids'])}")
            L.append(f"- **Request-failed:** {len(o['request_failed'])}")
            L.append(f"- **Parse-failed:** {len(o['parse_failed'])}")
            L.append(f"- **Truncated and unparseable:** {len(o['truncated_and_unparseable'])}")
            L.append(f"- **Records written:** {o['records_written']}")

            remap_summaries = [s for s in o["summaries"]
                               if s.get("id_remapped")]
            if remap_summaries:
                L.append("")
                L.append("### ID remaps (model returned wrong IDs, positionally corrected)")
                for s in remap_summaries:
                    L.append(f"  - `{s['task_id']}`: model returned "
                             f"{s.get('original_ids')}")

            failed_summaries = [s for s in o["summaries"]
                                if s["outcome"] != "success"]
            if failed_summaries:
                L.append("")
                L.append("### Failures (full list — these need investigation)")
                for s in failed_summaries:
                    L.append(f"  - **`{s['task_id']}`** — {s['outcome']}")
                    L.append(f"    - status_code: {s['status_code']}")
                    L.append(f"    - finish_reason: {s['finish_reason']}")
                    if s.get("served_model"):
                        L.append(f"    - served_model: `{s['served_model']}`")
                    if s.get("error"):
                        L.append(f"    - error: {s['error']}")
                    if s.get("error_body"):
                        L.append(f"    - error_body: {s['error_body'][:200]}")
                    if s.get("parse_error"):
                        L.append(f"    - parse_error: {s['parse_error']}")
                    if s.get("response_text_snippet"):
                        L.append(f"    - response_snippet (first 200 chars): {s['response_text_snippet']!r}")

        if o.get("unknown_model_seen"):
            L.append("")
            L.append(f"**Possible unknown-model error detected for `{o['model_requested']}`.** "
                     f"Verify pool name in `v2/usai_harness.yaml`.")
        L.append("")

    L.append("## Verdict")
    L.append("")
    L.append("Three states (same semantics across stage1/2/3): **PASS** — every "
             "question classified and read back. **PASS_WITH_RESIDUAL** — all "
             "written records read back, but a small fraction "
             f"(<= {int(_smoke.RESIDUAL_THRESHOLD * 100)}%) failed loudly and "
             "is retryable via `--retry-failed`; exit 0. **FAIL** — records "
             "silently dropped (read-back != written, a code bug), loud "
             "failures above threshold, an unknown-model error, or a rater "
             "that did not run.")
    L.append("")
    rows_iterated = cfg["expected"]["question_count"]
    agg = "PASS"

    def _downgrade(current: str, new: str) -> str:
        order = {"PASS": 0, "PASS_WITH_RESIDUAL": 1, "FAIL": 2}
        return new if order[new] > order[current] else current

    for o in outcomes:
        if o.get("mode") == "not_run":
            agg = _downgrade(agg, "FAIL")
            L.append(f"- `{o['rater_label']}`: **FAIL** — NOT RUN this session "
                     f"and no prior checkpoint on disk; run this rater before "
                     f"treating Stage 1 as complete.")
            continue
        if o.get("unknown_model_seen"):
            agg = _downgrade(agg, "FAIL")
            L.append(f"- `{o['rater_label']}`: **FAIL** — unknown-model error "
                     f"for `{o['model_requested']}` (not in harness pool).")
            continue
        if o.get("mode") in ("retry", "retry_noop"):
            count = _count_jsonl_records(o.get("results_path"))
        else:
            count = o.get("records_written", 0)
        v = _smoke.classify_run(
            requested=rows_iterated, written=count, loaded=count,
        )
        agg = _downgrade(agg, v["state"])
        source_note = " (from prior checkpoint)" if o.get("mode") == "prior_run" else ""
        L.append(f"- `{o['rater_label']}`: **{v['state']}** — {count}/{rows_iterated} "
                 f"records ({v['residual']} residual){source_note}: {v['reason']}")
    L.append("")
    L.append(f"**Overall: {agg}**")
    L.append("")

    if agg != "PASS":
        L.append("## Next step")
        L.append("")
        L.append("Investigate failures above. To retry failed batches with halved "
                 "batch_size and doubled max_tokens, run:")
        L.append("")
        L.append("```bash")
        L.append("python src/core/stage1_classify.py --retry-failed")
        L.append("```")
        L.append("")

    report_path.write_text("\n".join(L))
    return report_path


# =============================================================================
# MAIN
# =============================================================================

async def amain(args) -> int:
    cfg = load_config()
    smoke = bool(getattr(args, "smoke", False))
    if smoke and args.retry_failed:
        die("--smoke and --retry-failed are mutually exclusive.")
    dirs = ensure_dirs(cfg, smoke=smoke)

    # ---- SMOKE GATE -----------------------------------------------------
    # A full/initial run refuses to start unless a smoke pass exists for the
    # current code. Retry and smoke itself are exempt. The gate runs before any
    # batch is submitted; it loads no harness or input data of its own.
    if not args.retry_failed and not smoke:
        ok, reason = _smoke.smoke_gate_ok(
            smoke_stamp_path(cfg), script_path=THIS_SCRIPT,
        )
        if not ok:
            if args.skip_smoke_gate:
                print("!" * 70)
                print(f"WARNING: --skip-smoke-gate set; bypassing smoke gate "
                      f"({reason})")
                print("!" * 70)
            else:
                die(f"No valid smoke pass for current code ({reason}). "
                    f"Run with --smoke first, or pass --skip-smoke-gate to "
                    f"override (not recommended).")

    try:
        from usai_harness import USAiClient
    except ImportError as e:
        die(f"usai_harness not installed: {e}.")

    taxonomy = load_taxonomy(cfg)
    questions_df = load_questions(cfg)

    if smoke:
        # Bias the smoke sample toward an edge case: flag rows whose question
        # text is empty/NaN/whitespace as tricky, then let pick_smoke_indices
        # include one if present. Real run code path, tiny N. This exercises
        # the NaN-question edge that v1/v2 must round-trip, not just the happy
        # path.
        q_text = questions_df["question"]
        flags = [
            (q is None)
            or (isinstance(q, float) and pd.isna(q))
            or (pd.isna(q) if not isinstance(q, str) else not str(q).strip())
            for q in q_text
        ]
        idx = _smoke.pick_smoke_indices(flags, n=_smoke.SMOKE_N)
        questions_df = questions_df.iloc[idx].reset_index(drop=True)

    questions = questions_df.to_dict("records")
    n_questions = len(questions)
    n_batches = (n_questions + cfg["pipeline"]["batch_size"] - 1) // cfg["pipeline"]["batch_size"]

    print(f"Loaded {n_questions} questions, {n_batches} batches (at default batch_size).")
    print(f"Mode: {'smoke' if smoke else 'retry-failed' if args.retry_failed else 'initial'}")
    if args.rater:
        print(f"Single-rater mode: {args.rater} only.")

    # Decide which raters execute this session. --rater filters to one;
    # otherwise both run in order. Single-rater initial mode does a clean
    # wipe of that rater's prior outputs before the run.
    run_labels: list[str] = [args.rater] if args.rater else ["rater_a", "rater_b"]
    if args.rater and not args.retry_failed:
        _wipe_rater_output(args.rater, cfg, dirs)

    h = cfg["harness"]
    try:
        async with USAiClient(
            project=h["project"],
            config_path=Path(h["config_path"]),
            ledger_path=Path(h["ledger_path"]),
            log_dir=Path(h["log_dir"]),
        ) as client:
            for label, rcfg in cfg["raters"].items():
                if not client.config.has_model(rcfg["model"]):
                    die(f"Rater {label}: configured model {rcfg['model']!r} is not in "
                        f"v2/usai_harness.yaml pool. "
                        f"Pool: {[m.name for m in client.config.models]}.")

            if not args.retry_failed:
                preflight_record = await preflight(client, cfg, dirs)
            else:
                preflight_record = {"skipped": True}

            ran_outcomes: dict[str, dict] = {}
            for label in run_labels:
                rcfg = cfg["raters"][label]
                if args.retry_failed:
                    outcome = await run_rater_retry(
                        client=client, rater_label=label, rater_cfg=rcfg,
                        questions=questions, taxonomy=taxonomy, cfg=cfg, dirs=dirs,
                    )
                else:
                    outcome = await run_rater_initial(
                        client=client, rater_label=label, rater_cfg=rcfg,
                        questions=questions, taxonomy=taxonomy, cfg=cfg, dirs=dirs,
                        smoke=smoke,
                    )
                ran_outcomes[label] = outcome

                # ---- ROUND-TRIP GATE (initial OR smoke) -----------------
                # After a rater's JSONL is written, confirm the read-back
                # contract. SMOKE: strict -- every invariant (written==
                # requested, loaded==written, a model served, no null ids)
                # must hold or SmokeFailure (exit 3). INITIAL: fatal-only -- a
                # broken read-back contract (loaded!=written, e.g. duplicate or
                # null ids), total failure (written==0), or a null id dies
                # loudly. A written<requested shortfall here is the normal
                # loud residual (a few failed batches write no lines) and is
                # graded by the final three-state verdict, not fatal. Retry
                # mode appends/dedups, so the identities do not hold; skipped.
                if not args.retry_failed:
                    requested = outcome.get("requested", n_questions)
                    results_path = outcome.get("results_path")
                    written, key_values = _read_jsonl_keys(results_path)
                    loaded = len(_load_jsonl_ids(results_path))
                    if smoke:
                        problems = _smoke.check_roundtrip(
                            requested=requested,
                            written=written,
                            loaded=loaded,
                            served_models=set(outcome.get("served_models") or []),
                            model_requested=(rcfg["model"] if requested > 0 else None),
                            unknown_model=bool(outcome.get("unknown_model_seen")),
                            key_field="id",
                            key_values=key_values,
                        )
                        if problems:
                            raise _smoke.SmokeFailure(
                                f"[stage1_{label}] " + "; ".join(problems))
                    else:
                        problems = _smoke.fatal_roundtrip_problems(
                            requested=requested,
                            written=written,
                            loaded=loaded,
                            key_field="id",
                            key_values=key_values,
                        )
                        if problems:
                            die(f"FATAL [stage1_{label}]: " + "; ".join(problems))
                    print(f"   [roundtrip ok] stage1_{label}: "
                          f"requested={requested} written={written} "
                          f"loaded={loaded}")

        # Assemble report-ordered outcomes. For raters that didn't run this
        # session (--rater mode), reconstruct an outcome from disk so the
        # combined report still shows the whole picture.
        outcomes: list[dict] = []
        for label in ("rater_a", "rater_b"):
            if label in ran_outcomes:
                outcomes.append(ran_outcomes[label])
            else:
                outcomes.append(_build_prior_outcome(label, cfg, dirs))

        mode = "smoke" if smoke else "retry" if args.retry_failed else "initial"
        report_path = write_run_report(
            cfg, dirs, n_questions, n_batches, preflight_record, outcomes, mode,
        )
        print(f"\nRun report: {report_path}")

    except _smoke.SmokeFailure as e:
        print("\n" + "=" * 70)
        print(f"SMOKE FAILED: {e}")
        print("=" * 70)
        return _smoke.SMOKE_EXIT_CODE

    # A smoke run validates the round-trip contract, not full coverage.
    # Reaching here means every per-rater round-trip assert passed. Stamp the
    # current code so a later full run may start, then exit 0.
    if smoke:
        payload = _smoke.write_smoke_stamp(
            smoke_stamp_path(cfg), script_path=THIS_SCRIPT,
            extra={"raters": run_labels, "smoke_n": _smoke.SMOKE_N},
        )
        print("\n" + "=" * 70)
        print("SMOKE PASSED")
        print(f"  stamp: {smoke_stamp_path(cfg)}")
        print(f"  source_sha256: {payload['source_sha256'][:16]}...")
        print("=" * 70)
        return 0

    # Three-state verdict per rater (PASS / PASS_WITH_RESIDUAL / FAIL),
    # consistent with stage2/stage3. `count` is the usable records written;
    # the gap to question_count is the loud, retryable residual (failed batches
    # write no lines). A small residual passes with a --retry-failed note; a
    # systemic one FAILs. Silent drops (duplicate/null ids: count back != lines
    # written) were already fatal in the per-phase gate. `not_run` and an
    # unknown-model error are systemic and FAIL regardless of count.
    rows_iterated = cfg["expected"]["question_count"]
    worst_exit = 0
    for o in outcomes:
        label = o.get("rater_label") or o.get("label") or "rater"
        if o.get("mode") == "not_run":
            print(f"Verdict [{label}]: FAIL -- rater did not run")
            worst_exit = max(worst_exit, 2)
            continue
        if o.get("unknown_model_seen"):
            print(f"Verdict [{label}]: FAIL -- unknown-model error "
                  f"(model not in harness pool)")
            worst_exit = max(worst_exit, 2)
            continue
        if o.get("mode") in ("retry", "retry_noop"):
            count = _count_jsonl_records(o.get("results_path"))
        else:
            count = o.get("records_written", 0)
        v = _smoke.classify_run(
            requested=rows_iterated, written=count, loaded=count,
        )
        print(f"Verdict [{label}]: {v['state']} -- {v['reason']}")
        worst_exit = max(worst_exit, v["exit_code"])
    return worst_exit


def main() -> int:
    parser = argparse.ArgumentParser(description="v2 Stage 1 classifier")
    parser.add_argument(
        "--retry-failed", action="store_true",
        help="Re-run only previously-failed batches (per-rater checkpoint), "
             "with batch_size halved and max_tokens doubled. Appends to existing JSONL.",
    )
    parser.add_argument(
        "--rater", choices=["rater_a", "rater_b"], default=None,
        help="Run only this rater. Default: both. In single-rater initial "
             "mode, that rater's JSONL, raw_responses, and checkpoint are "
             "wiped before the run to avoid stale-data contamination. The "
             "skipped rater's state is read from disk for the combined "
             "run report.",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help=f"Smoke test: run the full path on {_smoke.SMOKE_N} questions "
             f"into a smoke/ subdir, assert round-trip invariants, stamp on "
             f"pass. Mutually exclusive with --retry-failed.",
    )
    parser.add_argument(
        "--skip-smoke-gate", action="store_true",
        help="Bypass the mandatory smoke gate on an initial run (prints a "
             "loud warning). Rare intentional use only.",
    )
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
