#!/usr/bin/env python3
"""v2 Stage 1 Comparison: v1 ↔ v2 classification agreement analysis.

The raison d'être of the v2 confirmation run. Compares classification
results across pipeline versions (v1 vs v2) and across raters (within
each version), measuring agreement at topic and subtopic levels.

Joins on `id` (CSV row index). Produces:
  - Agreement matrices (topic × topic, subtopic × subtopic)
  - Cohen's kappa at topic and subtopic levels
  - Disagreement lists with question text for inspection
  - Cross-version stability report (did the new models agree with the old?)
  - Summary statistics as JSON for downstream consumption

Run from v2/ directory:
    python src/core/stage1_compare.py

Reads all paths from config/stage1.yaml + hardcoded v1 paths (v1 is frozen,
paths won't change).

Output goes to output/stage1/comparison/.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

try:
    from sklearn.metrics import cohen_kappa_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# =============================================================================
# CONFIG
# =============================================================================

CONFIG_PATH = Path("config/stage1.yaml")

# v1 result paths are frozen — v1 is an archived artifact, these won't move.
V1_RESULTS_DIR = Path("../docs/stages/01_classification/data/results")
V1_CLAUDE = V1_RESULTS_DIR / "results_claude.jsonl"
V1_OPENAI = V1_RESULTS_DIR / "results_openai.jsonl"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        die(f"Config not found at {CONFIG_PATH.resolve()}. Run from v2/.")
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# DATA LOADING
# =============================================================================

def load_jsonl(path: Path, label: str) -> pd.DataFrame:
    """Load a JSONL classification result file into a DataFrame."""
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
    # Normalize id to int for clean joins
    df["id"] = df["id"].astype(int)
    print(f"  {label}: {len(df)} records loaded from {path}")
    return df


def load_questions(cfg: dict[str, Any]) -> pd.DataFrame:
    """Load the source questions CSV for disagreement context."""
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
            "survey": surveys[0] if surveys else "Unknown",
            "question": str(question) if pd.notna(question) else "[NaN]",
        })
    return pd.DataFrame(questions)


# =============================================================================
# AGREEMENT METRICS
# =============================================================================

def compute_agreement(
    merged: pd.DataFrame,
    col_a: str,
    col_b: str,
    label: str,
) -> dict[str, Any]:
    """Compute agreement metrics between two classification columns."""
    valid = merged[[col_a, col_b]].dropna()
    n = len(valid)
    if n == 0:
        return {"label": label, "n": 0, "raw_agreement": 0.0, "kappa": None}

    matches = (valid[col_a] == valid[col_b]).sum()
    raw_agreement = matches / n

    kappa = None
    if HAS_SKLEARN:
        try:
            kappa = cohen_kappa_score(valid[col_a], valid[col_b])
        except Exception:
            pass

    return {
        "label": label,
        "n": int(n),
        "matches": int(matches),
        "disagreements": int(n - matches),
        "raw_agreement": round(raw_agreement, 4),
        "raw_agreement_pct": round(raw_agreement * 100, 2),
        "kappa": round(kappa, 4) if kappa is not None else None,
    }


def build_confusion_matrix(
    merged: pd.DataFrame,
    col_a: str,
    col_b: str,
) -> pd.DataFrame:
    """Build a confusion/agreement matrix between two columns."""
    valid = merged[[col_a, col_b]].dropna()
    return pd.crosstab(valid[col_a], valid[col_b], margins=True)


def extract_disagreements(
    merged: pd.DataFrame,
    col_a: str,
    col_b: str,
    label_a: str,
    label_b: str,
    question_col: str = "question",
    survey_col: str = "survey",
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Extract rows where two classifiers disagree."""
    valid = merged.dropna(subset=[col_a, col_b])
    mask = valid[col_a] != valid[col_b]
    disagreed = valid[mask].copy()

    cols_out = ["id"]
    if question_col in disagreed.columns:
        cols_out.append(question_col)
    if survey_col in disagreed.columns:
        cols_out.append(survey_col)
    cols_out.extend([col_a, col_b])

    disagreed = disagreed[cols_out].rename(columns={
        col_a: label_a,
        col_b: label_b,
    })
    disagreed = disagreed.sort_values("id").reset_index(drop=True)
    if max_rows is not None:
        disagreed = disagreed.head(max_rows)
    return disagreed


