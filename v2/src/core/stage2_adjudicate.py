#!/usr/bin/env python3
"""v2 Stage 2: Adjudicate Stage 1 classification disagreements.

Confirmation run. Mirrors v1's arbitration artifact
(src/core/arbitrate_final.py) byte-for-byte in logic; only the model identity
of the raters changed (claude-haiku-4-5 / gpt-5-mini -> claude_4_5_sonnet /
gemini-2.5-flash) and the field labels are blinded (rater_a / rater_b).

Strategy:
  * Merge the two per-rater JSONL files from Stage 1 on `id`.
  * A disagreement is any row where primary_topic OR primary_subtopic
    differs between rater_a and rater_b.
  * For each disagreement, compute min(confidence_a, confidence_b).
  * Auto-mark min_confidence >= confidence_threshold as dual_modal.
  * Send the rest to the LLM arbitrator with options:
      pick_rater_a / pick_rater_b / dual_modal / new_concept.
  * Output CSV schema mirrors v1 so v1 and v2 outputs can be diffed.

Run from v2/ directory:
    python src/core/stage2_adjudicate.py            # full run
    python src/core/stage2_adjudicate.py --dry-run  # load + split only

Dry-run mode prints the merge counts, disagreement counts, and tier
breakdown and exits WITHOUT calling the arbitrator API. Use it to verify
data loading before committing to a full arbitration pass.

What this script does NOT do:
  * Hardcode any model name, threshold, or path -- all in config/stage2.yaml.
  * Touch v1 artifacts. v1 is frozen.
  * Implement its own retry inside the API call beyond exponential backoff;
    higher-level retries belong to the operator (re-run on the residuals).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


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

    required_top = {"arbitrator", "pipeline", "data", "stage1", "output"}
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
    rater_a_cols = ["id", "primary_topic", "primary_subtopic", "confidence"]
    rater_b_cols = ["id", "primary_topic", "primary_subtopic", "confidence"]

    for col in rater_a_cols:
        if col not in rater_a_df.columns:
            die(f"rater_a JSONL missing column {col!r}")
    for col in rater_b_cols:
        if col not in rater_b_df.columns:
            die(f"rater_b JSONL missing column {col!r}")

    merged = rater_a_df[rater_a_cols].merge(
        rater_b_df[rater_b_cols],
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
# JSON EXTRACTION (lifted verbatim from v1 arbitrate_final.py)
# =============================================================================

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
                    json_str = content[start:i + 1]
                    return json.loads(json_str)

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
    """Arbitration prompt. Raters are blinded -- model identity withheld."""
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
# ARBITRATOR API CALL
# =============================================================================

def call_arbitrator(prompt: str, cfg: dict[str, Any]) -> dict[str, Any]:
    """Call the configured arbitrator model with retry/backoff."""
    arb = cfg["arbitrator"]
    provider = arb["provider"].lower()
    api_key = os.getenv(arb["api_key_env"])
    if not api_key:
        die(f"Environment variable {arb['api_key_env']} is not set. "
            f"Cannot reach arbitrator.")

    max_retries = cfg["pipeline"]["max_retries"]

    if provider != "anthropic":
        die(f"Unsupported arbitrator provider: {provider!r}. "
            f"Currently only 'anthropic' is wired.")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=arb["model"],
                max_tokens=arb["max_tokens"],
                temperature=arb["temperature"],
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text
            return extract_json_robust(content)
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Arbitrator failed after {max_retries} attempts: "
                       f"{last_err}")


# =============================================================================
# PER-QUESTION ARBITRATION
# =============================================================================

def arbitrate_question(
    row: pd.Series,
    taxonomy: dict[str, list[str]],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Arbitrate a single disagreement row."""
    result: dict[str, Any] = {
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

    try:
        prompt = create_arbitration_prompt(row, taxonomy)
        arb_result = call_arbitrator(prompt, cfg)

        result["decision"] = arb_result["decision"]
        result["primary_topic"] = arb_result["primary_topic"]
        result["primary_subtopic"] = arb_result["primary_subtopic"]
        result["primary_confidence"] = arb_result["primary_confidence"]
        result["secondary_primary_topic"] = arb_result.get("secondary_primary_topic")
        result["secondary_primary_subtopic"] = arb_result.get("secondary_primary_subtopic")
        result["secondary_primary_confidence"] = arb_result.get(
            "secondary_primary_confidence"
        )
        result["all_relevant_subtopics"] = json.dumps(
            arb_result.get("all_relevant_subtopics", [])
        )
        result["reasoning"] = arb_result["reasoning"]
        result["is_dual_modal"] = arb_result.get("is_dual_modal", False)
        result["status"] = "arbitrated"
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        result["decision"] = "failed"

    return result


# =============================================================================
# AUTO DUAL-MODAL (high-confidence disagreements)
# =============================================================================

def build_auto_dual_modal_rows(
    auto_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Auto-classify high-confidence disagreements as dual_modal.

    The higher-confidence rater wins primary; the other becomes secondary.
    """
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
# MAIN
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="v2 Stage 2 adjudication: resolve Stage 1 disagreements",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load + merge + split only. No arbitrator API calls.",
    )
    args = parser.parse_args()

    cfg = load_config()

    print("=" * 70)
    print("v2 STAGE 2 ADJUDICATION")
    if args.dry_run:
        print("MODE: dry-run (no API calls)")
    print("=" * 70)

    # --- Load inputs ---
    print("\n1. Loading data...")
    taxonomy = load_taxonomy(cfg)
    questions_df = load_questions(cfg)
    print(f"  taxonomy: {len(taxonomy)} top-level topics")
    print(f"  questions: {len(questions_df)} rows from source CSV")

    rater_a_path = Path(cfg["stage1"]["rater_a_results"])
    rater_b_path = Path(cfg["stage1"]["rater_b_results"])
    rater_a_df = load_jsonl(rater_a_path, "rater_a")
    rater_b_df = load_jsonl(rater_b_path, "rater_b")

    # --- Merge and identify disagreements ---
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
        print("\nDRY RUN complete. Exiting before API calls.")
        return 0

    # --- Output dir ---
    out_dir = Path(cfg["output"]["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    arb_csv = out_dir / cfg["output"]["arbitration_csv"]
    auto_csv = out_dir / cfg["output"]["auto_dual_modal_csv"]
    all_csv = out_dir / cfg["output"]["all_resolutions_csv"]

    # --- Arbitrate ---
    print(f"\n3. Arbitrating {len(needs_arb)} questions "
          f"(model={cfg['arbitrator']['model']}, "
          f"workers={cfg['pipeline']['max_workers']})...")

    results: list[dict[str, Any]] = []
    results_lock = threading.Lock()
    checkpoint_every = int(cfg["pipeline"]["batch_checkpoint_interval"])
    rate_delay = float(cfg["pipeline"]["rate_limit_delay"])
    max_workers = int(cfg["pipeline"]["max_workers"])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(arbitrate_question, row, taxonomy, cfg): int(row["id"])
            for _, row in needs_arb.iterrows()
        }

        with tqdm(total=len(needs_arb), desc="  Arbitrating") as pbar:
            for future in as_completed(future_to_id):
                result = future.result()
                with results_lock:
                    results.append(result)
                    if len(results) % checkpoint_every == 0:
                        pd.DataFrame(results).to_csv(
                            arb_csv, index=False, encoding="utf-8",
                        )
                pbar.update(1)
                time.sleep(rate_delay)

    arb_df = pd.DataFrame(results)
    arb_df.to_csv(arb_csv, index=False, encoding="utf-8")
    print(f"   wrote {arb_csv}")

    # --- Auto dual-modal ---
    print(f"\n4. Auto-classifying {len(auto_dual)} dual-modal cases...")
    auto_rows = build_auto_dual_modal_rows(auto_dual)
    auto_df = pd.DataFrame(auto_rows)
    auto_df.to_csv(auto_csv, index=False, encoding="utf-8")
    print(f"   wrote {auto_csv}")

    # --- Combined ---
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

    if "is_dual_modal" in all_df.columns:
        dual_total = int(all_df["is_dual_modal"].sum())
        print(f"\nDual-modal total: {dual_total} "
              f"({dual_total / len(all_df) * 100:.1f}%)")
        print(f"  arbitrated dual_modal: {int(arb_df['is_dual_modal'].sum())}")
        print(f"  auto dual_modal:       {len(auto_df)}")

    if "status" in arb_df.columns:
        failed = arb_df[arb_df["status"] == "failed"]
        print(f"\nFailed arbitrations: {len(failed)}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
