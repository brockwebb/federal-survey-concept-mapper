#!/usr/bin/env python3
"""v2 Stage 2: Adjudicate Stage 1 classification disagreements.

Confirmation run. Mirrors v1's arbitration artifact
(src/core/arbitrate_final.py) in logic, with two architectural changes:

  * All LLM traffic goes through the USAi harness (same auth path as
    Stage 1). No direct vendor SDK calls. No dotenv.
  * Operational parity with stage1_classify.py: live checkpoint file,
    per-task summaries, retry-failed mode, run report, served-model
    confirmation, records-written validation.

Strategy:
  * Merge the two per-rater JSONL files from Stage 1 on `id`.
  * A disagreement is any row where primary_topic OR primary_subtopic
    differs between rater_a and rater_b.
  * For each disagreement, compute min(confidence_a, confidence_b).
  * Auto-mark min_confidence >= confidence_threshold as dual_modal.
  * Submit the rest as a single `client.batch(...)` job. Each task is
    one arbitration prompt. The arbitrator picks pick_rater_a /
    pick_rater_b / dual_modal / new_concept.

Run from v2/ directory:
    python src/core/stage2_adjudicate.py                  # initial run
    python src/core/stage2_adjudicate.py --retry-failed   # retry only failed task_ids
    python src/core/stage2_adjudicate.py --dry-run        # load + split only

Dry-run mode prints counts and exits WITHOUT instantiating the harness
or calling any API. Use it to verify data loading before committing.

Retry-failed mode reads the checkpoint at
`output/stage2/checkpoints/stage2_arbitration.json`, identifies tasks
in `request_failed ∪ parse_failed`, re-submits ONLY those, merges
recovered results into the existing CSV (by `id`), and updates the
checkpoint. Successes are never re-run.

Output schema mirrors v1 so v1 and v2 outputs can be diffed.

What this script does NOT do:
  * Hardcode any model, threshold, or path -- all in config/stage2.yaml.
  * Touch v1 artifacts. v1 is frozen.
  * Call vendor SDKs directly. The harness owns auth + retries.
  * Tolerate an arbitrator model that isn't in the harness pool --
    halts at startup via client.config.has_model().
  * Swallow harness response details on failure. status_code,
    finish_reason, served_model, error_body snippet are captured for
    every task and surfaced in the run report.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import threading
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

CONFIG_PATH = Path("config/stage2.yaml")
THIS_SCRIPT = Path(__file__).resolve()


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        die(f"Config not found at {CONFIG_PATH.resolve()}. "
            f"Run from the v2/ directory.")
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    required_top = {"arbitrator", "pipeline", "data", "stage1", "output",
                    "harness", "job"}
    missing = required_top - set(cfg.keys())
    if missing:
        die(f"Config missing required top-level keys: {missing}")

    return cfg


def smoke_output_dir(cfg: dict[str, Any]) -> Path:
    """Where a --smoke run writes its working files. Kept under a dedicated
    smoke/ tree so it never clobbers real results."""
    return Path(cfg["output"]["output_dir"]) / "smoke"


def smoke_stamp_path(cfg: dict[str, Any]) -> Path:
    """Stage-level smoke-pass stamp. The gate is keyed on the script source
    hash (current code), so the stamp lives once at the smoke root."""
    return Path(cfg["output"]["output_dir"]) / "smoke" / "smoke_pass.json"


# =============================================================================
# DATA LOADING
# =============================================================================

def load_taxonomy(cfg: dict[str, Any]) -> dict[str, list[str]]:
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
    """Load the source questions CSV. Mirrors stage1_compare.load_questions."""
    path = Path(cfg["data"]["questions_csv"])
    if not path.exists():
        die(f"Questions CSV not found at {path.resolve()}")
    df = pd.read_csv(path)
    questions = []
    for idx, row in df.iterrows():
        question = row["Question"]
        surveys = [c for c in df.columns if c != "Question" and pd.notna(row[c])]
        questions.append({
            "id": int(idx),
            "primary_survey": surveys[0] if surveys else "Unknown",
            "question": str(question) if pd.notna(question) else "[NaN]",
        })
    return pd.DataFrame(questions)


def load_jsonl(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        die(f"{label}: file not found at {path.resolve()}")
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    df = pd.DataFrame(records)
    if "id" not in df.columns:
        die(f"{label}: JSONL records missing 'id' field")
    df["id"] = df["id"].astype(int)
    print(f"  {label}: {len(df)} records loaded from {path}")
    return df


# =============================================================================
# MERGE + DISAGREEMENT IDENTIFICATION
# =============================================================================

CONFIDENCE_TIERS = (
    ("very_low", 0.00, 0.60),
    ("low", 0.60, 0.75),
    ("medium", 0.75, 0.90),
    ("high", 0.90, 0.95),
    ("very_high", 0.95, 1.01),
)


def assign_tier(conf: float) -> str:
    for name, lo, hi in CONFIDENCE_TIERS:
        if lo <= conf < hi:
            return name
    return "very_high"


def build_disagreements(
    rater_a_df: pd.DataFrame,
    rater_b_df: pd.DataFrame,
    questions_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge raters on `id`, attach question text, return disagreements only."""
    cols = ["id", "primary_topic", "primary_subtopic", "confidence"]
    for col in cols:
        if col not in rater_a_df.columns:
            die(f"rater_a JSONL missing column {col!r}")
        if col not in rater_b_df.columns:
            die(f"rater_b JSONL missing column {col!r}")

    merged = rater_a_df[cols].merge(
        rater_b_df[cols],
        on="id",
        suffixes=("_a", "_b"),
        how="inner",
    )
    merged = merged.merge(
        questions_df[["id", "question", "primary_survey"]],
        on="id",
        how="left",
    )

    disagree_mask = (
        (merged["primary_topic_a"] != merged["primary_topic_b"])
        | (merged["primary_subtopic_a"] != merged["primary_subtopic_b"])
    )
    disagreements = merged[disagree_mask].copy()
    disagreements["min_confidence"] = disagreements[
        ["confidence_a", "confidence_b"]
    ].min(axis=1)
    disagreements["confidence_tier"] = disagreements["min_confidence"].apply(
        assign_tier
    )
    return disagreements