def top_disagreement_pairs(
    merged: pd.DataFrame,
    col_a: str,
    col_b: str,
    top_n: int = 20,
) -> list[dict]:
    """Find the most common (value_a, value_b) disagreement pairs."""
    valid = merged[[col_a, col_b]].dropna()
    mask = valid[col_a] != valid[col_b]
    disagreed = valid[mask]
    pairs = Counter(zip(disagreed[col_a], disagreed[col_b]))
    return [
        {"from": a, "to": b, "count": c}
        for (a, b), c in pairs.most_common(top_n)
    ]


# =============================================================================
# CROSS-VERSION COMPARISON
# =============================================================================

def compare_pair(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    label_a: str,
    label_b: str,
    questions_df: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Any]:
    """Full comparison between two raters. Returns summary dict."""
    # Join on id
    merged = df_a.merge(
        df_b, on="id", suffixes=(f"_{label_a}", f"_{label_b}"),
        how="inner",
    )
    # Attach question text
    merged = merged.merge(questions_df[["id", "question", "survey"]], on="id", how="left")

    join_n = len(merged)
    col_topic_a = f"primary_topic_{label_a}"
    col_topic_b = f"primary_topic_{label_b}"
    col_sub_a = f"primary_subtopic_{label_a}"
    col_sub_b = f"primary_subtopic_{label_b}"

    # Agreement metrics
    topic_agreement = compute_agreement(merged, col_topic_a, col_topic_b,
                                         f"{label_a}_vs_{label_b}_topic")
    subtopic_agreement = compute_agreement(merged, col_sub_a, col_sub_b,
                                            f"{label_a}_vs_{label_b}_subtopic")

    # Confusion matrices
    topic_matrix = build_confusion_matrix(merged, col_topic_a, col_topic_b)
    subtopic_matrix = build_confusion_matrix(merged, col_sub_a, col_sub_b)

    # Top disagreement patterns
    topic_top_disagree = top_disagreement_pairs(merged, col_topic_a, col_topic_b)
    subtopic_top_disagree = top_disagreement_pairs(merged, col_sub_a, col_sub_b)

    # Full disagreement lists
    topic_disagree_df = extract_disagreements(
        merged, col_topic_a, col_topic_b, label_a, label_b,
    )
    subtopic_disagree_df = extract_disagreements(
        merged, col_sub_a, col_sub_b, label_a, label_b,
    )

    # Save artifacts
    pair_label = f"{label_a}_vs_{label_b}"
    topic_matrix.to_csv(output_dir / f"topic_matrix_{pair_label}.csv")
    subtopic_matrix.to_csv(output_dir / f"subtopic_matrix_{pair_label}.csv")
    topic_disagree_df.to_csv(
        output_dir / f"topic_disagreements_{pair_label}.csv", index=False,
    )
    subtopic_disagree_df.to_csv(
        output_dir / f"subtopic_disagreements_{pair_label}.csv", index=False,
    )

    return {
        "pair": pair_label,
        "joined_records": int(join_n),
        "records_a": int(len(df_a)),
        "records_b": int(len(df_b)),
        "topic": topic_agreement,
        "subtopic": subtopic_agreement,
        "topic_top_disagreements": topic_top_disagree,
        "subtopic_top_disagreements": subtopic_top_disagree,
    }


# =============================================================================
# CONFIDENCE ANALYSIS
# =============================================================================

