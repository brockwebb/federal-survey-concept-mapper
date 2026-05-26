#!/usr/bin/env python3
"""v2 Stage 3 pair builder: candidate question pairs for harmonization.

Pure data step -- no API calls. Joins the v2 Stage 2 master classification
against the raw PublicSurveyQuestionsMap.csv to produce, for each source
survey (CPS, FoodAPS, AHS), the cartesian product of (source question,
ACS question) within each shared final_subtopic.

Logic mirrors v1's `src/core/survey_question_matching.py::generate_candidate_pairs`
with three changes:

  1. Pair keys are CSV row indices (the same `id` used by v2 Stage 1/2),
     not internal `survey_q_id` strings derived from a merge on the
     deduplicated `Question` text.
  2. FoodAPS is treated as one survey whose presence is "any of the four
     FoodAPS columns non-empty" -- v1 only used the household survey
     column.
  3. AHS is added as a brand-new source survey.

Run from v2/:
    python src/core/stage3_pair_builder.py

Outputs (relative to v2/output/stage3/candidate_pairs/):
    pairs_cps.csv
    pairs_foodaps.csv
    pairs_ahs.csv
    pair_summary.json
"""
from __future__ import annotations

import json
import sys
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
    required = {"source_surveys", "target_survey", "match_on",
                "data", "output"}
    missing = required - set(cfg.keys())
    if missing:
        die(f"Config missing top-level keys: {missing}")
    return cfg


# =============================================================================
# DATA LOADING
# =============================================================================

def load_questions_map(cfg: dict[str, Any]) -> pd.DataFrame:
    path = Path(cfg["data"]["questions_csv"])
    if not path.exists():
        die(f"Questions map CSV not found at {path.resolve()}")
    df = pd.read_csv(path)
    if "Question" not in df.columns:
        die("Questions map CSV missing 'Question' column")
    # The row index IS the id used by v2 Stage 1/2.
    df.index.name = "id"
    return df


