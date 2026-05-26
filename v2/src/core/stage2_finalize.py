#!/usr/bin/env python3
"""v2 Stage 2 finalize: assemble master dataset + compare against v1.

Two products in one script:

  1. v2/output/stage2/master_dataset.csv — one row per question with the
     final v2 topic/subtopic decision. Built from the per-rater Stage 1
     JSONL files and the disagreement resolutions produced by
     stage2_adjudicate.py.
  2. A v1-vs-v2 comparison: report.md, changed_questions.csv, summary.json.

Pure data step. No API calls, no harness. All paths come from
config/stage2.yaml under the `finalize:` block. Run from the v2/
directory:

    python src/core/stage2_finalize.py

Halts loudly if any input is missing, if any disagreement lacks a
resolution row, or if the assembled master isn't exactly
finalize.expected_row_count rows.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score


CONFIG_PATH = Path("config/stage2.yaml")


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
    required = {"data", "stage1", "output", "finalize"}
    missing = required - set(cfg.keys())
    if missing:
        die(f"Config missing required top-level keys: {missing}")
    required_fin = {
        "v1_master", "v2_master", "comparison_report",
        "changed_questions_csv", "comparison_summary_json",
        "expected_row_count",
    }
    missing_fin = required_fin - set(cfg["finalize"].keys())
    if missing_fin:
        die(f"finalize: block missing keys: {missing_fin}")
    return cfg


# =============================================================================
# LOADERS
# =============================================================================

def load_questions(cfg: dict[str, Any]) -> pd.DataFrame:
    """Same shape as stage2_adjudicate.load_questions — id, question,
    primary_survey, with id = the row index of the source CSV."""
    path = Path(cfg["data"]["questions_csv"])
    if not path.exists():
        die(f"Questions CSV not found at {path.resolve()}")
    df = pd.read_csv(path)
    rows = []
    for idx, row in df.iterrows():
        question = row["Question"]
        surveys = [c for c in df.columns
                   if c != "Question" and pd.notna(row[c])]
        rows.append({
            "id": int(idx),
            "primary_survey": surveys[0] if surveys else "Unknown",
            "question": str(question) if pd.notna(question) else "[NaN]",
        })
    return pd.DataFrame(rows)


def load_rater_jsonl(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        die(f"{label}: file not found at {path.resolve()}")
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    df = pd.DataFrame(records)
    for col in ("id", "primary_topic", "primary_subtopic", "confidence"):
        if col not in df.columns:
            die(f"{label}: JSONL missing required column {col!r}")
    df["id"] = df["id"].astype(int)
    if df["id"].duplicated().any():
        die(f"{label}: duplicate ids in JSONL")
    return df


def load_resolutions(path: Path) -> pd.DataFrame:
    if not path.exists():
        die(f"Resolutions CSV not found at {path.resolve()}. "
            f"Run stage2_adjudicate.py first.")
    df = pd.read_csv(path)
    for col in ("id", "decision"):
        if col not in df.columns:
            die(f"Resolutions CSV missing required column {col!r}")
    df["id"] = df["id"].astype(int)
    if df["id"].duplicated().any():
        die(f"Resolutions CSV has duplicate ids "
            f"(n={df['id'].duplicated().sum()})")
    failed_mask = df["decision"].isin(
        ["failed", "request_failed", "parse_failed"]
    )
    if failed_mask.any():
        n = int(failed_mask.sum())
        die(f"Resolutions CSV has {n} failed/unresolved arbitration rows. "
            f"Run `python src/core/stage2_adjudicate.py --retry-failed` "
            f"and rerun.")
    return df


def load_v1_master(path: Path) -> pd.DataFrame:
    if not path.exists():
        die(f"v1 master not found at {path.resolve()}")
    df = pd.read_csv(path)
    needed = ["id", "final_topic", "final_subtopic", "decision_method"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        die(f"v1 master missing columns: {missing}")
    df = df[needed].copy()
    df["id"] = df["id"].astype(int)
    if df["id"].duplicated().any():
        die("v1 master has duplicate ids")
    return df.rename(columns={
        "final_topic": "v1_final_topic",
        "final_subtopic": "v1_final_subtopic",
        "decision_method": "v1_decision_method",
    })


# =============================================================================
# MASTER DATASET ASSEMBLY
# =============================================================================

# Output column order — matches the spec in
# cc_tasks/2026-05-22_stage2_finalize_and_compare.md.
MASTER_COLS = [
    "id", "question", "primary_survey",
    "final_topic", "final_subtopic", "final_confidence",
    "decision_method", "is_dual_modal",
    "secondary_primary_topic", "secondary_primary_subtopic",
    "all_relevant_subtopics",
    "original_rater_a_topic", "original_rater_a_subtopic",
    "original_rater_a_confidence",
    "original_rater_b_topic", "original_rater_b_subtopic",
    "original_rater_b_confidence",
]


def build_master_dataset(
    rater_a: pd.DataFrame,
    rater_b: pd.DataFrame,
    resolutions: pd.DataFrame,
    questions: pd.DataFrame,
    expected_rows: int,
) -> pd.DataFrame:
    """Merge raters on id, split into agreements/disagreements, fill the
    final fields from rater_a for agreements and from the arbitrator's
    resolution row for disagreements. Returns one row per question."""
    cols = ["id", "primary_topic", "primary_subtopic", "confidence"]
    merged = rater_a[cols].merge(
        rater_b[cols], on="id", suffixes=("_a", "_b"),
        how="inner", validate="one_to_one",
    )
    if len(merged) != expected_rows:
        die(f"Rater merge produced {len(merged)} rows, expected "
            f"{expected_rows}. rater_a={len(rater_a)}, "
            f"rater_b={len(rater_b)}.")

    agree_mask = (
        (merged["primary_topic_a"] == merged["primary_topic_b"])
        & (merged["primary_subtopic_a"] == merged["primary_subtopic_b"])
    )
    agreements = merged[agree_mask].copy()
    disagreements = merged[~agree_mask].copy()

    # --- Agreements ----------------------------------------------------------
    agreements["final_topic"] = agreements["primary_topic_a"]
    agreements["final_subtopic"] = agreements["primary_subtopic_a"]
    agreements["final_confidence"] = agreements[
        ["confidence_a", "confidence_b"]
    ].max(axis=1)
    agreements["decision_method"] = "agreement"
    agreements["is_dual_modal"] = False
    agreements["secondary_primary_topic"] = pd.NA
    agreements["secondary_primary_subtopic"] = pd.NA
    agreements["all_relevant_subtopics"] = agreements.apply(
        lambda r: json.dumps([f"{r['final_topic']}.{r['final_subtopic']}"]),
        axis=1,
    )

    # --- Disagreements: join with resolutions --------------------------------
    res_cols = [
        "id",
        "decision",
        "primary_topic",
        "primary_subtopic",
        "primary_confidence",
        "is_dual_modal",
        "secondary_primary_topic",
        "secondary_primary_subtopic",
        "all_relevant_subtopics",
    ]
    missing_cols = [c for c in res_cols if c not in resolutions.columns]
    if missing_cols:
        die(f"Resolutions CSV missing columns: {missing_cols}")

    disagreements = disagreements.merge(
        resolutions[res_cols], on="id", how="left", validate="one_to_one",
    )
    unresolved = disagreements[disagreements["decision"].isna()]
    if len(unresolved):
        ids = unresolved["id"].head(10).tolist()
        die(f"{len(unresolved)} disagreements have no resolution row in "
            f"resolutions CSV. First ids: {ids}")

    disagreements["final_topic"] = disagreements["primary_topic"]
    disagreements["final_subtopic"] = disagreements["primary_subtopic"]
    disagreements["final_confidence"] = disagreements["primary_confidence"]
    disagreements["decision_method"] = disagreements["decision"]

    # Coerce is_dual_modal to bool; resolutions CSV round-trips it as a
    # string under some pandas/csv combinations.
    def _to_bool(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() == "true"
        return bool(v)
    disagreements["is_dual_modal"] = disagreements["is_dual_modal"].apply(_to_bool)

    # --- Combine -------------------------------------------------------------
    keep = [
        "id",
        "final_topic", "final_subtopic", "final_confidence",
        "decision_method", "is_dual_modal",
        "secondary_primary_topic", "secondary_primary_subtopic",
        "all_relevant_subtopics",
        "primary_topic_a", "primary_subtopic_a", "confidence_a",
        "primary_topic_b", "primary_subtopic_b", "confidence_b",
    ]
    master = pd.concat(
        [agreements[keep], disagreements[keep]], ignore_index=True,
    )
    master = master.sort_values("id").reset_index(drop=True)

    # --- Attach question text / primary_survey -------------------------------
    master = master.merge(
        questions[["id", "question", "primary_survey"]],
        on="id", how="left", validate="one_to_one",
    )

    # --- Validate ------------------------------------------------------------
    if len(master) != expected_rows:
        die(f"Master has {len(master)} rows, expected {expected_rows}.")
    if master["final_topic"].isna().any():
        die("Master has rows with null final_topic.")
    if master["final_subtopic"].isna().any():
        die("Master has rows with null final_subtopic.")
    if master["question"].isna().any():
        die("Master has rows whose question text didn't merge from source.")

    master = master.rename(columns={
        "primary_topic_a": "original_rater_a_topic",
        "primary_subtopic_a": "original_rater_a_subtopic",
        "confidence_a": "original_rater_a_confidence",
        "primary_topic_b": "original_rater_b_topic",
        "primary_subtopic_b": "original_rater_b_subtopic",
        "confidence_b": "original_rater_b_confidence",
    })
    return master[MASTER_COLS]


# =============================================================================
# v1 vs v2 COMPARISON
# =============================================================================

def compare_v1_v2(
    v2_master: pd.DataFrame,
    v1: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Inner-join on id. Returns (summary_dict, joined_df). Joined has both
    sides labeled v1_/v2_."""
    v2_slim = v2_master[
        ["id", "question", "primary_survey",
         "final_topic", "final_subtopic", "decision_method"]
    ].rename(columns={
        "final_topic": "v2_final_topic",
        "final_subtopic": "v2_final_subtopic",
        "decision_method": "v2_decision_method",
    })
    joined = v2_slim.merge(v1, on="id", how="inner", validate="one_to_one")

    if len(joined) != len(v2_master) or len(joined) != len(v1):
        print(f"WARNING: row-count mismatch — comparing on intersection of "
              f"{len(joined)} ids "
              f"(v2={len(v2_master)}, v1={len(v1)}).", flush=True)

    topic_match = (joined["v1_final_topic"] == joined["v2_final_topic"])
    sub_match = (joined["v1_final_subtopic"] == joined["v2_final_subtopic"])
    full_match = topic_match & sub_match
    n = len(joined)

    summary: dict[str, Any] = {
        "n_compared": n,
        "topic_agreement_pct": round(100.0 * float(topic_match.mean()), 3),
        "subtopic_agreement_pct": round(100.0 * float(sub_match.mean()), 3),
        "full_agreement_pct": round(100.0 * float(full_match.mean()), 3),
        "topic_kappa": round(float(cohen_kappa_score(
            joined["v1_final_topic"], joined["v2_final_topic"],
        )), 4),
        "subtopic_kappa": round(float(cohen_kappa_score(
            joined["v1_final_subtopic"], joined["v2_final_subtopic"],
        )), 4),
    }

    # Agreement broken down by v1 decision_method
    by_v1 = []
    for method, grp in joined.groupby("v1_decision_method", dropna=False):
        tm = (grp["v1_final_topic"] == grp["v2_final_topic"])
        sm = (grp["v1_final_subtopic"] == grp["v2_final_subtopic"])
        by_v1.append({
            "v1_decision_method": str(method),
            "n": int(len(grp)),
            "topic_agreement_pct": round(100.0 * float(tm.mean()), 3),
            "full_agreement_pct": round(100.0 * float((tm & sm).mean()), 3),
        })
    summary["agreement_by_v1_decision_method"] = sorted(
        by_v1, key=lambda r: r["n"], reverse=True,
    )

    # Agreement broken down by v2 decision_method
    by_v2 = []
    for method, grp in joined.groupby("v2_decision_method", dropna=False):
        tm = (grp["v1_final_topic"] == grp["v2_final_topic"])
        sm = (grp["v1_final_subtopic"] == grp["v2_final_subtopic"])
        by_v2.append({
            "v2_decision_method": str(method),
            "n": int(len(grp)),
            "topic_agreement_pct": round(100.0 * float(tm.mean()), 3),
            "full_agreement_pct": round(100.0 * float((tm & sm).mean()), 3),
        })
    summary["agreement_by_v2_decision_method"] = sorted(
        by_v2, key=lambda r: r["n"], reverse=True,
    )

    # Decision method migration crosstab (v1 row → v2 col)
    migration = pd.crosstab(
        joined["v1_decision_method"], joined["v2_decision_method"],
    )
    summary["decision_method_migration"] = {
        str(v1m): {str(v2m): int(migration.loc[v1m, v2m])
                   for v2m in migration.columns}
        for v1m in migration.index
    }

    # Topic confusion — only rows where the topic differs.
    diff = joined[~topic_match]
    topic_confusion = (
        diff.groupby(["v1_final_topic", "v2_final_topic"])
        .size().reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    summary["topic_confusion"] = [
        {"v1_final_topic": str(r["v1_final_topic"]),
         "v2_final_topic": str(r["v2_final_topic"]),
         "n": int(r["n"])}
        for _, r in topic_confusion.iterrows()
    ]

    return summary, joined


def render_report(summary: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# v1 vs v2 Classification Comparison")
    L.append("")
    L.append("## Headline")
    L.append("")
    L.append(f"- n compared:           **{summary['n_compared']:,}**")
    L.append(f"- topic agreement:      **{summary['topic_agreement_pct']}%**")
    L.append(f"- subtopic agreement:   **{summary['subtopic_agreement_pct']}%**")
    L.append(f"- full agreement:       **{summary['full_agreement_pct']}%**")
    L.append(f"- topic Cohen κ:        **{summary['topic_kappa']}**")
    L.append(f"- subtopic Cohen κ:     **{summary['subtopic_kappa']}**")
    L.append("")

    L.append("## Agreement by v1 decision_method")
    L.append("")
    L.append("| v1 method | n | topic agree % | full agree % |")
    L.append("|-----------|---|---------------|--------------|")
    for r in summary["agreement_by_v1_decision_method"]:
        L.append(f"| {r['v1_decision_method']} | {r['n']} | "
                 f"{r['topic_agreement_pct']} | {r['full_agreement_pct']} |")
    L.append("")

    L.append("## Agreement by v2 decision_method")
    L.append("")
    L.append("| v2 method | n | topic agree % | full agree % |")
    L.append("|-----------|---|---------------|--------------|")
    for r in summary["agreement_by_v2_decision_method"]:
        L.append(f"| {r['v2_decision_method']} | {r['n']} | "
                 f"{r['topic_agreement_pct']} | {r['full_agreement_pct']} |")
    L.append("")

    L.append("## Decision method migration (v1 row → v2 col)")
    L.append("")
    mig = summary["decision_method_migration"]
    v2_methods = sorted({m for d in mig.values() for m in d.keys()})
    L.append("| v1 \\ v2 | " + " | ".join(v2_methods) + " | total |")
    L.append("|" + "---|" * (len(v2_methods) + 2))
    for v1m in sorted(mig.keys()):
        row = mig[v1m]
        cells = [str(row.get(m, 0)) for m in v2_methods]
        L.append(f"| {v1m} | " + " | ".join(cells)
                 + f" | {sum(row.values())} |")
    L.append("")

    L.append("## Topic confusion (rows where v1 topic ≠ v2 topic)")
    L.append("")
    L.append("| v1 topic | v2 topic | n |")
    L.append("|---|---|---|")
    for r in summary["topic_confusion"][:30]:
        L.append(f"| {r['v1_final_topic']} | {r['v2_final_topic']} | {r['n']} |")
    if len(summary["topic_confusion"]) > 30:
        L.append("")
        L.append(f"_(top 30 of {len(summary['topic_confusion'])} shown; "
                 f"full data in summary JSON)_")
    L.append("")
    return "\n".join(L)


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    cfg = load_config()
    fin = cfg["finalize"]
    expected = int(fin["expected_row_count"])

    print("=" * 70)
    print("v2 STAGE 2 FINALIZE")
    print("=" * 70)

    print("\n1. Loading inputs...")
    questions = load_questions(cfg)
    print(f"   questions: {len(questions)} rows")

    rater_a = load_rater_jsonl(
        Path(cfg["stage1"]["rater_a_results"]), "rater_a",
    )
    rater_b = load_rater_jsonl(
        Path(cfg["stage1"]["rater_b_results"]), "rater_b",
    )
    print(f"   rater_a:   {len(rater_a)} rows")
    print(f"   rater_b:   {len(rater_b)} rows")

    out_dir = Path(cfg["output"]["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    res_path = out_dir / cfg["output"]["all_resolutions_csv"]
    resolutions = load_resolutions(res_path)
    print(f"   resolutions: {len(resolutions)} rows from {res_path}")

    # ----- Part 1: master dataset -------------------------------------------
    print("\n2. Building v2 master dataset...")
    master = build_master_dataset(
        rater_a, rater_b, resolutions, questions, expected,
    )
    master_path = out_dir / fin["v2_master"]
    master.to_csv(master_path, index=False, encoding="utf-8")
    print(f"   wrote {master_path}  ({len(master)} rows)")

    print("\n   v2 decision_method breakdown:")
    dm_counts = master["decision_method"].value_counts()
    for k, n in dm_counts.items():
        print(f"     {k:<20s} {n:>5d}  ({100.0 * n / len(master):.2f}%)")

    # ----- Part 2: v1 vs v2 comparison --------------------------------------
    print("\n3. Comparing v1 vs v2...")
    v1_path = Path(fin["v1_master"])
    v1 = load_v1_master(v1_path)
    print(f"   v1 master: {len(v1)} rows from {v1_path}")

    summary, joined = compare_v1_v2(master, v1)

    diff_mask = (
        (joined["v1_final_topic"] != joined["v2_final_topic"])
        | (joined["v1_final_subtopic"] != joined["v2_final_subtopic"])
    )
    changed = joined[diff_mask].copy()
    changed_path = out_dir / fin["changed_questions_csv"]
    changed.to_csv(changed_path, index=False, encoding="utf-8")
    print(f"   wrote {changed_path}  ({len(changed)} changed)")

    report_md = render_report(summary)
    report_path = out_dir / fin["comparison_report"]
    report_path.write_text(report_md, encoding="utf-8")
    print(f"   wrote {report_path}")

    summary_path = out_dir / fin["comparison_summary_json"]
    summary_path.write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8",
    )
    print(f"   wrote {summary_path}")

    print("\n" + "=" * 70)
    print("HEADLINE")
    print("=" * 70)
    print(f"  n compared:           {summary['n_compared']:,}")
    print(f"  topic agreement:      {summary['topic_agreement_pct']}%")
    print(f"  subtopic agreement:   {summary['subtopic_agreement_pct']}%")
    print(f"  full agreement:       {summary['full_agreement_pct']}%")
    print(f"  topic Cohen κ:        {summary['topic_kappa']}")
    print(f"  subtopic Cohen κ:     {summary['subtopic_kappa']}")
    print(f"  changed questions:    {len(changed):,}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
