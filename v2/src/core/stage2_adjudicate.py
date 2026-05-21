#!/usr/bin/env python3
"""v2 Stage 2: Adjudicate Stage 1 classification disagreements.

Confirmation run. Mirrors v1's arbitration artifact
(src/core/arbitrate_final.py) in logic; the model identity is blinded
(rater_a / rater_b) and all LLM traffic now goes through the USAi harness
-- the same auth path Stage 1 uses. No direct vendor SDK calls, no
dotenv, no env-var credential loading.

Strategy:
  * Merge the two per-rater JSONL files from Stage 1 on `id`.
  * A disagreement is any row where primary_topic OR primary_subtopic
    differs between rater_a and rater_b.
  * For each disagreement, compute min(confidence_a, confidence_b).
  * Auto-mark min_confidence >= confidence_threshold as dual_modal.
  * Submit the rest as a single `client.batch(...)` job (the harness owns
    concurrency, rate-limiting, retries). Each task is the arbitration
    prompt for one disagreement. The arbitrator picks pick_rater_a /
    pick_rater_b / dual_modal / new_concept.
  * Output CSV schema mirrors v1 so v1 and v2 outputs can be diffed.

Run from v2/ directory:
    python src/core/stage2_adjudicate.py            # full run
    python src/core/stage2_adjudicate.py --dry-run  # load + split only

Dry-run mode prints the merge counts, disagreement counts, and tier
breakdown and exits WITHOUT instantiating the harness client or calling
any API. Use it to verify data loading before committing to a full run.

What this script does NOT do:
  * Hardcode any model name, threshold, or path -- all in config/stage2.yaml.
  * Touch v1 artifacts. v1 is frozen.
  * Call vendor SDKs directly. The harness owns auth, retries, concurrency.
  * Tolerate an arbitrator model that isn't in the harness pool -- it halts
    at startup via client.config.has_model().
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


# =============================================================================
# CONFIG LOADING
# =============================================================================

CONFIG_PATH = Path("config/stage2.yaml")


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
                    "harness"}
    missing = required_top - set(cfg.keys())
    if missing:
        die(f"Config missing required top-level keys: {missing}")

    return cfg


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
    """Load a Stage 1 JSONL result file into a DataFrame."""
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
# AUTO DUAL-MODAL (high-confidence disagreements -- no API call needed)
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
    """Build harness task dicts + a side table mapping task_id -> baseline.

    The baseline is everything we already know about the row before the
    arbitrator answers (id, question, original picks, tier, ...). The
    progress callback merges arbitration output on top.
    """
    arb = cfg["arbitrator"]
    tasks: list[dict[str, Any]] = []
    baselines: dict[str, dict[str, Any]] = {}

    for _, row in needs_arb.iterrows():
        task_id = f"stage2_arb_{int(row['id']):06d}"
        prompt = create_arbitration_prompt(row, taxonomy)
        tasks.append({
            "task_id": task_id,
            "model": arb["model"],
            "temperature": arb["temperature"],
            "max_tokens": arb["max_tokens"],
            "messages": [{"role": "user", "content": prompt}],
        })
        baselines[task_id] = _arb_baseline(row)

    return tasks, baselines


def make_progress_handler(
    baselines: dict[str, dict[str, Any]],
    results: list[dict[str, Any]],
    results_lock: threading.Lock,
    arb_csv: Path,
    raw_subdir: Path,
    checkpoint_every: int,
):
    """Build the per-task progress callback for client.batch(progress=...).

    Each completed task fires this with a ProgressEvent whose .result is a
    BatchResult (task_id, success, status_code, latency_ms, error, response).
    The callback parses the arbitrator's JSON, merges it on top of the
    baseline, appends the row to `results`, and periodically writes the
    CSV checkpoint.
    """
    raw_subdir.mkdir(parents=True, exist_ok=True)

    def handler(event) -> None:
        r = event.result
        task_id = r.task_id
        baseline = baselines.get(task_id, {})

        raw_path = raw_subdir / f"{task_id}.json"
        raw_path.write_text(json.dumps({
            "task_id": task_id,
            "success": r.success,
            "status_code": r.status_code,
            "latency_ms": r.latency_ms,
            "error": r.error,
            "response": r.response,
        }, indent=2, default=str))

        result_row: dict[str, Any] = dict(baseline)

        if not r.success:
            result_row["status"] = "failed"
            result_row["decision"] = "failed"
            result_row["error"] = r.error or "request_failed"
        else:
            text = extract_response_text(r.response) or ""
            finish = extract_finish_reason(r.response)
            try:
                arb_result = extract_json_robust(text)
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
                result_row["finish_reason"] = finish
                result_row["status"] = "arbitrated"
            except Exception as e:
                result_row["status"] = "parse_failed"
                result_row["decision"] = "failed"
                result_row["error"] = f"parse: {e}"
                result_row["finish_reason"] = finish
                result_row["response_text_snippet"] = text[:200]

        with results_lock:
            results.append(result_row)
            if len(results) % checkpoint_every == 0:
                pd.DataFrame(results).to_csv(
                    arb_csv, index=False, encoding="utf-8",
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
# MAIN (async, harness-driven)
# =============================================================================

async def amain(args: argparse.Namespace) -> int:
    cfg = load_config()

    print("=" * 70)
    print("v2 STAGE 2 ADJUDICATION")
    if args.dry_run:
        print("MODE: dry-run (no harness, no API calls)")
    print("=" * 70)

    # --- Load inputs (no harness needed for any of this) ---
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

    # --- Output paths ---
    out_dir = Path(cfg["output"]["output_dir"])
    raw_subdir = out_dir / cfg["output"].get("raw_responses_subdir", "raw_responses")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_subdir.mkdir(parents=True, exist_ok=True)

    arb_csv = out_dir / cfg["output"]["arbitration_csv"]
    auto_csv = out_dir / cfg["output"]["auto_dual_modal_csv"]
    all_csv = out_dir / cfg["output"]["all_resolutions_csv"]

    # --- Import harness lazily so --dry-run works without it installed ---
    try:
        from usai_harness import USAiClient
    except ImportError as e:
        die(f"usai_harness not installed: {e}. "
            f"Stage 2 requires the same harness Stage 1 uses.")

    h = cfg["harness"]
    arb_cfg = cfg["arbitrator"]
    arb_model = arb_cfg["model"]

    print(f"\n3. Connecting to harness ({h['project']})...")
    async with USAiClient(
        project=h["project"],
        config_path=Path(h["config_path"]),
        ledger_path=Path(h["ledger_path"]),
        log_dir=Path(h["log_dir"]),
    ) as client:
        if not client.config.has_model(arb_model):
            die(f"Arbitrator model {arb_model!r} not in "
                f"v2/usai_harness.yaml pool. "
                f"Pool: {[m.name for m in client.config.models]}. "
                f"Fix v2/config/stage2.yaml or v2/usai_harness.yaml — "
                f"do not hardcode in script.")
        print(f"  arbitrator model {arb_model!r} resolved in pool")

        # Build per-disagreement tasks + baseline rows.
        tasks, baselines = build_api_tasks(needs_arb, taxonomy, cfg)
        print(f"  built {len(tasks)} arbitration tasks "
              f"(max_tokens={arb_cfg['max_tokens']}, "
              f"temperature={arb_cfg['temperature']})")

        # Submit as a single batch. The harness handles concurrency,
        # rate-limiting, and retries; the progress callback persists
        # each completion as it lands.
        results: list[dict[str, Any]] = []
        results_lock = threading.Lock()
        checkpoint_every = int(cfg["pipeline"]["batch_checkpoint_interval"])
        handler = make_progress_handler(
            baselines=baselines,
            results=results,
            results_lock=results_lock,
            arb_csv=arb_csv,
            raw_subdir=raw_subdir,
            checkpoint_every=checkpoint_every,
        )

        job_name = "stage2_adjudicate"
        if tasks:
            print(f"\n4. Submitting batch '{job_name}' to harness...")
            await client.batch(tasks, job_name=job_name, progress=handler)
            print(f"   batch complete; {len(results)} arbitration results")
        else:
            print("\n4. No disagreements need arbitration -- skipping batch.")

    # --- Persist final CSVs ---
    arb_df = pd.DataFrame(results)
    if len(arb_df):
        arb_df.to_csv(arb_csv, index=False, encoding="utf-8")
        print(f"   wrote {arb_csv}")

    print(f"\n5. Auto-classifying {len(auto_dual)} dual-modal cases...")
    auto_rows = build_auto_dual_modal_rows(auto_dual)
    auto_df = pd.DataFrame(auto_rows)
    auto_df.to_csv(auto_csv, index=False, encoding="utf-8")
    print(f"   wrote {auto_csv}")

    all_df = pd.concat([arb_df, auto_df], ignore_index=True)
    all_df.to_csv(all_csv, index=False, encoding="utf-8")
    print(f"   wrote {all_csv}")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal resolutions: {len(all_df):,}")
    if "decision" in all_df.columns:
        print("\nDecision breakdown:")
        for decision, count in all_df["decision"].value_counts().items():
            pct = count / len(all_df) * 100
            print(f"  {decision}: {count} ({pct:.1f}%)")
    if "is_dual_modal" in all_df.columns and len(all_df):
        dual_total = int(all_df["is_dual_modal"].fillna(False).astype(bool).sum())
        print(f"\nDual-modal total: {dual_total} "
              f"({dual_total / len(all_df) * 100:.1f}%)")
        if len(arb_df):
            arb_dual = int(
                arb_df["is_dual_modal"].fillna(False).astype(bool).sum()
            )
            print(f"  arbitrated dual_modal: {arb_dual}")
        print(f"  auto dual_modal:       {len(auto_df)}")
    if len(arb_df) and "status" in arb_df.columns:
        failed = arb_df[arb_df["status"].isin(["failed", "parse_failed"])]
        print(f"\nFailed arbitrations: {len(failed)}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="v2 Stage 2 adjudication: resolve Stage 1 disagreements",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load + merge + split only. No harness, no API calls.",
    )
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
