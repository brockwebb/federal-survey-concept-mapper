#!/usr/bin/env python3
"""v2 Stage 3 barrier classification: dual-rater + arbitrator pipeline.

For each candidate question pair (built by stage3_pair_builder.py), this
script routes the harmonization-barrier coding through three roles in
the USAi harness pool:

  * rater_a (Sonnet)  -- one prompt per pair, returns primary_barrier +
                         feasibility + reasoning.
  * rater_b (Gemini)  -- same prompt, independent rater.
  * arbitrator (Opus) -- only invoked on pairs where the two raters
                         disagree on primary_barrier or feasibility.

The barrier taxonomy (TC/CC/PC/RS/MC/PM + F1/F2/F3) is the v1 taxonomy
from `src/pipelines/01_barrier_pipeline.py` -- categories, subtypes,
and feasibility codes are copied verbatim. The only structural change
is one-pair-per-task (instead of v1's batched JSON-array prompts), so
the harness can checkpoint and retry individual pairs.

Run from v2/:

    python src/core/stage3_barrier_classify.py --survey cps
    python src/core/stage3_barrier_classify.py --survey foodaps
    python src/core/stage3_barrier_classify.py --survey ahs
    python src/core/stage3_barrier_classify.py --survey all
    python src/core/stage3_barrier_classify.py --survey cps --dry-run
    python src/core/stage3_barrier_classify.py --survey cps --retry-failed

Outputs land under output/stage3/results/<survey>/ (one tree per survey
even when --survey all is used). Schema mirrors v1 where applicable.

Halts loudly if any configured model is missing from the harness pool.
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


CONFIG_PATH = Path("config/stage3.yaml")


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# CONFIG
# =============================================================================

def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        die(f"Config not found at {CONFIG_PATH.resolve()}. "
            f"Run from the v2/ directory.")
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    required = {"source_surveys", "target_survey", "data", "output",
                "harness", "barrier_coding", "pipeline", "job"}
    missing = required - set(cfg.keys())
    if missing:
        die(f"Config missing top-level keys: {missing}")
    bc = cfg["barrier_coding"]
    for role in ("rater_a", "rater_b", "arbitrator"):
        if role not in bc or "model" not in bc[role]:
            die(f"barrier_coding.{role}.model is required")
    return cfg


# =============================================================================
# BARRIER TAXONOMY -- copied verbatim from v1
# src/pipelines/01_barrier_pipeline.py
# =============================================================================

BARRIER_TAXONOMY = """
## Harmonization Barrier Taxonomy

### Level 1: Constraint Type (6 categories)
| Code | Type | Definition |
|------|------|------------|
| TC | Temporal | Reference period or timing differences |
| CC | Construct | Concept definition or operationalization differences |
| PC | Population/Coverage | Universe, frame, or sample design differences |
| RS | Response Scale | Scale type, categories, or format differences |
| MC | Mode/Context | Interview mode or questionnaire context differences |
| PM | Processing/Metadata | Coding, weighting, or documentation differences |

### Level 2: Subtypes
**TC (Temporal):**
- TC.1: Reference period length (e.g., 7-day vs 12-month)
- TC.2: Temporal framing (point-in-time vs habitual vs retrospective)
- TC.3: Calendar alignment (fixed vs rolling reference periods)

**CC (Construct):**
- CC.1: Concept definition (different meaning of core term)
- CC.2: Operationalization (different behavioral indicators)
- CC.3: Boundary conditions (different thresholds or cutoffs)
- CC.4: Scope inclusions (different components counted)

**PC (Population/Coverage):**
- PC.1: Universe definition (target population differs)
- PC.2: Frame exclusions (different exclusions from sampling)
- PC.3: Age bounds (different age eligibility)
- PC.4: Geographic scope (different geographic coverage)

**RS (Response Scale):**
- RS.1: Scale type (fundamentally different response formats)
- RS.2: Category structure (different number/boundaries of categories)
- RS.3: Anchoring/labels (different verbal anchors or direction)
- RS.4: Numeric vs verbal (numeric scale vs labeled categories)

**MC (Mode/Context):**
- MC.1: Interview mode (different data collection modes)
- MC.2: Question routing (different skip patterns or filters)
- MC.3: Contextual priming (preceding questions affect interpretation)
- MC.4: Proxy response (proxy vs self-report rules)

**PM (Processing/Metadata):**
- PM.1: Coding schemes (different classification or coding)
- PM.2: Derived variables (different algorithms for constructed variables)
- PM.3: Documentation gaps (insufficient metadata to assess)

### Feasibility Classification
| Code | Feasibility | Definition |
|------|-------------|------------|
| F1 | Direct recode | Mechanically transformable (simple recoding) |
| F2 | Statistical adjustment | Requires modeling or assumptions |
| F3 | Incompatible | Fundamentally different, not harmonizable |

### Special code
- NHB: No Harmonization Barrier. Use when the two questions can be
       consolidated as-is with no barrier (feasibility F1 always).
"""


# =============================================================================
# PROMPTS
# =============================================================================

def create_rater_prompt(pair: dict[str, Any]) -> str:
    """Single-pair barrier-coding prompt. Returns ONE JSON object."""
    return f"""You are coding the harmonization barrier between a pair of federal survey questions using an established taxonomy from the survey methodology literature.

{BARRIER_TAXONOMY}

## QUESTION PAIR
- pair_id: {pair['pair_id']}
- source_survey: {pair['source_survey']}
- shared_topic: {pair.get('shared_topic', '')}
- shared_subtopic: {pair.get('shared_subtopic', '')}