def confidence_summary(df: pd.DataFrame, label: str) -> dict[str, Any]:
    """Summary statistics for confidence scores."""
    if "confidence" not in df.columns:
        return {"label": label, "available": False}
    conf = df["confidence"].dropna()
    return {
        "label": label,
        "available": True,
        "n": int(len(conf)),
        "mean": round(float(conf.mean()), 4),
        "median": round(float(conf.median()), 4),
        "std": round(float(conf.std()), 4),
        "min": round(float(conf.min()), 4),
        "max": round(float(conf.max()), 4),
        "below_0.5": int((conf < 0.5).sum()),
        "below_0.7": int((conf < 0.7).sum()),
        "above_0.9": int((conf >= 0.9).sum()),
    }


# =============================================================================
# V1 UNDECIDED ANALYSIS
# =============================================================================

def analyze_undecided(
    v1_df: pd.DataFrame,
    v2_df: pd.DataFrame,
    label_v1: str,
    label_v2: str,
) -> dict[str, Any]:
    """Check if v2 resolved v1's undecided/low-confidence cases.

    v1 didn't have an explicit 'undecided' category, but confidence < 0.5
    or certain topic values may indicate uncertainty. This looks at the
    lowest-confidence v1 records and checks if v2 classified them more
    confidently.
    """
    merged = v1_df.merge(v2_df, on="id", suffixes=("_v1", "_v2"), how="inner")

    # Low-confidence in v1
    if "confidence_v1" in merged.columns:
        low_conf_mask = merged["confidence_v1"] < 0.5
        low_conf = merged[low_conf_mask]
        n_low = len(low_conf)
        if n_low > 0 and "confidence_v2" in merged.columns:
            v2_improved = (low_conf["confidence_v2"] >= 0.7).sum()
            v2_agreed_topic = (
                low_conf["primary_topic_v1"] == low_conf["primary_topic_v2"]
            ).sum()
        else:
            v2_improved = 0
            v2_agreed_topic = 0
    else:
        n_low = 0
        v2_improved = 0
        v2_agreed_topic = 0

    return {
        "comparison": f"{label_v1}_vs_{label_v2}",
        "v1_low_confidence_count": int(n_low),
        "v2_improved_confidence": int(v2_improved),
        "v2_agreed_on_topic": int(v2_agreed_topic),
    }


# =============================================================================
# REPORT GENERATION
# =============================================================================