def load_master(cfg: dict[str, Any]) -> pd.DataFrame:
    path = Path(cfg["data"]["master_dataset"])
    if not path.exists():
        die(f"v2 master not found at {path.resolve()}. "
            f"Run stage2_finalize.py first.")
    df = pd.read_csv(path)
    needed = ["id", "question", "final_topic", "final_subtopic"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        die(f"Master missing columns: {missing}")
    df["id"] = df["id"].astype(int)
    return df.set_index("id")[needed[1:]]


# =============================================================================
# PRESENCE MASK
# =============================================================================

# Text values that mean "absent" in the source CSV.
_ABSENT_STR_VALUES = {"", "nan", "NaN", "[NaN]", "None", "null"}


def _normalize_text(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    s = str(v).strip()
    if s in _ABSENT_STR_VALUES:
        return None
    return s


def presence_mask(
    qmap: pd.DataFrame, columns: list[str], label: str,
) -> pd.Series:
    """True for rows where at least one of `columns` carries a real
    question text (not NaN / empty / '[NaN]')."""
    mask = pd.Series(False, index=qmap.index)
    for c in columns:
        if c not in qmap.columns:
            die(f"{label}: survey column not found in CSV: {c!r}")
        mask = mask | qmap[c].apply(_normalize_text).notna()
    return mask


def survey_columns(cfg_block: dict[str, Any]) -> list[str]:
    if "columns" in cfg_block:
        return list(cfg_block["columns"])
    if "column" in cfg_block:
        return [cfg_block["column"]]
    die(f"Survey config block missing both 'column' and 'columns': "
        f"{cfg_block!r}")


# =============================================================================
# PAIR BUILDING
# =============================================================================

UNRESOLVABLE_TOPICS = {"Unresolvable"}


def build_pairs_for_survey(
    survey_key: str,
    survey_cfg: dict[str, Any],
    target_cfg: dict[str, Any],
    qmap: pd.DataFrame,
    master: pd.DataFrame,
    match_on: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Generate (source, ACS) pairs that share `match_on`. Returns the
    pair frame + per-survey diagnostics. NaN/empty text on either side
    drops the row before pairing."""
    name = survey_cfg["name"]
    s_cols = survey_columns(survey_cfg)
    a_cols = survey_columns(target_cfg)

    s_mask = presence_mask(qmap, s_cols, f"{name} source")
    a_mask = presence_mask(qmap, a_cols, f"{target_cfg['name']} target")

    s_ids_all = qmap.index[s_mask].tolist()
    a_ids_all = qmap.index[a_mask].tolist()

    # Attach master classifications. Rows without a master row are
    # dropped (shouldn't happen, but we guard).
    def attach(ids: list[int]) -> pd.DataFrame:
        df = master.reindex(ids).dropna(subset=[match_on])
        df = df[~df[match_on].isin(UNRESOLVABLE_TOPICS)]
        # Drop NaN/[NaN]/empty question text. The master always has a
        # `question` field but stage2_finalize substitutes "[NaN]" for
        # the small residual of empty question rows.
        df = df[df["question"].apply(_normalize_text).notna()]
        return df

    s_df = attach(s_ids_all)
    a_df = attach(a_ids_all)

    diag: dict[str, Any] = {
        "survey": name,
        "source_questions_in_map": int(len(s_ids_all)),
        "acs_questions_in_map": int(len(a_ids_all)),
        "source_after_master_join": int(len(s_df)),
        "acs_after_master_join": int(len(a_df)),
    }

    # Group by match key.
    s_groups = {k: g.index.tolist() for k, g in s_df.groupby(match_on)}
    a_groups = {k: g.index.tolist() for k, g in a_df.groupby(match_on)}
    shared = sorted(set(s_groups) & set(a_groups))
    diag["shared_subtopics"] = len(shared)

    rows: list[dict[str, Any]] = []
    pair_idx = 0
    for sub in shared:
        topic = master.loc[s_groups[sub][0], "final_topic"]
        for s_id in s_groups[sub]:
            s_text = master.loc[s_id, "question"]
            for a_id in a_groups[sub]:
                a_text = master.loc[a_id, "question"]
                rows.append({
                    "pair_id": f"{survey_key.upper()}_{pair_idx:05d}",
                    "source_survey": name,
                    "survey_q_id": int(s_id),
                    "survey_text": s_text,
                    "acs_q_id": int(a_id),
                    "acs_text": a_text,
                    "shared_topic": topic,
                    "shared_subtopic": sub,
                })
                pair_idx += 1

    pairs = pd.DataFrame(rows)
    if len(pairs):
        # Dedup safety: same (survey_q_id, acs_q_id) appearing twice.
        before = len(pairs)
        pairs = pairs.drop_duplicates(
            subset=["survey_q_id", "acs_q_id"]
        ).reset_index(drop=True)
        # Re-stamp pair_ids after dedup so they remain sequential.
        pairs["pair_id"] = [
            f"{survey_key.upper()}_{i:05d}" for i in range(len(pairs))
        ]
        diag["duplicates_dropped"] = before - len(pairs)
    else:
        diag["duplicates_dropped"] = 0

    diag["pairs_total"] = int(len(pairs))
    diag["pairs_by_subtopic_top5"] = (
        pairs["shared_subtopic"].value_counts().head(5).to_dict()
        if len(pairs) else {}
    )
    return pairs, diag


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    cfg = load_config()
    out_root = Path(cfg["output"]["output_dir"])
    pairs_dir = out_root / cfg["output"]["pairs_subdir"]
    pairs_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("v2 STAGE 3 PAIR BUILDER")
    print("=" * 70)

    print("\n1. Loading inputs...")
    qmap = load_questions_map(cfg)
    print(f"   questions map: {len(qmap)} rows")
    master = load_master(cfg)
    print(f"   master:        {len(master)} rows")

    match_on = cfg["match_on"]
    print(f"   matching on:   {match_on!r}")

    target_cfg = cfg["target_survey"]
    summary: dict[str, Any] = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "match_on": match_on,
        "target_survey": target_cfg["name"],
        "surveys": {},
    }
    total_pairs = 0

    print("\n2. Building pairs per survey...")
    for survey_key, survey_cfg in cfg["source_surveys"].items():
        print(f"\n   [{survey_key}] {survey_cfg['name']}")
        pairs, diag = build_pairs_for_survey(
            survey_key, survey_cfg, target_cfg, qmap, master, match_on,
        )
        out_path = pairs_dir / f"pairs_{survey_key}.csv"
        pairs.to_csv(out_path, index=False, encoding="utf-8")
        print(f"     source qs (map / after join): "
              f"{diag['source_questions_in_map']} / "
              f"{diag['source_after_master_join']}")
        print(f"     acs qs    (map / after join): "
              f"{diag['acs_questions_in_map']} / "
              f"{diag['acs_after_master_join']}")
        print(f"     shared subtopics: {diag['shared_subtopics']}")
        print(f"     pairs written:    {diag['pairs_total']:,}  "
              f"-> {out_path}")
        if diag["duplicates_dropped"]:
            print(f"     duplicates dropped: {diag['duplicates_dropped']}")
        summary["surveys"][survey_key] = diag
        total_pairs += diag["pairs_total"]

    summary["pairs_total_all_surveys"] = total_pairs
    summary_path = pairs_dir / cfg["output"]["pair_summary_json"]
    summary_path.write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8",
    )
    print(f"\n3. Wrote summary: {summary_path}")

    print("\n" + "=" * 70)
    print("HEADLINE")
    print("=" * 70)
    for k, d in summary["surveys"].items():
        print(f"  {k:<8s} {d['pairs_total']:>6,d} pairs   "
              f"({d['shared_subtopics']} shared subtopics)")
    print(f"  {'TOTAL':<8s} {total_pairs:>6,d} pairs")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