QUESTION A ({pair['source_survey']}): "{pair['survey_text']}"
QUESTION B (ACS): "{pair['acs_text']}"

## TASK
Identify the SINGLE primary harmonization barrier preventing the two
questions from being consolidated as-is. Use the taxonomy above.

1. **classification**: Level 1 code (TC | CC | PC | RS | MC | PM | NHB).
2. **primary_barrier**: Level 1.Level 2 code (e.g., "TC.1"). Use "NHB"
   if there is no barrier.
3. **feasibility**: F1 | F2 | F3. NHB pairs are always F1.
4. **confidence**: 0.0-1.0 calibrated confidence in the classification.
5. **reference_period_a**: time reference in QUESTION A, or "not specified".
6. **reference_period_b**: time reference in QUESTION B, or "not specified".
7. **reasoning**: 2-3 sentences explaining the classification. Be specific
   about the differences (or, for NHB, why no barrier exists).
8. **consolidation_potential**: "yes" | "no" | "partial". Could QUESTION A
   be dropped if surveys were person-linked?

Respond with a SINGLE JSON OBJECT, no preamble, no markdown fence:
{{
  "pair_id": "{pair['pair_id']}",
  "classification": "TC | CC | PC | RS | MC | PM | NHB",
  "primary_barrier": "TC.1 | CC.2 | ... | NHB",
  "feasibility": "F1 | F2 | F3",
  "confidence": 0.0,
  "reference_period_a": "...",
  "reference_period_b": "...",
  "reasoning": "...",
  "consolidation_potential": "yes | no | partial"
}}
"""


def create_arbitrator_prompt(
    pair: dict[str, Any],
    rater_a: dict[str, Any],
    rater_b: dict[str, Any],
) -> str:
    """Arbitration prompt for one disagreement. Blind labels A/B."""
    return f"""You are arbitrating between two AI barrier classifications for a pair of federal survey questions. Use the established taxonomy.

{BARRIER_TAXONOMY}

## QUESTION PAIR
- pair_id: {pair['pair_id']}
- source_survey: {pair['source_survey']}
- shared_subtopic: {pair.get('shared_subtopic', '')}

QUESTION A ({pair['source_survey']}): "{pair['survey_text']}"
QUESTION B (ACS): "{pair['acs_text']}"

## RATER CODINGS
Rater A:
- classification: {rater_a.get('classification')}
- primary_barrier: {rater_a.get('primary_barrier')}
- feasibility: {rater_a.get('feasibility')}
- confidence: {rater_a.get('confidence')}
- reasoning: {rater_a.get('reasoning')}

Rater B:
- classification: {rater_b.get('classification')}
- primary_barrier: {rater_b.get('primary_barrier')}
- feasibility: {rater_b.get('feasibility')}
- confidence: {rater_b.get('confidence')}
- reasoning: {rater_b.get('reasoning')}

## TASK
Decide whose coding is correct, or provide your own if both are wrong.

Decision options:
- "pick_rater_a": Rater A is correct.
- "pick_rater_b": Rater B is correct.
- "new_classification": Both wrong; provide the correct taxonomy code.

Respond with a SINGLE JSON OBJECT, no preamble, no markdown fence:
{{
  "pair_id": "{pair['pair_id']}",
  "decision": "pick_rater_a | pick_rater_b | new_classification",
  "classification": "TC | CC | PC | RS | MC | PM | NHB",
  "primary_barrier": "TC.1 | CC.2 | ... | NHB",
  "feasibility": "F1 | F2 | F3",
  "confidence": 0.0,
  "reasoning": "2-3 sentences justifying the decision."
}}
"""


# =============================================================================
# HARNESS-RESPONSE EXTRACTORS (mirror stage2_adjudicate.py)
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
    """Same JSON-recovery flow used by stage2_adjudicate.py."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    if "```json" in content:
        content = content.split("```json", 1)[1]
    if "```" in content:
        content = content.split("```", 1)[0]
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    start = content.find("{")
    if start == -1:
        raise ValueError("No JSON object found")
    brace = 0
    for i, ch in enumerate(content[start:], start):
        if ch == "{":
            brace += 1
        elif ch == "}":
            brace -= 1
            if brace == 0:
                return json.loads(content[start:i + 1])
    raise ValueError("No complete JSON object found")


# =============================================================================
# DATA LOADING
# =============================================================================

def survey_keys_from_arg(cfg: dict[str, Any], arg: str) -> list[str]:
    valid = list(cfg["source_surveys"].keys())
    if arg == "all":
        return valid
    if arg not in valid:
        die(f"--survey {arg!r} not in config. Available: {valid + ['all']}")
    return [arg]