def write_comparison_report(
    output_dir: Path,
    comparisons: list[dict],
    confidences: list[dict],
    undecided_analyses: list[dict],
    record_counts: dict[str, int],
) -> Path:
    """Write human-readable markdown comparison report."""
    report_path = output_dir / "stage1_comparison_report.md"
    L: list[str] = []

    L.append("# v2 Stage 1 Comparison Report")
    L.append("")
    L.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    L.append("")
    L.append("## Record Counts")
    L.append("")
    for label, count in record_counts.items():
        L.append(f"- **{label}:** {count}")
    L.append("")

    L.append("## Pairwise Comparisons")
    L.append("")
    for comp in comparisons:
        L.append(f"### {comp['pair']}")
        L.append("")
        L.append(f"- Joined records: {comp['joined_records']}")
        L.append(f"- **Topic agreement:** {comp['topic']['raw_agreement_pct']}% "
                 f"({comp['topic']['matches']}/{comp['topic']['n']})")
        if comp["topic"]["kappa"] is not None:
            L.append(f"- **Topic Cohen's κ:** {comp['topic']['kappa']}")
        L.append(f"- **Subtopic agreement:** {comp['subtopic']['raw_agreement_pct']}% "
                 f"({comp['subtopic']['matches']}/{comp['subtopic']['n']})")
        if comp["subtopic"]["kappa"] is not None:
            L.append(f"- **Subtopic Cohen's κ:** {comp['subtopic']['kappa']}")
        L.append("")

        if comp["topic_top_disagreements"]:
            L.append("#### Top topic disagreement patterns")
            L.append("")
            for d in comp["topic_top_disagreements"][:10]:
                L.append(f"  - {d['from']} → {d['to']}: {d['count']}")
            L.append("")

        if comp["subtopic_top_disagreements"]:
            L.append("#### Top subtopic disagreement patterns")
            L.append("")
            for d in comp["subtopic_top_disagreements"][:10]:
                L.append(f"  - {d['from']} → {d['to']}: {d['count']}")
            L.append("")

    L.append("## Confidence Distributions")
    L.append("")
    for c in confidences:
        if not c.get("available"):
            L.append(f"- **{c['label']}:** no confidence data")
            continue
        L.append(f"### {c['label']}")
        L.append("")
        L.append(f"- Mean: {c['mean']}, Median: {c['median']}, Std: {c['std']}")
        L.append(f"- Range: [{c['min']}, {c['max']}]")
        L.append(f"- Below 0.5: {c['below_0.5']}, Below 0.7: {c['below_0.7']}, "
                 f"Above 0.9: {c['above_0.9']}")
        L.append("")

    if undecided_analyses:
        L.append("## Undecided / Low-Confidence Resolution")
        L.append("")
        for u in undecided_analyses:
            L.append(f"### {u['comparison']}")
            L.append("")
            L.append(f"- v1 records with confidence < 0.5: {u['v1_low_confidence_count']}")
            L.append(f"- Of those, v2 confidence ≥ 0.7: {u['v2_improved_confidence']}")
            L.append(f"- Of those, v2 agreed on topic: {u['v2_agreed_on_topic']}")
            L.append("")

    L.append("## Output Files")
    L.append("")
    L.append("All CSVs are in this directory (`output/stage1/comparison/`):")
    L.append("")
    L.append("- `topic_matrix_*.csv` — confusion matrices at topic level")
    L.append("- `subtopic_matrix_*.csv` — confusion matrices at subtopic level")
    L.append("- `topic_disagreements_*.csv` — full disagreement lists with question text")
    L.append("- `subtopic_disagreements_*.csv` — full disagreement lists with question text")
    L.append("- `comparison_summary.json` — machine-readable summary of all metrics")
    L.append("")

    report_path.write_text("\n".join(L), encoding="utf-8")
    return report_path


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="v2 Stage 1 comparison: v1 ↔ v2 classification agreement",
    )
    parser.add_argument(
        "--v2-only", action="store_true",
        help="Compare only v2 rater_a vs rater_b (skip v1 cross-version comparisons).",
    )
    args = parser.parse_args()

    cfg = load_config()

    # Output directory
    out_root = Path(cfg["output"]["output_dir"])
    comp_dir = out_root / "comparison"
    comp_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("v2 STAGE 1 COMPARISON")
    print("=" * 70)

    # --- Load v2 results ---
    print("\n1. Loading v2 results...")
    rater_a_cfg = cfg["raters"]["rater_a"]
    rater_b_cfg = cfg["raters"]["rater_b"]

    def slugify(name: str) -> str:
        import re
        return re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_")

    v2a_path = out_root / cfg["output"]["results_filename_pattern"].format(
        rater_label="rater_a", model_slug=slugify(rater_a_cfg["model"]),
    )
    v2b_path = out_root / cfg["output"]["results_filename_pattern"].format(
        rater_label="rater_b", model_slug=slugify(rater_b_cfg["model"]),
    )

    v2a = load_jsonl(v2a_path, f"v2_rater_a ({rater_a_cfg['model']})")
    v2b = load_jsonl(v2b_path, f"v2_rater_b ({rater_b_cfg['model']})")

    # --- Load v1 results ---
    v1_claude = None
    v1_openai = None
    if not args.v2_only:
        print("\n2. Loading v1 results...")
        if V1_CLAUDE.exists():
            v1_claude = load_jsonl(V1_CLAUDE, "v1_claude (claude-haiku-4-5)")
        else:
            print(f"  WARNING: v1 Claude results not found at {V1_CLAUDE}")
        if V1_OPENAI.exists():
            v1_openai = load_jsonl(V1_OPENAI, "v1_openai (gpt-5-mini)")
        else:
            print(f"  WARNING: v1 OpenAI results not found at {V1_OPENAI}")

    # --- Load question text for disagreement context ---
    print("\n3. Loading question text...")
    questions_df = load_questions(cfg)
    print(f"  {len(questions_df)} questions loaded")

    # --- Run comparisons ---
    print("\n4. Computing comparisons...")
    comparisons: list[dict] = []
    confidences: list[dict] = []
    undecided_analyses: list[dict] = []
    record_counts: dict[str, int] = {}

    record_counts["v2_rater_a"] = len(v2a)
    record_counts["v2_rater_b"] = len(v2b)

    # v2 internal: rater_a vs rater_b
    print("\n  v2 rater_a vs v2 rater_b...")
    comparisons.append(compare_pair(
        v2a, v2b, "v2a", "v2b", questions_df, comp_dir,
    ))

    # Confidence summaries for v2
    confidences.append(confidence_summary(v2a, f"v2_rater_a ({rater_a_cfg['model']})"))
    confidences.append(confidence_summary(v2b, f"v2_rater_b ({rater_b_cfg['model']})"))

    if not args.v2_only:
        if v1_claude is not None:
            record_counts["v1_claude"] = len(v1_claude)
            confidences.append(confidence_summary(v1_claude, "v1_claude"))

            # v1_claude vs v2_rater_a (Claude lineage)
            print("  v1_claude vs v2_rater_a (Claude lineage)...")
            comparisons.append(compare_pair(
                v1_claude, v2a, "v1claude", "v2a", questions_df, comp_dir,
            ))

            # v1_claude vs v2_rater_b
            print("  v1_claude vs v2_rater_b...")
            comparisons.append(compare_pair(
                v1_claude, v2b, "v1claude", "v2b", questions_df, comp_dir,
            ))

            # Undecided resolution
            undecided_analyses.append(analyze_undecided(
                v1_claude, v2a, "v1_claude", "v2_rater_a",
            ))

        if v1_openai is not None:
            record_counts["v1_openai"] = len(v1_openai)
            confidences.append(confidence_summary(v1_openai, "v1_openai"))

            # v1_openai vs v2_rater_a
            print("  v1_openai vs v2_rater_a...")
            comparisons.append(compare_pair(
                v1_openai, v2a, "v1openai", "v2a", questions_df, comp_dir,
            ))

            # v1_openai vs v2_rater_b (GPT → Gemini succession)
            print("  v1_openai vs v2_rater_b (GPT → Gemini)...")
            comparisons.append(compare_pair(
                v1_openai, v2b, "v1openai", "v2b", questions_df, comp_dir,
            ))

            # Undecided resolution
            undecided_analyses.append(analyze_undecided(
                v1_openai, v2a, "v1_openai", "v2_rater_a",
            ))

        if v1_claude is not None and v1_openai is not None:
            # v1 internal: claude vs openai (baseline inter-rater)
            print("  v1_claude vs v1_openai (v1 baseline)...")
            comparisons.append(compare_pair(
                v1_claude, v1_openai, "v1claude", "v1openai", questions_df, comp_dir,
            ))

    # --- Save machine-readable summary ---
    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "record_counts": record_counts,
        "comparisons": comparisons,
        "confidences": confidences,
        "undecided_analyses": undecided_analyses,
        "sklearn_available": HAS_SKLEARN,
    }
    summary_path = comp_dir / "comparison_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n  Summary: {summary_path}")

    # --- Write report ---
    print("\n5. Writing report...")
    report_path = write_comparison_report(
        comp_dir, comparisons, confidences, undecided_analyses, record_counts,
    )
    print(f"  Report: {report_path}")

    # --- Print headline numbers ---
    print("\n" + "=" * 70)
    print("HEADLINE RESULTS")
    print("=" * 70)
    for comp in comparisons:
        print(f"\n  {comp['pair']}:")
        print(f"    Topic:    {comp['topic']['raw_agreement_pct']}% "
              f"(κ={comp['topic']['kappa']})")
        print(f"    Subtopic: {comp['subtopic']['raw_agreement_pct']}% "
              f"(κ={comp['subtopic']['kappa']})")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