# =============================================================================
# HARNESS-RESPONSE EXTRACTORS (mirrors stage1_classify helpers)
# =============================================================================

def extract_response_text(harness_response: Any) -> str | None:
    if not isinstance(harness_response, dict):
        return None
    choices = harness_response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return None
    return message.get("content")


def extract_finish_reason(harness_response: Any) -> str | None:
    if not isinstance(harness_response, dict):
        return None
    choices = harness_response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    return choices[0].get("finish_reason")


def looks_like_unknown_model_error(harness_response: Any) -> bool:
    if not isinstance(harness_response, dict):
        return False
    body = harness_response.get("error_body")
    if not isinstance(body, str):
        return False
    lower = body.lower()
    needles = ("model not found", "model_not_found", "unknown model",
               "invalid model", "does not exist")
    return any(n in lower for n in needles)


def extract_json_robust(content: str) -> dict:
    """Robustly extract JSON from LLM response."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    if "```json" in content:
        content = content.split("```json")[1]
    if "```" in content:
        content = content.split("```")[0]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    try:
        start = content.find("{")
        if start == -1:
            raise ValueError("No JSON object found")

        brace_count = 0
        for i, char in enumerate(content[start:], start):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return json.loads(content[start:i + 1])

        raise ValueError("No complete JSON object found")
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Could not extract valid JSON: {e}")


# =============================================================================
# ARBITRATION PROMPT (blind labels: Rater A / Rater B)
# =============================================================================

def create_arbitration_prompt(
    row: pd.Series,
    taxonomy: dict[str, list[str]],
) -> str:
    return f"""You are arbitrating between two AI categorizations using the official Census Bureau taxonomy.

IMPORTANT RULES:
1. Most questions have ONE primary topic - this is the default
2. Only mark as "dual_modal" if the question GENUINELY spans two topics equally
3. Dual-modal should be RARE (<10% of cases) - justify it thoroughly
4. All topics and subtopics MUST exist in the provided taxonomy

CENSUS TAXONOMY:
{json.dumps(taxonomy, indent=2)}

QUESTION:
Survey: {row['primary_survey']}
Question: {row['question']}

RATER CATEGORIZATIONS:
Rater A:
- Topic: {row['primary_topic_a']}
- Subtopic: {row['primary_subtopic_a']}
- Confidence: {row['confidence_a']:.2f}

Rater B:
- Topic: {row['primary_topic_b']}
- Subtopic: {row['primary_subtopic_b']}
- Confidence: {row['confidence_b']:.2f}

CONFIDENCE CONTEXT:
- Min confidence: {row['min_confidence']:.2f}
- Tier: {row['confidence_tier']}

YOUR DECISION OPTIONS:
1. "pick_rater_a" - Rater A is correct (single primary)
2. "pick_rater_b" - Rater B is correct (single primary)
3. "dual_modal" - Question genuinely spans TWO topics (requires strong justification)
4. "new_concept" - Both wrong; provide correct concept (single primary)

DUAL-MODAL CRITERIA (must meet ALL):
- Question asks about two distinct topics simultaneously
- Cannot be accurately answered with single primary
- Not just that secondary concepts exist (most questions have those)
- Example: "What is your household income from employment benefits?" = Economic + Social

Return JSON:
{{
  "decision": "pick_rater_a" | "pick_rater_b" | "dual_modal" | "new_concept",

  "primary_topic": "Topic from taxonomy",
  "primary_subtopic": "Subtopic from taxonomy",
  "primary_confidence": 0.0-1.0,

  "secondary_primary_topic": "Topic from taxonomy" | null,
  "secondary_primary_subtopic": "Subtopic from taxonomy" | null,
  "secondary_primary_confidence": 0.0-1.0 | null,

  "all_relevant_subtopics": [
    "Topic.Subtopic",
    ...
  ],

  "reasoning": "Explanation (2-3 sentences). If dual_modal, justify why single primary is insufficient.",
  "is_dual_modal": true | false
}}