def load_pairs(cfg: dict[str, Any], survey_key: str) -> pd.DataFrame:
    pairs_dir = (Path(cfg["output"]["output_dir"])
                 / cfg["output"]["pairs_subdir"])
    path = pairs_dir / f"pairs_{survey_key}.csv"
    if not path.exists():
        die(f"Pairs CSV not found at {path}. "
            f"Run stage3_pair_builder.py first.")
    df = pd.read_csv(path)
    needed = ["pair_id", "source_survey", "survey_q_id", "survey_text",
              "acs_q_id", "acs_text", "shared_topic", "shared_subtopic"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        die(f"Pairs CSV missing columns: {missing}")
    return df


def survey_output_dir(cfg: dict[str, Any], survey_key: str) -> Path:
    return (Path(cfg["output"]["output_dir"])
            / cfg["output"]["results_subdir"] / survey_key)


# =============================================================================
# TASK IDs
# =============================================================================

TASK_ID_RE = re.compile(r"^stage3_(rater_a|rater_b|arb)_(.+)$")


def rater_task_id(rater_label: str, pair_id: str) -> str:
    return f"stage3_{rater_label}_{pair_id}"


def arb_task_id(pair_id: str) -> str:
    return f"stage3_arb_{pair_id}"


def parse_task_id(task_id: str) -> tuple[str | None, str | None]:
    m = TASK_ID_RE.match(task_id)
    if not m:
        return None, None
    return m.group(1), m.group(2)


# =============================================================================
# CHECKPOINTS
# =============================================================================

def write_checkpoint(
    path: Path,
    *,
    phase: str,
    job_name: str,
    mode: str,
    model_requested: str,
    completed: int,
    total: int,
    tracker: dict[str, Any],
) -> None:
    payload = {
        "phase": phase,
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
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        die(f"No checkpoint at {path}. Run the initial pass before "
            f"--retry-failed.")
    return json.loads(path.read_text(encoding="utf-8"))


def empty_tracker() -> dict[str, Any]:
    return {
        "summaries": [],
        "succeeded": [],
        "request_failed": [],
        "parse_failed": [],
        "served_models": set(),
        "unknown_model": False,
        "records_written": 0,
    }


# =============================================================================
# RATER PROGRESS HANDLER
# =============================================================================

def make_rater_handler(
    *,
    rater_label: str,
    pair_map: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
    records_lock: threading.Lock,
    tracker: dict[str, Any],
    raw_subdir: Path,
    results_path: Path,
    checkpoint_path: Path,
    job_name: str,
    mode: str,
    model_requested: str,
):
    raw_subdir.mkdir(parents=True, exist_ok=True)

    def handler(event) -> None:
        r = event.result
        task_id = r.task_id
        _, pair_id = parse_task_id(task_id)
        pair = pair_map.get(pair_id, {})

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
            "pair_id": pair_id,
            "rater": rater_label,
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
        record: dict[str, Any] = {"pair_id": pair_id, "rater": rater_label}

        if not r.success:
            summary["outcome"] = "request_failed"
            if isinstance(r.response, dict):
                summary["error_body"] = r.response.get("error_body")
            if looks_like_unknown_model_error(r.response or {}):
                summary["unknown_model"] = True
                tracker["unknown_model"] = True
            tracker["request_failed"].append(task_id)
            record.update({"status": "request_failed",
                           "error": r.error or "request_failed"})
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
                parsed = extract_json_robust(text)
            except Exception as e:
                summary["outcome"] = "parse_failed"
                summary["parse_error"] = str(e)
                tracker["parse_failed"].append(task_id)
                record.update({"status": "parse_failed",
                               "error": f"parse: {e}",
                               "finish_reason": summary["finish_reason"],
                               "served_model": served})
            else:
                record.update({
                    "status": "ok",
                    "classification": parsed.get("classification"),
                    "primary_barrier": parsed.get("primary_barrier"),
                    "feasibility": parsed.get("feasibility"),
                    "confidence": parsed.get("confidence"),
                    "reference_period_a": parsed.get("reference_period_a"),
                    "reference_period_b": parsed.get("reference_period_b"),
                    "consolidation_potential": parsed.get(
                        "consolidation_potential"),
                    "reasoning": parsed.get("reasoning"),
                    "finish_reason": summary["finish_reason"],
                    "served_model": served,
                })
                tracker["records_written"] += 1
                tracker["succeeded"].append(task_id)
                summary["outcome"] = "success"

        with records_lock:
            tracker["summaries"].append(summary)
            records.append(record)
            write_checkpoint(
                checkpoint_path,
                phase=f"rater_{rater_label}",
                job_name=job_name, mode=mode,
                model_requested=model_requested,
                completed=event.completed, total=event.total,
                tracker=tracker,
            )
            # Live append to JSONL for crash safety.
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")

            ts = datetime.now().strftime("%H:%M:%S")
            pct = (event.completed / event.total * 100.0) if event.total else 0.0
            print(
                f"[{ts}] {rater_label} {event.completed}/{event.total} "
                f"({pct:.1f}%)  "
                f"succeeded={len(tracker['succeeded'])} "
                f"failed={len(tracker['request_failed'])+len(tracker['parse_failed'])}  "
                f"[{pair_id} -> {summary['outcome']}]",
                flush=True,
            )

    return handler


# =============================================================================
# ARBITRATOR PROGRESS HANDLER
# =============================================================================

def make_arb_handler(
    *,
    pair_map: dict[str, dict[str, Any]],
    a_map: dict[str, dict[str, Any]],
    b_map: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
    rows_lock: threading.Lock,
    tracker: dict[str, Any],
    raw_subdir: Path,
    arb_csv: Path,
    checkpoint_path: Path,
    job_name: str,
    mode: str,
    model_requested: str,
    checkpoint_every: int,
):
    raw_subdir.mkdir(parents=True, exist_ok=True)

    def handler(event) -> None:
        r = event.result
        task_id = r.task_id
        _, pair_id = parse_task_id(task_id)
        pair = pair_map.get(pair_id, {})

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
            "task_id": task_id, "pair_id": pair_id, "rater": "arbitrator",
            "outcome": None, "status_code": r.status_code,
            "error": r.error, "error_body": None,
            "finish_reason": None, "served_model": None,
            "parse_error": None, "response_text_snippet": None,
            "unknown_model": False, "latency_ms": r.latency_ms,
        }
        row: dict[str, Any] = {
            "pair_id": pair_id,
            "source_survey": pair.get("source_survey"),
            "shared_subtopic": pair.get("shared_subtopic"),
            "rater_a_classification": (a_map.get(pair_id) or {}).get(
                "classification"),
            "rater_a_primary_barrier": (a_map.get(pair_id) or {}).get(
                "primary_barrier"),
            "rater_a_feasibility": (a_map.get(pair_id) or {}).get("feasibility"),
            "rater_b_classification": (b_map.get(pair_id) or {}).get(
                "classification"),
            "rater_b_primary_barrier": (b_map.get(pair_id) or {}).get(
                "primary_barrier"),
            "rater_b_feasibility": (b_map.get(pair_id) or {}).get("feasibility"),
        }

        if not r.success:
            summary["outcome"] = "request_failed"
            if isinstance(r.response, dict):
                summary["error_body"] = r.response.get("error_body")
            if looks_like_unknown_model_error(r.response or {}):
                summary["unknown_model"] = True
                tracker["unknown_model"] = True
            tracker["request_failed"].append(task_id)
            row.update({"status": "request_failed",
                        "decision": "failed",
                        "error": r.error or "request_failed"})
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
                parsed = extract_json_robust(text)
            except Exception as e:
                summary["outcome"] = "parse_failed"
                summary["parse_error"] = str(e)
                tracker["parse_failed"].append(task_id)
                row.update({"status": "parse_failed", "decision": "failed",
                            "error": f"parse: {e}",
                            "finish_reason": summary["finish_reason"],
                            "served_model": served})
            else:
                row.update({
                    "status": "arbitrated",
                    "decision": parsed.get("decision"),
                    "classification": parsed.get("classification"),
                    "primary_barrier": parsed.get("primary_barrier"),
                    "feasibility": parsed.get("feasibility"),
                    "confidence": parsed.get("confidence"),
                    "reasoning": parsed.get("reasoning"),
                    "finish_reason": summary["finish_reason"],
                    "served_model": served,
                })
                tracker["records_written"] += 1
                tracker["succeeded"].append(task_id)
                summary["outcome"] = "success"

        with rows_lock:
            tracker["summaries"].append(summary)
            rows.append(row)
            write_checkpoint(
                checkpoint_path,
                phase="arbitrator", job_name=job_name, mode=mode,
                model_requested=model_requested,
                completed=event.completed, total=event.total,
                tracker=tracker,
            )
            if len(rows) % checkpoint_every == 0:
                pd.DataFrame(rows).to_csv(arb_csv, index=False, encoding="utf-8")

            ts = datetime.now().strftime("%H:%M:%S")
            pct = (event.completed / event.total * 100.0) if event.total else 0.0
            print(
                f"[{ts}] arbitrator {event.completed}/{event.total} "
                f"({pct:.1f}%)  "
                f"succeeded={len(tracker['succeeded'])} "
                f"failed={len(tracker['request_failed'])+len(tracker['parse_failed'])}  "
                f"[{pair_id} -> {summary['outcome']}]",
                flush=True,
            )

    return handler


# =============================================================================
# PHASE RUNNERS
# =============================================================================

async def run_rater_phase(
    *,
    client,
    cfg: dict[str, Any],
    pairs: pd.DataFrame,
    rater_label: str,            # 'a' | 'b'
    survey_out: Path,
    results_path: Path,
    checkpoint_path: Path,
    raw_subdir: Path,
    job_name: str,
    mode: str,
    only_pair_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    role_key = f"rater_{rater_label}"
    bc = cfg["barrier_coding"]
    rater_cfg = bc[role_key]
    model = rater_cfg["model"]

    if not client.config.has_model(model):
        die(f"{role_key} model {model!r} not in v2/usai_harness.yaml pool. "
            f"Pool: {[m.name for m in client.config.models]}.")

    iter_pairs = pairs.to_dict("records")
    if only_pair_ids is not None:
        iter_pairs = [p for p in iter_pairs if p["pair_id"] in only_pair_ids]

    pair_map = {p["pair_id"]: p for p in iter_pairs}
    tasks = []
    for p in iter_pairs:
        tasks.append({
            "task_id": rater_task_id(rater_label, p["pair_id"]),
            "model": model,
            "temperature": bc["temperature"],
            "max_tokens": bc["max_tokens"],
            "messages": [{"role": "user",
                          "content": create_rater_prompt(p)}],
        })

    # For initial pass we truncate the JSONL. For retry, we append and
    # later rewrite the JSONL deduped-by-pair_id.
    if mode == "initial":
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_text("", encoding="utf-8")

    records: list[dict[str, Any]] = []
    lock = threading.Lock()
    tracker = empty_tracker()

    handler = make_rater_handler(
        rater_label=rater_label,
        pair_map=pair_map,
        records=records, records_lock=lock, tracker=tracker,
        raw_subdir=raw_subdir, results_path=results_path,
        checkpoint_path=checkpoint_path,
        job_name=job_name, mode=mode, model_requested=model,
    )

    if tasks:
        print(f"\n   submitting {len(tasks)} {role_key} tasks "
              f"(model={model})...")
        await client.batch(tasks, job_name=job_name, progress=handler)
    else:
        print(f"   no tasks for {role_key}")
    return records, tracker


def derive_disagreements(
    rater_a: dict[str, dict[str, Any]],
    rater_b: dict[str, dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """Return {pair_id: {a, b, kind}} for pairs where the two raters
    disagree on primary_barrier OR feasibility. Pairs where either rater
    failed are skipped (handled separately as unresolved)."""
    out: dict[str, dict[str, str]] = {}
    for pid, a in rater_a.items():
        b = rater_b.get(pid)
        if not b:
            continue
        if a.get("status") != "ok" or b.get("status") != "ok":
            continue
        pb_a, pb_b = a.get("primary_barrier"), b.get("primary_barrier")
        fe_a, fe_b = a.get("feasibility"), b.get("feasibility")
        if pb_a != pb_b or fe_a != fe_b:
            kind = []
            if pb_a != pb_b:
                kind.append("barrier")
            if fe_a != fe_b:
                kind.append("feasibility")
            out[pid] = {"kind": "+".join(kind)}
    return out


async def run_arb_phase(
    *,
    client,
    cfg: dict[str, Any],
    pairs_by_id: dict[str, dict[str, Any]],
    rater_a_by_id: dict[str, dict[str, Any]],
    rater_b_by_id: dict[str, dict[str, Any]],
    disagreement_ids: list[str],
    arb_csv: Path,
    checkpoint_path: Path,
    raw_subdir: Path,
    job_name: str,
    mode: str,
    only_pair_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bc = cfg["barrier_coding"]
    arb_cfg = bc["arbitrator"]
    model = arb_cfg["model"]

    if not client.config.has_model(model):
        die(f"arbitrator model {model!r} not in pool. "
            f"Pool: {[m.name for m in client.config.models]}.")

    if only_pair_ids is not None:
        disagreement_ids = [
            pid for pid in disagreement_ids if pid in only_pair_ids
        ]

    tasks = []
    for pid in disagreement_ids:
        p = pairs_by_id.get(pid)
        if p is None:
            continue
        tasks.append({
            "task_id": arb_task_id(pid),
            "model": model,
            "temperature": bc["temperature"],
            "max_tokens": bc["max_tokens"],
            "messages": [{"role": "user",
                          "content": create_arbitrator_prompt(
                              p, rater_a_by_id[pid], rater_b_by_id[pid],
                          )}],
        })

    rows: list[dict[str, Any]] = []
    lock = threading.Lock()
    tracker = empty_tracker()

    handler = make_arb_handler(
        pair_map=pairs_by_id,
        a_map=rater_a_by_id, b_map=rater_b_by_id,
        rows=rows, rows_lock=lock, tracker=tracker,
        raw_subdir=raw_subdir, arb_csv=arb_csv,
        checkpoint_path=checkpoint_path,
        job_name=job_name, mode=mode, model_requested=model,
        checkpoint_every=int(cfg["pipeline"]["batch_checkpoint_interval"]),
    )

    if tasks:
        print(f"\n   submitting {len(tasks)} arbitration tasks "
              f"(model={model})...")
        await client.batch(tasks, job_name=job_name, progress=handler)
    else:
        print("   no disagreements to arbitrate")
    return rows, tracker


# =============================================================================
# FINAL MERGE
# =============================================================================

def merge_final(
    pairs: pd.DataFrame,
    rater_a_by_id: dict[str, dict[str, Any]],
    rater_b_by_id: dict[str, dict[str, Any]],
    arb_by_id: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Build the final per-pair barrier classification CSV."""
    out_rows: list[dict[str, Any]] = []
    for _, p in pairs.iterrows():
        pid = p["pair_id"]
        a = rater_a_by_id.get(pid) or {}
        b = rater_b_by_id.get(pid) or {}
        arb = arb_by_id.get(pid)

        if a.get("status") != "ok" or b.get("status") != "ok":
            decision_method = "rater_failed"
            final_class = None
            final_barrier = None
            final_feas = None
            final_conf = None
        elif (a.get("primary_barrier") == b.get("primary_barrier")
              and a.get("feasibility") == b.get("feasibility")):
            decision_method = "agreement"
            final_class = a.get("classification")
            final_barrier = a.get("primary_barrier")
            final_feas = a.get("feasibility")
            ca, cb = a.get("confidence"), b.get("confidence")
            try:
                final_conf = max(float(ca), float(cb))
            except (TypeError, ValueError):
                final_conf = ca if ca is not None else cb
        elif arb is not None and arb.get("status") == "arbitrated":
            decision_method = arb.get("decision", "arbitrated")
            final_class = arb.get("classification")
            final_barrier = arb.get("primary_barrier")
            final_feas = arb.get("feasibility")
            final_conf = arb.get("confidence")
        else:
            decision_method = "arbitration_failed"
            final_class = None
            final_barrier = None
            final_feas = None
            final_conf = None

        out_rows.append({
            "pair_id": pid,
            "source_survey": p["source_survey"],
            "survey_q_id": int(p["survey_q_id"]),
            "acs_q_id": int(p["acs_q_id"]),
            "shared_topic": p.get("shared_topic"),
            "shared_subtopic": p.get("shared_subtopic"),
            "survey_text": p["survey_text"],
            "acs_text": p["acs_text"],
            "final_classification": final_class,
            "final_primary_barrier": final_barrier,
            "final_feasibility": final_feas,
            "final_confidence": final_conf,
            "decision_method": decision_method,
            "rater_a_primary_barrier": a.get("primary_barrier"),
            "rater_a_feasibility": a.get("feasibility"),
            "rater_a_confidence": a.get("confidence"),
            "rater_b_primary_barrier": b.get("primary_barrier"),
            "rater_b_feasibility": b.get("feasibility"),
            "rater_b_confidence": b.get("confidence"),
            "rater_a_status": a.get("status"),
            "rater_b_status": b.get("status"),
            "arbitrator_status": (arb or {}).get("status"),
        })
    return pd.DataFrame(out_rows)


# =============================================================================
# REPORT
# =============================================================================

def write_run_report(
    cfg: dict[str, Any],
    *,
    out_dir: Path,
    survey_key: str,
    pairs: pd.DataFrame,
    rater_a_records: list[dict[str, Any]],
    rater_b_records: list[dict[str, Any]],
    disagreements: dict[str, dict[str, str]],
    arb_rows: list[dict[str, Any]],
    final_df: pd.DataFrame,
    trackers: dict[str, dict[str, Any]],
    wall_seconds: float,
    mode: str,
) -> tuple[Path, bool]:
    path = out_dir / cfg["output"]["run_report"]
    bc = cfg["barrier_coding"]
    L: list[str] = []
    L.append(f"# v2 Stage 3 Barrier Classification -- {survey_key.upper()}")
    L.append("")
    L.append(f"- **Mode:** {mode}")
    L.append(f"- **Generated:** {datetime.now(timezone.utc).isoformat()}")
    L.append(f"- **Wall time:** {wall_seconds:.1f} s")
    L.append(f"- **Pairs (input):** {len(pairs):,}")
    L.append("")

    def _count_status(records: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in records:
            counts[r.get("status", "unknown")] = counts.get(
                r.get("status", "unknown"), 0) + 1
        return counts

    a_counts = _count_status(rater_a_records)
    b_counts = _count_status(rater_b_records)
    arb_counts = _count_status(arb_rows)

    a_failed = a_counts.get("request_failed", 0) + a_counts.get("parse_failed", 0)
    b_failed = b_counts.get("request_failed", 0) + b_counts.get("parse_failed", 0)
    arb_failed = (arb_counts.get("request_failed", 0)
                  + arb_counts.get("parse_failed", 0))

    coverage = (final_df["final_primary_barrier"].notna().sum()
                if "final_primary_barrier" in final_df.columns else 0)
    overall_pass = (a_failed == 0 and b_failed == 0 and arb_failed == 0
                    and coverage == len(pairs))

    L.append(f"## Verdict: **{'PASS' if overall_pass else 'FAIL'}**")
    L.append("")
    L.append(f"- rater_a (model `{bc['rater_a']['model']}`): "
             f"{a_counts.get('ok', 0)} ok, {a_failed} failed")
    L.append(f"- rater_b (model `{bc['rater_b']['model']}`): "
             f"{b_counts.get('ok', 0)} ok, {b_failed} failed")
    L.append(f"- disagreements arbitrated: {len(arb_rows)} "
             f"(of {len(disagreements)} identified; "
             f"{arb_failed} failed)")
    L.append(f"- final classifications written: {coverage} / {len(pairs)}")
    L.append("")

    if rater_a_records and rater_b_records:
        ok_a = {r["pair_id"] for r in rater_a_records if r.get("status") == "ok"}
        ok_b = {r["pair_id"] for r in rater_b_records if r.get("status") == "ok"}
        both = ok_a & ok_b
        L.append("## Inter-rater")
        L.append("")
        L.append(f"- pairs with both raters ok: {len(both):,}")
        L.append(f"- disagreements (barrier or feasibility): "
                 f"{len(disagreements):,} "
                 f"({100*len(disagreements)/max(len(both),1):.2f}%)")
        kinds: dict[str, int] = {}
        for d in disagreements.values():
            kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
        for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
            L.append(f"  - {k}: {v:,}")
        L.append("")

    if len(final_df) and "decision_method" in final_df.columns:
        L.append("## Final decision_method breakdown")
        L.append("")
        for k, n in final_df["decision_method"].value_counts().items():
            L.append(f"- `{k}`: {n} ({100*n/len(final_df):.2f}%)")
        L.append("")

    if len(final_df) and "final_classification" in final_df.columns:
        L.append("## Final barrier classifications")
        L.append("")
        for k, n in final_df["final_classification"].value_counts(
                dropna=False).items():
            L.append(f"- `{k}`: {n}")
        L.append("")
    if len(final_df) and "final_feasibility" in final_df.columns:
        L.append("## Final feasibility")
        L.append("")
        for k, n in final_df["final_feasibility"].value_counts(
                dropna=False).items():
            L.append(f"- `{k}`: {n}")
        L.append("")

    # Served-model confirmation
    L.append("## Served models")
    for role, t in trackers.items():
        sm = sorted(t["served_models"]) if t["served_models"] else []
        L.append(f"- {role}: {', '.join(f'`{s}`' for s in sm) or '(none)'}"
                 + ("  **UNKNOWN-MODEL ERROR**" if t["unknown_model"] else ""))
    L.append("")
    L.append(f"_See `{cfg['output']['raw_responses_subdir']}/` for raw "
             f"harness responses and `{cfg['output']['checkpoints_subdir']}/` "
             f"for per-phase checkpoints._")

    path.write_text("\n".join(L), encoding="utf-8")
    return path, overall_pass


# =============================================================================
# JSONL HELPERS
# =============================================================================

def write_jsonl_dedup(path: Path, records: list[dict[str, Any]]) -> None:
    """Write records keyed by (pair_id, rater) with the latest occurrence
    winning. Used after a retry pass so the JSONL on disk reflects current
    state."""
    keyed: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in records:
        key = (rec.get("pair_id", ""), rec.get("rater", ""))
        keyed[key] = rec
    with open(path, "w", encoding="utf-8") as f:
        for rec in keyed.values():
            f.write(json.dumps(rec, default=str) + "\n")


def load_jsonl_as_map(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            pid = rec.get("pair_id")
            if pid:
                out[pid] = rec
    return out


# =============================================================================
# PER-SURVEY ORCHESTRATION
# =============================================================================

async def run_survey(
    cfg: dict[str, Any],
    survey_key: str,
    args: argparse.Namespace,
) -> int:
    pairs = load_pairs(cfg, survey_key)
    if pairs.empty:
        print(f"[{survey_key}] no pairs to classify; skipping.")
        return 0

    out_dir = survey_output_dir(cfg, survey_key)
    raw_root = out_dir / cfg["output"]["raw_responses_subdir"]
    ckpt_dir = out_dir / cfg["output"]["checkpoints_subdir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    rater_a_path = out_dir / cfg["output"]["rater_a_results_filename"]
    rater_b_path = out_dir / cfg["output"]["rater_b_results_filename"]
    arb_csv = out_dir / cfg["output"]["arbitration_csv"]
    final_csv = out_dir / cfg["output"]["final_csv"]
    comp_json = out_dir / cfg["output"]["comparison_summary_json"]

    rater_a_ckpt = ckpt_dir / "rater_a.json"
    rater_b_ckpt = ckpt_dir / "rater_b.json"
    arb_ckpt = ckpt_dir / "arbitrator.json"

    job_a = f"{cfg['job']['rater_a_name']}_{survey_key}"
    job_b = f"{cfg['job']['rater_b_name']}_{survey_key}"
    job_arb = f"{cfg['job']['arbitrator_name']}_{survey_key}"

    mode = "retry" if args.retry_failed else "initial"
    if args.dry_run:
        mode = "dry_run"

    print(f"\n{'='*70}\nSURVEY: {survey_key}  ({len(pairs)} pairs, mode={mode})"
          f"\n{'='*70}")

    if args.dry_run:
        print(f"   would build rater_a + rater_b tasks "
              f"(model_a={cfg['barrier_coding']['rater_a']['model']}, "
              f"model_b={cfg['barrier_coding']['rater_b']['model']}).")
        print(f"   max_tokens={cfg['barrier_coding']['max_tokens']}, "
              f"temperature={cfg['barrier_coding']['temperature']}.")
        print(f"   output dir: {out_dir}")
        return 0

    try:
        from usai_harness import USAiClient
    except ImportError as e:
        die(f"usai_harness not installed: {e}")

    h = cfg["harness"]
    t0 = time.monotonic()

    async with USAiClient(
        project=h["project"],
        config_path=Path(h["config_path"]),
        ledger_path=Path(h["ledger_path"]),
        log_dir=Path(h["log_dir"]),
    ) as client:

        # ---- RETRY MODE: narrow each phase to its failed task_ids -------
        only_a: set[str] | None = None
        only_b: set[str] | None = None
        only_arb: set[str] | None = None
        if args.retry_failed:
            for ckpt_path, label, container in [
                (rater_a_ckpt, "rater_a", "a"),
                (rater_b_ckpt, "rater_b", "b"),
                (arb_ckpt, "arbitrator", "arb"),
            ]:
                if not ckpt_path.exists():
                    print(f"   no {label} checkpoint -- nothing to retry "
                          f"there.")
                    continue
                ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
                failed = sorted(set(ckpt.get("request_failed", []))
                                | set(ckpt.get("parse_failed", [])))
                pair_ids = {parse_task_id(t)[1] for t in failed
                            if parse_task_id(t)[1]}
                if container == "a":
                    only_a = pair_ids
                elif container == "b":
                    only_b = pair_ids
                else:
                    only_arb = pair_ids
                print(f"   {label}: {len(pair_ids)} failed task_ids to retry.")

        # ---- Phase 1: rater_a ------------------------------------------
        print(f"\n[{survey_key}] Phase 1: rater_a")
        a_records, a_tracker = await run_rater_phase(
            client=client, cfg=cfg, pairs=pairs, rater_label="a",
            survey_out=out_dir, results_path=rater_a_path,
            checkpoint_path=rater_a_ckpt,
            raw_subdir=raw_root / "rater_a",
            job_name=job_a, mode=mode, only_pair_ids=only_a,
        )
        # ---- Phase 2: rater_b ------------------------------------------
        print(f"\n[{survey_key}] Phase 2: rater_b")
        b_records, b_tracker = await run_rater_phase(
            client=client, cfg=cfg, pairs=pairs, rater_label="b",
            survey_out=out_dir, results_path=rater_b_path,
            checkpoint_path=rater_b_ckpt,
            raw_subdir=raw_root / "rater_b",
            job_name=job_b, mode=mode, only_pair_ids=only_b,
        )

        # For retry, dedup the JSONL on disk so the latest record wins.
        if args.retry_failed:
            disk_a = load_jsonl_as_map(rater_a_path)
            for rec in a_records:
                pid = rec.get("pair_id")
                if pid:
                    disk_a[pid] = rec
            write_jsonl_dedup(
                rater_a_path,
                [dict(v, pair_id=k) for k, v in disk_a.items()],
            )
            disk_b = load_jsonl_as_map(rater_b_path)
            for rec in b_records:
                pid = rec.get("pair_id")
                if pid:
                    disk_b[pid] = rec
            write_jsonl_dedup(
                rater_b_path,
                [dict(v, pair_id=k) for k, v in disk_b.items()],
            )

        # ---- Phase 3: disagreements + arbitration ----------------------
        rater_a_by_id = load_jsonl_as_map(rater_a_path)
        rater_b_by_id = load_jsonl_as_map(rater_b_path)
        disagreements = derive_disagreements(rater_a_by_id, rater_b_by_id)

        comp_summary = {
            "survey": survey_key,
            "pairs_total": int(len(pairs)),
            "rater_a_ok": int(sum(1 for r in rater_a_by_id.values()
                                  if r.get("status") == "ok")),
            "rater_b_ok": int(sum(1 for r in rater_b_by_id.values()
                                  if r.get("status") == "ok")),
            "agreements": int(sum(
                1 for pid, a in rater_a_by_id.items()
                if a.get("status") == "ok"
                and rater_b_by_id.get(pid, {}).get("status") == "ok"
                and a.get("primary_barrier") == rater_b_by_id[pid].get(
                    "primary_barrier")
                and a.get("feasibility") == rater_b_by_id[pid].get(
                    "feasibility")
            )),
            "disagreements": int(len(disagreements)),
        }
        comp_json.write_text(
            json.dumps(comp_summary, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"\n[{survey_key}] comparison: "
              f"{comp_summary['agreements']} agree, "
              f"{comp_summary['disagreements']} disagree")

        # Decide which arbitrations to run: disagreements minus those
        # already arbitrated (unless --retry-failed narrowed us).
        existing_arb: dict[str, dict[str, Any]] = {}
        if arb_csv.exists() and args.retry_failed:
            df_existing = pd.read_csv(arb_csv)
            for _, r in df_existing.iterrows():
                existing_arb[r["pair_id"]] = r.to_dict()

        disagreement_ids = list(disagreements.keys())
        if args.retry_failed:
            # only_arb (if set) already narrows; otherwise just retry any
            # currently-disagreeing pair that doesn't have a good prior
            # arbitration row.
            target = only_arb if only_arb is not None else {
                pid for pid in disagreement_ids
                if existing_arb.get(pid, {}).get("status") != "arbitrated"
            }
            disagreement_ids = [pid for pid in disagreement_ids
                                if pid in target]

        pairs_by_id = {p["pair_id"]: p for p in pairs.to_dict("records")}
        print(f"\n[{survey_key}] Phase 3: arbitration "
              f"({len(disagreement_ids)} tasks)")
        arb_rows, arb_tracker = await run_arb_phase(
            client=client, cfg=cfg,
            pairs_by_id=pairs_by_id,
            rater_a_by_id=rater_a_by_id, rater_b_by_id=rater_b_by_id,
            disagreement_ids=disagreement_ids,
            arb_csv=arb_csv, checkpoint_path=arb_ckpt,
            raw_subdir=raw_root / "arbitrator",
            job_name=job_arb, mode=mode,
            only_pair_ids=only_arb,
        )

    # Merge & write CSVs (still inside survey scope, outside harness ctx)
    # Combine existing + new arbitration rows so retries don't drop data.
    final_arb_rows: dict[str, dict[str, Any]] = dict(existing_arb)
    for row in arb_rows:
        final_arb_rows[row["pair_id"]] = row
    arb_df = pd.DataFrame(list(final_arb_rows.values()))
    if len(arb_df):
        arb_df = arb_df.sort_values("pair_id").reset_index(drop=True)
        arb_df.to_csv(arb_csv, index=False, encoding="utf-8")
    print(f"[{survey_key}] wrote {arb_csv}  "
          f"({len(arb_df)} arbitration rows)")

    final_df = merge_final(
        pairs, rater_a_by_id, rater_b_by_id, final_arb_rows,
    )
    final_df.to_csv(final_csv, index=False, encoding="utf-8")
    print(f"[{survey_key}] wrote {final_csv}  ({len(final_df)} rows)")

    wall = time.monotonic() - t0
    report_path, overall_pass = write_run_report(
        cfg, out_dir=out_dir, survey_key=survey_key,
        pairs=pairs,
        rater_a_records=list(rater_a_by_id.values()),
        rater_b_records=list(rater_b_by_id.values()),
        disagreements=disagreements,
        arb_rows=list(final_arb_rows.values()),
        final_df=final_df,
        trackers={
            "rater_a": a_tracker, "rater_b": b_tracker,
            "arbitrator": arb_tracker,
        },
        wall_seconds=wall, mode=mode,
    )
    print(f"[{survey_key}] wrote {report_path}")
    print(f"[{survey_key}] verdict: {'PASS' if overall_pass else 'FAIL'}")
    return 0 if overall_pass else 2


# =============================================================================
# MAIN
# =============================================================================

async def amain(args: argparse.Namespace) -> int:
    cfg = load_config()
    if args.dry_run and args.retry_failed:
        die("--dry-run and --retry-failed are mutually exclusive.")

    keys = survey_keys_from_arg(cfg, args.survey)
    print("=" * 70)
    print("v2 STAGE 3 BARRIER CLASSIFICATION")
    print(f"surveys: {keys}")
    print(f"mode:    {'dry_run' if args.dry_run else ('retry' if args.retry_failed else 'initial')}")
    print("=" * 70)

    exit_code = 0
    for k in keys:
        rc = await run_survey(cfg, k, args)
        if rc != 0:
            exit_code = rc
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="v2 Stage 3 barrier classification "
                    "(dual-rater + arbitrator)",
    )
    parser.add_argument("--survey", required=True,
                        help="cps | foodaps | ahs | all "
                             "(or any key in stage3.yaml source_surveys)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Load pairs + report intended jobs; no API calls.")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Re-run failed tasks across all phases.")
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