CRITICAL:
- Single primary is default
- Dual-modal requires explicit justification in reasoning
- All concepts must be from taxonomy
- all_relevant_subtopics should include concepts from both raters + any you identify
"""


# =============================================================================
# AUTO DUAL-MODAL
# =============================================================================

def build_auto_dual_modal_rows(
    auto_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in auto_df.iterrows():
        if row["confidence_a"] >= row["confidence_b"]:
            primary_topic = row["primary_topic_a"]
            primary_subtopic = row["primary_subtopic_a"]
            primary_conf = row["confidence_a"]
            secondary_topic = row["primary_topic_b"]
            secondary_subtopic = row["primary_subtopic_b"]
            secondary_conf = row["confidence_b"]
        else:
            primary_topic = row["primary_topic_b"]
            primary_subtopic = row["primary_subtopic_b"]
            primary_conf = row["confidence_b"]
            secondary_topic = row["primary_topic_a"]
            secondary_subtopic = row["primary_subtopic_a"]
            secondary_conf = row["confidence_a"]

        rows.append({
            "id": int(row["id"]),
            "question": row["question"],
            "primary_survey": row["primary_survey"],
            "original_rater_a": f"{row['primary_topic_a']}.{row['primary_subtopic_a']}",
            "original_rater_b": f"{row['primary_topic_b']}.{row['primary_subtopic_b']}",
            "original_rater_a_confidence": float(row["confidence_a"]),
            "original_rater_b_confidence": float(row["confidence_b"]),
            "min_confidence": float(row["min_confidence"]),
            "confidence_tier": row["confidence_tier"],
            "decision": "auto_dual_modal",
            "primary_topic": primary_topic,
            "primary_subtopic": primary_subtopic,
            "primary_confidence": float(primary_conf),
            "secondary_primary_topic": secondary_topic,
            "secondary_primary_subtopic": secondary_subtopic,
            "secondary_primary_confidence": float(secondary_conf),
            "all_relevant_subtopics": json.dumps([
                f"{primary_topic}.{primary_subtopic}",
                f"{secondary_topic}.{secondary_subtopic}",
            ]),
            "reasoning": (
                f"Both raters highly confident "
                f"(min={row['min_confidence']:.2f}) but chose different "
                f"topics. Auto-marked as dual-modal."
            ),
            "is_dual_modal": True,
            "status": "auto_dual_modal",
        })
    return rows


# =============================================================================
# HARNESS BATCH PLUMBING
# =============================================================================

TASK_ID_RE = re.compile(r"^stage2_arb_(\d{6,})$")


def task_id_for(row_id: int) -> str:
    return f"stage2_arb_{int(row_id):06d}"


def id_from_task_id(task_id: str) -> int | None:
    m = TASK_ID_RE.match(task_id)
    return int(m.group(1)) if m else None


def _arb_baseline(row: pd.Series) -> dict[str, Any]:
    """Bookkeeping fields kept regardless of arbitration outcome."""
    return {
        "id": int(row["id"]),
        "question": row["question"],
        "primary_survey": row["primary_survey"],
        "original_rater_a": f"{row['primary_topic_a']}.{row['primary_subtopic_a']}",
        "original_rater_b": f"{row['primary_topic_b']}.{row['primary_subtopic_b']}",
        "original_rater_a_confidence": float(row["confidence_a"]),
        "original_rater_b_confidence": float(row["confidence_b"]),
        "min_confidence": float(row["min_confidence"]),
        "confidence_tier": row["confidence_tier"],
    }


def build_api_tasks(
    needs_arb: pd.DataFrame,
    taxonomy: dict[str, list[str]],
    cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Build harness task dicts + a side table mapping task_id -> baseline."""
    arb = cfg["arbitrator"]
    tasks: list[dict[str, Any]] = []
    baselines: dict[str, dict[str, Any]] = {}

    for _, row in needs_arb.iterrows():
        tid = task_id_for(row["id"])
        tasks.append({
            "task_id": tid,
            "model": arb["model"],
            "temperature": arb["temperature"],
            "max_tokens": arb["max_tokens"],
            "messages": [{"role": "user",
                          "content": create_arbitration_prompt(row, taxonomy)}],
        })
        baselines[tid] = _arb_baseline(row)

    return tasks, baselines


def _empty_tracker() -> dict[str, Any]:
    """Mutable accumulator. Mirrors stage1_classify._empty_tracker."""
    return {
        "summaries": [],
        "succeeded": [],
        "request_failed": [],
        "parse_failed": [],
        "served_models": set(),
        "unknown_model": False,
        "records_written": 0,
    }


def _write_checkpoint(
    path: Path,
    *,
    job_name: str,
    mode: str,
    model_requested: str,
    completed: int,
    total: int,
    tracker: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> None:
    """Live checkpoint write. Same key names retry-mode reads back."""
    payload: dict[str, Any] = {
        "job_name": job_name,
        "mode": mode,
        "model_requested": model_requested,
        "completed": int(completed),
        "total": int(total),
        "records_written": int(tracker["records_written"]),
        "succeeded_task_ids": sorted(set(tracker["succeeded"])),
        "request_failed": sorted(set(tracker["request_failed"])),
        "parse_failed": sorted(set(tracker["parse_failed"])),
        "served_models": sorted(tracker["served_models"]),
        "unknown_model": bool(tracker["unknown_model"]),
        "last_update_at": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def make_progress_handler(
    *,
    baselines: dict[str, dict[str, Any]],
    results: list[dict[str, Any]],
    results_lock: threading.Lock,
    tracker: dict[str, Any],
    arb_csv: Path,
    raw_subdir: Path,
    checkpoint_path: Path,
    job_name: str,
    mode: str,
    model_requested: str,
    checkpoint_every: int,
):
    """Per-task progress callback for client.batch(progress=...).

    Records the full per-call status (status_code, finish_reason,
    served_model, error_body, parse outcome, response_text_snippet) on
    `tracker` and writes the checkpoint after every task. CSV is
    rewritten every `checkpoint_every` completions.
    """
    raw_subdir.mkdir(parents=True, exist_ok=True)

    def handler(event) -> None:
        r = event.result
        task_id = r.task_id
        baseline = baselines.get(task_id, {})

        # Persist the raw response for every task (success or fail).
        raw_path = raw_subdir / f"{task_id}.json"
        raw_path.write_text(json.dumps({
            "task_id": task_id,
            "success": r.success,
            "status_code": r.status_code,
            "latency_ms": r.latency_ms,
            "error": r.error,
            "response": r.response,
        }, indent=2, default=str), encoding="utf-8")

        summary: dict[str, Any] = {
            "task_id": task_id,
            "id": id_from_task_id(task_id),
            "outcome": None,
            "status_code": r.status_code,
            "error": r.error,
            "error_body": None,
            "finish_reason": None,
            "served_model": None,
            "parse_error": None,
            "response_text_snippet": None,
            "unknown_model": False,
            "latency_ms": r.latency_ms,
        }
        result_row: dict[str, Any] = dict(baseline)

        if not r.success:
            summary["outcome"] = "request_failed"
            if isinstance(r.response, dict):
                summary["error_body"] = r.response.get("error_body")
            if looks_like_unknown_model_error(r.response or {}):
                summary["unknown_model"] = True
                tracker["unknown_model"] = True
            tracker["request_failed"].append(task_id)
            result_row["status"] = "request_failed"
            result_row["decision"] = "failed"
            result_row["error"] = r.error or "request_failed"
            result_row["finish_reason"] = None
            result_row["served_model"] = None
        else:
            response = r.response or {}
            served = response.get("model") if isinstance(response, dict) else None
            if served:
                tracker["served_models"].add(served)
            summary["served_model"] = served
            summary["finish_reason"] = extract_finish_reason(response)

            text = extract_response_text(response) or ""
            if text:
                summary["response_text_snippet"] = text[:200]

            try:
                arb_result = extract_json_robust(text)
            except Exception as e:
                summary["outcome"] = "parse_failed"
                summary["parse_error"] = str(e)
                tracker["parse_failed"].append(task_id)
                result_row["status"] = "parse_failed"
                result_row["decision"] = "failed"
                result_row["error"] = f"parse: {e}"
                result_row["finish_reason"] = summary["finish_reason"]
                result_row["served_model"] = served
                result_row["response_text_snippet"] = summary["response_text_snippet"]
            else:
                result_row["decision"] = arb_result["decision"]
                result_row["primary_topic"] = arb_result["primary_topic"]
                result_row["primary_subtopic"] = arb_result["primary_subtopic"]
                result_row["primary_confidence"] = arb_result["primary_confidence"]
                result_row["secondary_primary_topic"] = arb_result.get(
                    "secondary_primary_topic"
                )
                result_row["secondary_primary_subtopic"] = arb_result.get(
                    "secondary_primary_subtopic"
                )
                result_row["secondary_primary_confidence"] = arb_result.get(
                    "secondary_primary_confidence"
                )
                result_row["all_relevant_subtopics"] = json.dumps(
                    arb_result.get("all_relevant_subtopics", [])
                )
                result_row["reasoning"] = arb_result["reasoning"]
                result_row["is_dual_modal"] = arb_result.get("is_dual_modal", False)
                result_row["finish_reason"] = summary["finish_reason"]
                result_row["served_model"] = served
                result_row["status"] = "arbitrated"
                tracker["records_written"] += 1
                tracker["succeeded"].append(task_id)
                summary["outcome"] = "success"

        with results_lock:
            tracker["summaries"].append(summary)
            results.append(result_row)
            _write_checkpoint(
                checkpoint_path,
                job_name=job_name,
                mode=mode,
                model_requested=model_requested,
                completed=event.completed,
                total=event.total,
                tracker=tracker,
            )
            if len(results) % checkpoint_every == 0:
                pd.DataFrame(results).to_csv(
                    arb_csv, index=False, encoding="utf-8",
                )

            # Stdout progress line. The harness's built-in text_progress
            # formatter is replaced when we pass progress=handler, so the
            # terminal goes silent during an hours-long run unless this
            # callback prints something itself.
            succeeded_n = len(tracker["succeeded"])
            failed_n = (len(tracker["request_failed"])
                        + len(tracker["parse_failed"]))
            pct = (event.completed / event.total * 100.0) if event.total else 0.0
            ts = datetime.now().strftime("%H:%M:%S")
            status_tag = (summary["outcome"]
                          if summary["outcome"] != "success" else "OK")
            print(
                f"[{ts}] {event.completed}/{event.total} ({pct:.1f}%)  "
                f"succeeded={succeeded_n} failed={failed_n}  "
                f"[{task_id} -> {status_tag}]",
                flush=True,
            )

    return handler


# =============================================================================
# DRY-RUN / SUMMARY HELPERS
# =============================================================================

def print_split_summary(
    disagreements: pd.DataFrame,
    needs_arb: pd.DataFrame,
    auto_dual: pd.DataFrame,
    threshold: float,
) -> None:
    print(f"\n   Total disagreements: {len(disagreements):,}")
    print(f"   Needs arbitration (min_conf < {threshold}): "
          f"{len(needs_arb):,}")
    print(f"   Auto dual-modal     (min_conf >= {threshold}): "
          f"{len(auto_dual):,}")

    print("\n   Arbitration breakdown by tier:")
    tier_counts = needs_arb["confidence_tier"].value_counts()
    tier_order = [t[0] for t in CONFIDENCE_TIERS]
    for tier in tier_order:
        count = int(tier_counts.get(tier, 0))
        if count > 0:
            print(f"     {tier}: {count}")


# =============================================================================
# RETRY-FAILED SUPPORT
# =============================================================================

def read_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        die(f"No checkpoint at {path}. Run the initial pass before "
            f"--retry-failed.")
    return json.loads(path.read_text(encoding="utf-8"))


def failed_ids_from_checkpoint(ckpt: dict[str, Any]) -> list[int]:
    failed_task_ids = sorted(set(
        ckpt.get("request_failed", []) + ckpt.get("parse_failed", [])
    ))
    ids = [id_from_task_id(t) for t in failed_task_ids]
    return [i for i in ids if i is not None]


def merge_retry_results_into_csv(
    arb_csv: Path,
    new_results: list[dict[str, Any]],
) -> pd.DataFrame:
    """Replace any existing rows whose id is in new_results['id']."""
    new_df = pd.DataFrame(new_results)
    if not arb_csv.exists():
        new_df.to_csv(arb_csv, index=False, encoding="utf-8")
        return new_df

    existing = pd.read_csv(arb_csv)
    if "id" not in existing.columns:
        die(f"Existing arbitration CSV has no 'id' column: {arb_csv}")

    retry_ids = set(new_df["id"].astype(int).tolist())
    keep = existing[~existing["id"].astype(int).isin(retry_ids)]
    combined = pd.concat([keep, new_df], ignore_index=True)
    combined = combined.sort_values("id").reset_index(drop=True)
    combined.to_csv(arb_csv, index=False, encoding="utf-8")
    return combined


def update_checkpoint_after_retry(
    ckpt: dict[str, Any],
    tracker: dict[str, Any],
) -> dict[str, Any]:
    """Move recovered task_ids out of failed lists into succeeded."""
    recovered = set(tracker["succeeded"])
    new_request_failed = sorted(
        set(ckpt.get("request_failed", [])) - recovered
    )
    new_parse_failed = sorted(set(ckpt.get("parse_failed", [])) - recovered)
    # Anything still failing after retry remains in whichever list this
    # pass placed it. Union with the still-failing lists we just produced.
    new_request_failed = sorted(
        set(new_request_failed) | set(tracker["request_failed"])
    )
    new_parse_failed = sorted(
        set(new_parse_failed) | set(tracker["parse_failed"])
    )
    succeeded = sorted(
        set(ckpt.get("succeeded_task_ids", [])) | recovered
    )
    served = sorted(
        set(ckpt.get("served_models", [])) | tracker["served_models"]
    )

    new_ckpt = dict(ckpt)
    new_ckpt["succeeded_task_ids"] = succeeded
    new_ckpt["request_failed"] = new_request_failed
    new_ckpt["parse_failed"] = new_parse_failed
    new_ckpt["served_models"] = served
    new_ckpt["recovered_via_retry"] = sorted(
        set(ckpt.get("recovered_via_retry", [])) | recovered
    )
    new_ckpt["last_retry_at"] = datetime.now(timezone.utc).isoformat()
    return new_ckpt


# =============================================================================
# RUN REPORT
# =============================================================================

def write_run_report(
    cfg: dict[str, Any],
    *,
    out_dir: Path,
    mode: str,
    disagreements_total: int,
    needs_arb_total: int,
    auto_dual_total: int,
    tier_counts: dict[str, int],
    arb_df: pd.DataFrame,
    auto_df: pd.DataFrame,
    all_df: pd.DataFrame,
    tracker: dict[str, Any],
    model_requested: str,
    wall_seconds: float,
) -> tuple[Path, dict[str, Any]]:
    """Write stage2_run_report.md. Returns (path, verdict) where verdict is
    the three-state dict from _smoke.classify_run."""
    report_path = out_dir / cfg["output"]["run_report"]
    L: list[str] = []
    L.append("# v2 Stage 2 Adjudication — Run Report")
    L.append("")
    L.append(f"- **Mode:** {mode}")
    L.append(f"- **Generated:** {datetime.now(timezone.utc).isoformat()}")
    L.append(f"- **Config:** `{CONFIG_PATH}`")
    L.append(f"- **Wall time:** {wall_seconds:.1f} s")
    L.append("")

    # Three-state verdict. `usable` resolutions are those actually resolved
    # (rows present, minus loud arbitration failures); the gap to
    # disagreements_total is the retryable residual (loud failures + any
    # uncovered disagreement). Silent drops were already fatal in the
    # per-phase arb gate, so this grades only the loud residual.
    arb_failed = 0
    if len(arb_df) and "status" in arb_df.columns:
        arb_failed = int(
            arb_df["status"].isin(["request_failed", "parse_failed", "failed"]).sum()
        )
    resolved_total = len(all_df)
    coverage_gap = disagreements_total - resolved_total
    usable = resolved_total - arb_failed
    verdict = _smoke.classify_run(
        requested=disagreements_total, written=usable, loaded=usable,
    )
    L.append(f"## Verdict: **{verdict['state']}**")
    L.append("")
    L.append(f"- {verdict['reason']}")
    L.append(f"- Disagreements (total): {disagreements_total}")
    L.append(f"- Resolutions written (arbitrated + auto): {resolved_total}")
    L.append(f"- Usable resolutions: {usable} "
             f"({verdict['residual']} residual)")
    L.append(f"- Coverage gap (must be 0): {coverage_gap}")
    L.append(f"- Failed arbitrations (request_failed + parse_failed): "
             f"{arb_failed}")
    L.append("")

    # Split
    L.append("## Split")
    L.append("")
    L.append(f"- Needs arbitration "
             f"(min_conf < {cfg['pipeline']['confidence_threshold']}): "
             f"{needs_arb_total}")
    L.append(f"- Auto dual-modal "
             f"(min_conf >= {cfg['pipeline']['confidence_threshold']}): "
             f"{auto_dual_total}")
    L.append("")

    L.append("### Arbitration tier breakdown")
    L.append("")
    tier_order = [t[0] for t in CONFIDENCE_TIERS]
    for tier in tier_order:
        if tier in tier_counts and tier_counts[tier] > 0:
            L.append(f"- {tier}: {tier_counts[tier]}")
    L.append("")

    # Decisions
    if "decision" in all_df.columns and len(all_df):
        L.append("## Decision breakdown (all resolutions)")
        L.append("")
        for decision, count in all_df["decision"].value_counts().items():
            pct = count / len(all_df) * 100
            L.append(f"- `{decision}`: {count} ({pct:.1f}%)")
        L.append("")

    # Arbitrator served-model confirmation
    L.append("## Arbitrator routing")
    L.append("")
    L.append(f"- Model requested (pool name): `{model_requested}`")
    if tracker["served_models"]:
        L.append(f"- Served by: {', '.join(f'`{s}`' for s in sorted(tracker['served_models']))}")
    else:
        L.append("- Served by: (no successes recorded — nothing to confirm)")
    if tracker["unknown_model"]:
        L.append("- **WARNING:** harness reported unknown-model error for at "
                 "least one task. Verify pool entry in `v2/usai_harness.yaml`.")
    L.append("")

    # Failure detail
    failed_summaries = [s for s in tracker["summaries"]
                        if s.get("outcome") in ("request_failed", "parse_failed")]
    if failed_summaries:
        L.append("## Failed arbitrations (per-task detail)")
        L.append("")
        for s in failed_summaries:
            L.append(f"### `{s['task_id']}`  (id={s.get('id')})")
            L.append(f"- outcome: `{s['outcome']}`")
            L.append(f"- status_code: {s.get('status_code')}")
            L.append(f"- finish_reason: `{s.get('finish_reason')}`")
            L.append(f"- served_model: `{s.get('served_model')}`")
            if s.get("error"):
                L.append(f"- error: `{s['error']}`")
            if s.get("error_body"):
                eb = str(s["error_body"])
                L.append(f"- error_body: `{eb[:300]}{'...' if len(eb) > 300 else ''}`")
            if s.get("parse_error"):
                L.append(f"- parse_error: `{s['parse_error']}`")
            if s.get("response_text_snippet"):
                L.append(f"- response_text_snippet: `{s['response_text_snippet']}`")
            L.append("")

    L.append("## Files")
    L.append("")
    L.append(f"- Arbitration CSV: `{cfg['output']['arbitration_csv']}`")
    L.append(f"- Auto dual-modal CSV: `{cfg['output']['auto_dual_modal_csv']}`")
    L.append(f"- All resolutions CSV: `{cfg['output']['all_resolutions_csv']}`")
    L.append(f"- Checkpoint: "
             f"`{cfg['output']['checkpoints_subdir']}/{cfg['output']['checkpoint_filename']}`")
    L.append(f"- Raw responses: `{cfg['output']['raw_responses_subdir']}/`")
    L.append("")

    report_path.write_text("\n".join(L), encoding="utf-8")
    return report_path, verdict


# =============================================================================
# MAIN (async, harness-driven)
# =============================================================================

async def amain(args: argparse.Namespace) -> int:
    cfg = load_config()
    smoke = bool(getattr(args, "smoke", False))

    mode = "retry" if args.retry_failed else "initial"
    if args.dry_run:
        mode = "dry_run"
    if smoke:
        mode = "smoke"

    print("=" * 70)
    print("v2 STAGE 2 ADJUDICATION")
    print(f"MODE: {mode}")
    print("=" * 70)

    # ---- SMOKE GATE -----------------------------------------------------
    # A full/initial run refuses to start unless a smoke pass exists for the
    # current code. Retry, dry-run, and smoke itself are exempt. The gate
    # sits here, before any data is loaded or any batch is submitted.
    if mode == "initial":
        stamp = smoke_stamp_path(cfg)
        ok, reason = _smoke.smoke_gate_ok(stamp, script_path=THIS_SCRIPT)
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
        return await _run(args, cfg, smoke, mode)
    except _smoke.SmokeFailure as e:
        print("\n" + "=" * 70)
        print(f"SMOKE FAILED: {e}")
        print("=" * 70)
        return _smoke.SMOKE_EXIT_CODE


async def _run(
    args: argparse.Namespace,
    cfg: dict[str, Any],
    smoke: bool,
    mode: str,
) -> int:

    # --- Load inputs ---
    print("\n1. Loading data...")
    taxonomy = load_taxonomy(cfg)
    questions_df = load_questions(cfg)
    print(f"  taxonomy: {len(taxonomy)} top-level topics")
    print(f"  questions: {len(questions_df)} rows from source CSV")

    rater_a_df = load_jsonl(Path(cfg["stage1"]["rater_a_results"]), "rater_a")
    rater_b_df = load_jsonl(Path(cfg["stage1"]["rater_b_results"]), "rater_b")

    print("\n2. Merging raters and identifying disagreements...")
    disagreements = build_disagreements(rater_a_df, rater_b_df, questions_df)
    threshold = float(cfg["pipeline"]["confidence_threshold"])
    needs_arb = disagreements[
        disagreements["min_confidence"] < threshold
    ].copy()
    auto_dual = disagreements[
        disagreements["min_confidence"] >= threshold
    ].copy()

    print_split_summary(disagreements, needs_arb, auto_dual, threshold)

    if args.dry_run:
        print("\nDRY RUN complete. Exiting before harness/API.")
        return 0

    # --- Smoke: limit arbitration to SMOKE_N pairs, biased to a tricky row ---
    # "Tricky" = a row whose question text is empty/NaN (the load_questions
    # path substitutes "[NaN]"), which stresses the arbitration prompt. We run
    # the full real path on these SMOKE_N pairs only. auto_dual is dropped so
    # the smoke run touches only the record-producing arbitration phase.
    if smoke:
        q = needs_arb["question"].astype(str)
        flags = [
            (not s.strip()) or s.strip() in ("[NaN]", "nan", "NaN", "None")
            for s in q
        ]
        idx = _smoke.pick_smoke_indices(flags, n=_smoke.SMOKE_N)
        needs_arb = needs_arb.iloc[idx].reset_index(drop=True)
        auto_dual = auto_dual.iloc[0:0].copy()
        print(f"\nSMOKE: limited to {len(needs_arb)} arbitration pairs "
              f"(of {len(disagreements)} disagreements).")

    # --- Output paths ---
    out_dir = (smoke_output_dir(cfg) if smoke
               else Path(cfg["output"]["output_dir"]))
    raw_subdir = out_dir / cfg["output"]["raw_responses_subdir"]
    ckpt_dir = out_dir / cfg["output"]["checkpoints_subdir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_subdir.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    arb_csv = out_dir / cfg["output"]["arbitration_csv"]
    auto_csv = out_dir / cfg["output"]["auto_dual_modal_csv"]
    all_csv = out_dir / cfg["output"]["all_resolutions_csv"]
    ckpt_path = ckpt_dir / cfg["output"]["checkpoint_filename"]

    # --- Retry-failed: load checkpoint, narrow needs_arb to failed ids ---
    prior_ckpt: dict[str, Any] = {}
    if args.retry_failed:
        prior_ckpt = read_checkpoint(ckpt_path)
        failed_ids = failed_ids_from_checkpoint(prior_ckpt)
        if not failed_ids:
            print("\nRETRY: no failed task_ids in checkpoint — nothing to do.")
            # Still rewrite "all" CSV to reflect current state.
            arb_df = pd.read_csv(arb_csv) if arb_csv.exists() else pd.DataFrame()
            auto_df = pd.read_csv(auto_csv) if auto_csv.exists() else pd.DataFrame()
            all_df = pd.concat(
                [d for d in [arb_df, auto_df] if len(d)],
                ignore_index=True,
            )
            if len(all_df):
                all_df.to_csv(all_csv, index=False, encoding="utf-8")
            print("DONE")
            return 0
        before = len(needs_arb)
        needs_arb = needs_arb[needs_arb["id"].astype(int).isin(failed_ids)].copy()
        print(f"\nRETRY: {len(needs_arb)} of {before} arbitration tasks "
              f"to re-run (from {len(failed_ids)} failed task_ids in checkpoint).")

    # --- Harness lazy import (so --dry-run never needs it) ---
    try:
        from usai_harness import USAiClient
    except ImportError as e:
        die(f"usai_harness not installed: {e}. "
            f"Stage 2 requires the same harness Stage 1 uses.")

    h = cfg["harness"]
    arb_cfg = cfg["arbitrator"]
    arb_model = arb_cfg["model"]
    job_name = cfg["job"]["name"] + ("_retry" if args.retry_failed else "")

    print(f"\n3. Connecting to harness ({h['project']})...")
    t0 = time.monotonic()
    async with USAiClient(
        project=h["project"],
        config_path=Path(h["config_path"]),
        ledger_path=Path(h["ledger_path"]),
        log_dir=Path(h["log_dir"]),
    ) as client:
        if not client.config.has_model(arb_model):
            die(f"Arbitrator model {arb_model!r} not in "
                f"v2/usai_harness.yaml pool. "
                f"Pool: {[m.name for m in client.config.models]}.")
        print(f"  arbitrator model {arb_model!r} resolved in pool")

        tasks, baselines = build_api_tasks(needs_arb, taxonomy, cfg)
        arb_requested = len(tasks)
        print(f"  built {len(tasks)} arbitration tasks "
              f"(max_tokens={arb_cfg['max_tokens']}, "
              f"temperature={arb_cfg['temperature']})")

        results: list[dict[str, Any]] = []
        results_lock = threading.Lock()
        tracker = _empty_tracker()
        checkpoint_every = int(cfg["pipeline"]["batch_checkpoint_interval"])

        handler = make_progress_handler(
            baselines=baselines,
            results=results,
            results_lock=results_lock,
            tracker=tracker,
            arb_csv=arb_csv,
            raw_subdir=raw_subdir,
            checkpoint_path=ckpt_path,
            job_name=job_name,
            mode=mode,
            model_requested=arb_model,
            checkpoint_every=checkpoint_every,
        )

        if tasks:
            print(f"\n4. Submitting batch '{job_name}' to harness "
                  f"({len(tasks)} tasks)...")
            await client.batch(tasks, job_name=job_name, progress=handler)
            print(f"   batch complete; {len(results)} arbitration results")
        else:
            print("\n4. No tasks to submit.")
    wall_s = time.monotonic() - t0

    # --- Persist arbitration CSV (initial or retry-merged) ---
    if args.retry_failed and results:
        arb_df = merge_retry_results_into_csv(arb_csv, results)
        print(f"   merged retry results into {arb_csv} "
              f"({len(arb_df)} total rows)")
    else:
        arb_df = pd.DataFrame(results)
        if len(arb_df):
            arb_df.to_csv(arb_csv, index=False, encoding="utf-8")
            print(f"   wrote {arb_csv}")
        elif arb_csv.exists():
            arb_df = pd.read_csv(arb_csv)

    # --- Round-trip gate for the arbitration phase (the record-producing
    # phase). SMOKE: strict -- every invariant must hold or SmokeFailure
    # (exit 3). INITIAL: fatal-only -- a broken read-back contract
    # (loaded!=written), total failure (written==0), or null keys die loudly;
    # a written<requested shortfall from LOUD arbitration failures is a
    # retryable residual graded by the three-state verdict, not fatal here.
    # Retry mode appends/merges, so the identities do not hold; skipped.
    if mode in ("initial", "smoke"):
        arb_written = len(results)
        if arb_csv.exists():
            arb_disk = pd.read_csv(arb_csv)
            arb_loaded = int(arb_disk["id"].notna().sum()) \
                if "id" in arb_disk.columns else len(arb_disk)
            arb_keys = (arb_disk["id"].tolist()
                        if "id" in arb_disk.columns else [])
        else:
            arb_loaded = 0
            arb_keys = []
        if smoke:
            arb_problems = _smoke.check_roundtrip(
                requested=arb_requested,
                written=arb_written,
                loaded=arb_loaded,
                served_models=tracker["served_models"],
                model_requested=(arb_model if arb_requested > 0 else None),
                unknown_model=tracker["unknown_model"],
                key_field="id",
                key_values=arb_keys,
            )
            if arb_problems:
                raise _smoke.SmokeFailure(
                    "[stage2_arbitration] " + "; ".join(arb_problems))
        else:
            arb_problems = _smoke.fatal_roundtrip_problems(
                requested=arb_requested,
                written=arb_written,
                loaded=arb_loaded,
                key_field="id",
                key_values=arb_keys,
            )
            if arb_problems:
                die(f"FATAL [stage2_arbitration]: " + "; ".join(arb_problems))
        print(f"   [roundtrip ok] stage2_arbitration: "
              f"requested={arb_requested} written={arb_written} "
              f"loaded={arb_loaded}")

    # --- Auto dual-modal (always written from disagreement state) ---
    print(f"\n5. Auto-classifying {len(auto_dual)} dual-modal cases...")
    auto_rows = build_auto_dual_modal_rows(auto_dual)
    auto_df = pd.DataFrame(auto_rows)
    auto_df.to_csv(auto_csv, index=False, encoding="utf-8")
    print(f"   wrote {auto_csv}")

    # --- Combined ---
    all_df = pd.concat(
        [d for d in [arb_df, auto_df] if len(d)],
        ignore_index=True,
    )
    all_df.to_csv(all_csv, index=False, encoding="utf-8")
    print(f"   wrote {all_csv}")

    # --- Update checkpoint for retry mode ---
    if args.retry_failed:
        new_ckpt = update_checkpoint_after_retry(prior_ckpt, tracker)
        # records_written reflects on-disk arbitration row count
        new_ckpt["records_written"] = len(arb_df)
        ckpt_path.write_text(json.dumps(new_ckpt, indent=2), encoding="utf-8")
        print(f"   updated checkpoint {ckpt_path}")
    else:
        # Final initial-pass checkpoint write (handler already wrote live;
        # this final flush carries total=tasks_count and records_written
        # for downstream consumers).
        _write_checkpoint(
            ckpt_path,
            job_name=job_name,
            mode=mode,
            model_requested=arb_model,
            completed=len(results),
            total=len(needs_arb),
            tracker=tracker,
        )

    # --- Run report + PASS/FAIL ---
    tier_counts = {
        t: int((needs_arb["confidence_tier"] == t).sum())
        for t in [name for name, _, _ in CONFIDENCE_TIERS]
    }
    report_path, verdict = write_run_report(
        cfg,
        out_dir=out_dir,
        mode=mode,
        disagreements_total=len(disagreements),
        needs_arb_total=len(needs_arb) if not args.retry_failed
        else int(prior_ckpt.get("total", len(needs_arb))),
        auto_dual_total=len(auto_dual),
        tier_counts=tier_counts,
        arb_df=arb_df,
        auto_df=auto_df,
        all_df=all_df,
        tracker=tracker,
        model_requested=arb_model,
        wall_seconds=wall_s,
    )
    print(f"\n   wrote {report_path}")

    # --- Console summary ---
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Disagreements (total):    {len(disagreements):,}")
    print(f"Resolutions written:      {len(all_df):,}")
    print(f"Coverage gap (must be 0): {len(disagreements) - len(all_df)}")
    if len(arb_df) and "status" in arb_df.columns:
        failed = int(
            arb_df["status"].isin(["request_failed", "parse_failed", "failed"]).sum()
        )
        print(f"Failed arbitrations:      {failed}")
    print(f"Verdict: {verdict['state']} -- {verdict['reason']}")
    print("=" * 70)

    if smoke:
        # Smoke validates the round-trip contract, not full coverage. Reaching
        # here means the arbitration round-trip assert passed; stamp the
        # current code so a later full run may start.
        payload = _smoke.write_smoke_stamp(
            smoke_stamp_path(cfg), script_path=THIS_SCRIPT,
            extra={"smoke_n": _smoke.SMOKE_N},
        )
        print("\n" + "=" * 70)
        print("SMOKE PASSED")
        print(f"  stamp: {smoke_stamp_path(cfg)}")
        print(f"  source_sha256: {payload['source_sha256'][:16]}...")
        print("=" * 70)
        return 0

    return verdict["exit_code"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="v2 Stage 2 adjudication: resolve Stage 1 disagreements",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load + merge + split only. No harness, no API calls.",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Read checkpoint; re-run only tasks in request_failed ∪ "
             "parse_failed.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help=f"Smoke test: run the full path on {_smoke.SMOKE_N} "
             f"arbitration pairs into a smoke/ subdir, assert round-trip "
             f"invariants, stamp on pass.",
    )
    parser.add_argument(
        "--skip-smoke-gate",
        action="store_true",
        help="Bypass the mandatory smoke gate on an initial run (prints a "
             "loud warning). Rare intentional use only.",
    )
    args = parser.parse_args()
    if sum(bool(x) for x in (args.dry_run, args.retry_failed, args.smoke)) > 1:
        die("--dry-run, --retry-failed, and --smoke are mutually exclusive.")
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
