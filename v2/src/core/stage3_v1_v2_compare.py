#!/usr/bin/env python3
"""v1 vs v2 Stage 3 reproducibility comparison (CPS + FoodAPS).

This is a REPRODUCIBILITY STUDY. The point of v2 is to confirm v1's
harmonization-barrier findings with different models. AHS has no v1
baseline (net new), so it is excluded here.

Stage 3 can diverge between v1 and v2 at TWO points, and this script
measures both separately:

  Level 1 -- pair generation. Candidate pairs are built from upstream
             subtopic classifications, which changed between v1 and v2.
             So the two versions may have generated different SETS of
             question pairs. We report how many pairs are common, v1-only,
             and v2-only.

  Level 2 -- barrier classification. For the pairs common to BOTH versions,
             did they receive the same barrier (L1) and feasibility code?
             Agreement + Cohen's kappa, computed only on the shared set.

CRITICAL -- the join key is the QUESTION TEXT pair, not pair_id. v1 pair
ids (CPS_0000) and v2 pair ids (CPS_00000) are independently generated and
do NOT correspond. v1 question ids (CPS_6, ACS_19) and v2 question ids
(CSV row integers) are different schemes. Normalized (source_text, acs_text)
is the only key common to both versions. Text normalization repairs the
cp1252-as-utf8 mojibake (e.g. "a<euro><tm>" for a curly apostrophe) so the
same question matches across versions.

Pure data step -- no API calls, no harness, no _smoke gate.

Run from v2/:
    python src/core/stage3_v1_v2_compare.py
    python src/core/stage3_v1_v2_compare.py --surveys cps
    python src/core/stage3_v1_v2_compare.py --surveys cps,foodaps

If the text join produces zero common pairs for a survey, that is FATAL --
it means the normalization is wrong, not that nothing matched.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from sklearn.metrics import cohen_kappa_score
    _HAVE_SK = True
except Exception:  # pragma: no cover
    _HAVE_SK = False


# =============================================================================
# PATHS (defaults assume cwd == v2/)
# =============================================================================

# v1 inputs (relative to v2/, i.e. one level up into docs/)
V1_VERDICTS = Path("../docs/stages/03_harmonization/data/analysis/final_verdicts.csv")
V1_PAIRS = {
    "cps": Path("../docs/stages/02_overlap/data/question_matching/cps/cps_candidate_pairs_all.csv"),
    "foodaps": Path("../docs/stages/02_overlap/data/question_matching/foodaps/foodaps_candidate_pairs_all.csv"),
}

# v2 inputs (relative to v2/)
V2_PAIRS_DIR = Path("output/stage3/candidate_pairs")
V2_RESULTS_DIR = Path("output/stage3/results")

OUT_DIR = Path("output/stage3/v1_v2_comparison")

# v1 final_verdicts survey-column values keyed by our survey key
V1_SURVEY_VALUE = {"cps": "CPS", "foodaps": "FOODAPS"}


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# TEXT NORMALIZATION
# =============================================================================

# Common cp1252-bytes-decoded-as-utf8 mojibake -> intended character.
# Covers the curly quotes/dashes that show up in the ACS question text.
_MOJIBAKE = {
    "\u00e2\u20ac\u2122": "'",   # right single quote '
    "\u00e2\u20ac\u02dc": "'",   # left single quote '
    "\u00e2\u20ac\u0153": '"',   # left double quote "
    "\u00e2\u20ac\u009d": '"',   # right double quote "
    "\u00e2\u20ac\u201d": "-",   # em dash
    "\u00e2\u20ac\u201c": "-",   # en dash
    "\u00e2\u20ac\u00a6": "...", # ellipsis
    "\u00e2\u20ac": '"',         # stray double-quote remnant
    "\u00c2\u00a0": " ",         # non-breaking space remnant
}

_FILL_RE = re.compile(r"\[[^\]]*\]")          # [FILL ...], [NaN], bracketed fills
_PAREN_FILL_RE = re.compile(r"\([^)]*fill[^)]*\)", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def _fix_mojibake(s: str) -> str:
    for bad, good in _MOJIBAKE.items():
        if bad in s:
            s = s.replace(bad, good)
    # Also try the generic utf8/cp1252 round-trip repair as a fallback.
    if "\u00e2" in s or "\u00c2" in s:
        try:
            s = s.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass
    return s


def normalize_text(v: Any) -> str:
    """Normalize question text into a stable join key. Repairs mojibake,
    removes bracketed fill instructions (which can render differently across
    versions), lowercases, strips punctuation runs, collapses whitespace."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v)
    s = _fix_mojibake(s)
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2014", "-").replace("\u2013", "-")
    s = _FILL_RE.sub(" ", s)
    s = _PAREN_FILL_RE.sub(" ", s)
    s = s.lower()
    # keep alphanumerics and spaces only; drop the rest (punctuation/quotes)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def pair_key(src: Any, acs: Any) -> str:
    return normalize_text(src) + " ||| " + normalize_text(acs)


# =============================================================================
# LOADERS
# =============================================================================

def load_v1(survey_key: str) -> pd.DataFrame:
    """Return v1 frame: [pair_key, v1_pair_id, v1_L1, v1_feas]."""
    pairs_path = V1_PAIRS[survey_key]
    if not pairs_path.exists():
        die(f"v1 pairs not found: {pairs_path.resolve()}")
    if not V1_VERDICTS.exists():
        die(f"v1 verdicts not found: {V1_VERDICTS.resolve()}")

    pairs = pd.read_csv(pairs_path, encoding="utf-8")
    for c in ("pair_id", "survey_text", "acs_text"):
        if c not in pairs.columns:
            die(f"v1 pairs {pairs_path.name} missing column {c!r}")

    verdicts = pd.read_csv(V1_VERDICTS, encoding="utf-8")
    for c in ("pair_id", "survey", "final_L1", "final_feasibility"):
        if c not in verdicts.columns:
            die(f"v1 verdicts missing column {c!r}")
    verdicts = verdicts[verdicts["survey"] == V1_SURVEY_VALUE[survey_key]].copy()

    df = pairs.merge(
        verdicts[["pair_id", "final_L1", "final_feasibility"]],
        on="pair_id", how="inner",
    )
    df["pair_key"] = [pair_key(s, a) for s, a in zip(df["survey_text"], df["acs_text"])]
    df = df.rename(columns={
        "pair_id": "v1_pair_id",
        "final_L1": "v1_L1",
        "final_feasibility": "v1_feas",
    })
    return df[["pair_key", "v1_pair_id", "v1_L1", "v1_feas",
               "survey_text", "acs_text"]]


def load_v2(survey_key: str) -> pd.DataFrame:
    """Return v2 frame: [pair_key, v2_pair_id, v2_L1, v2_feas].

    The v2 final_barrier_classifications.csv already carries survey_text and
    acs_text, so no merge with the pairs file is needed. The final L1 column
    is 'final_classification' and feasibility is 'final_feasibility'.
    """
    final_path = V2_RESULTS_DIR / survey_key / "final_barrier_classifications.csv"
    if not final_path.exists():
        die(f"v2 final not found: {final_path.resolve()}")

    final = pd.read_csv(final_path, encoding="utf-8")
    needed = ["pair_id", "survey_text", "acs_text",
              "final_classification", "final_feasibility"]
    missing = [c for c in needed if c not in final.columns]
    if missing:
        die(f"v2 final missing columns {missing}; have {list(final.columns)}")

    df = final[needed].copy()
    df["pair_key"] = [pair_key(s, a)
                      for s, a in zip(df["survey_text"], df["acs_text"])]
    df = df.rename(columns={
        "pair_id": "v2_pair_id",
        "final_classification": "v2_L1",
        "final_feasibility": "v2_feas",
    })
    return df[["pair_key", "v2_pair_id", "v2_L1", "v2_feas"]]


def _dedup_on_key(df: pd.DataFrame, label: str) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df = df[df["pair_key"].str.strip(" |") != ""]  # drop empty-text keys
    df = df.drop_duplicates(subset=["pair_key"], keep="first").reset_index(drop=True)
    return df, before - len(df)


# =============================================================================
# METRICS
# =============================================================================

def kappa(a: pd.Series, b: pd.Series) -> float | None:
    if not _HAVE_SK:
        return None
    aa = a.fillna("NONE").astype(str)
    bb = b.fillna("NONE").astype(str)
    try:
        return round(float(cohen_kappa_score(aa, bb)), 4)
    except Exception:
        return None


def confusion(a: pd.Series, b: pd.Series) -> pd.DataFrame:
    return pd.crosstab(
        a.fillna("NONE").astype(str),
        b.fillna("NONE").astype(str),
        dropna=False, margins=True,
    )


def compare_survey(survey_key: str) -> dict[str, Any]:
    v1 = load_v1(survey_key)
    v2 = load_v2(survey_key)

    v1, v1_dups = _dedup_on_key(v1, "v1")
    v2, v2_dups = _dedup_on_key(v2, "v2")

    v1_keys = set(v1["pair_key"])
    v2_keys = set(v2["pair_key"])
    common = v1_keys & v2_keys
    v1_only = v1_keys - v2_keys
    v2_only = v2_keys - v1_keys
    union = v1_keys | v2_keys

    if not common:
        die(f"[{survey_key}] ZERO common pairs after text join. "
            f"The normalization is almost certainly wrong (v1={len(v1_keys)}, "
            f"v2={len(v2_keys)}). Inspect normalize_text() and sample texts.")

    merged = v1.merge(v2, on="pair_key", how="inner")

    # Level 2 agreement on common pairs
    l1_match = (merged["v1_L1"].astype(str) == merged["v2_L1"].astype(str))
    feas_match = (merged["v1_feas"].astype(str) == merged["v2_feas"].astype(str))
    both = l1_match & feas_match

    level1 = {
        "v1_pairs": len(v1_keys),
        "v2_pairs": len(v2_keys),
        "common_pairs": len(common),
        "v1_only": len(v1_only),
        "v2_only": len(v2_only),
        "jaccard": round(len(common) / len(union), 4) if union else 0.0,
        "v1_dups_dropped": v1_dups,
        "v2_dups_dropped": v2_dups,
    }
    level2 = {
        "n_compared": int(len(merged)),
        "l1_agreement_pct": round(float(l1_match.mean()) * 100, 2),
        "feasibility_agreement_pct": round(float(feas_match.mean()) * 100, 2),
        "both_agreement_pct": round(float(both.mean()) * 100, 2),
        "l1_kappa": kappa(merged["v1_L1"], merged["v2_L1"]),
        "feasibility_kappa": kappa(merged["v1_feas"], merged["v2_feas"]),
    }

    # Sample matched tuples to prove the join is real
    sample = merged.head(5)[["v1_pair_id", "v2_pair_id", "v1_L1", "v2_L1",
                             "v1_feas", "v2_feas"]].to_dict("records")

    # Confusion matrices
    l1_conf = confusion(merged["v1_L1"], merged["v2_L1"])
    feas_conf = confusion(merged["v1_feas"], merged["v2_feas"])

    # Changed pairs
    changed = merged[~both].copy()

    return {
        "survey": survey_key,
        "level1": level1,
        "level2": level2,
        "sample_matches": sample,
        "_merged": merged,
        "_l1_conf": l1_conf,
        "_feas_conf": feas_conf,
        "_changed": changed,
    }


# =============================================================================
# REPORT
# =============================================================================

def write_report(results: list[dict[str, Any]], out_dir: Path) -> Path:
    L: list[str] = []
    L.append("# v1 vs v2 Stage 3 Reproducibility Comparison")
    L.append("")
    L.append("Confirmation run: do v1 and v2 produce the same harmonization-")
    L.append("barrier findings with different models? Two-level analysis:")
    L.append("pair generation (Level 1) and barrier classification (Level 2).")
    L.append("Join key is normalized question-text pair, not pair_id.")
    L.append("AHS excluded (no v1 baseline).")
    L.append("")

    for r in results:
        s = r["survey"].upper()
        l1, l2 = r["level1"], r["level2"]
        L.append(f"## {s}")
        L.append("")
        L.append("### Level 1 -- pair-set reproducibility")
        L.append(f"- v1 pairs: {l1['v1_pairs']:,}")
        L.append(f"- v2 pairs: {l1['v2_pairs']:,}")
        L.append(f"- common (same text pair): {l1['common_pairs']:,}")
        L.append(f"- v1-only: {l1['v1_only']:,}")
        L.append(f"- v2-only: {l1['v2_only']:,}")
        L.append(f"- Jaccard overlap: {l1['jaccard']:.4f}")
        if l1["v1_dups_dropped"] or l1["v2_dups_dropped"]:
            L.append(f"- duplicate text-keys dropped (v1/v2): "
                     f"{l1['v1_dups_dropped']}/{l1['v2_dups_dropped']}")
        L.append("")
        L.append("### Level 2 -- classification agreement (common pairs)")
        L.append(f"- pairs compared: {l2['n_compared']:,}")
        L.append(f"- barrier L1 agreement: {l2['l1_agreement_pct']}%  "
                 f"(kappa={l2['l1_kappa']})")
        L.append(f"- feasibility agreement: {l2['feasibility_agreement_pct']}%  "
                 f"(kappa={l2['feasibility_kappa']})")
        L.append(f"- both agree: {l2['both_agreement_pct']}%")
        L.append("")
        L.append("### Sample matched pairs (join sanity check)")
        L.append("| v1_pair_id | v2_pair_id | v1_L1 | v2_L1 | v1_feas | v2_feas |")
        L.append("|---|---|---|---|---|---|")
        for m in r["sample_matches"]:
            L.append(f"| {m['v1_pair_id']} | {m['v2_pair_id']} | "
                     f"{m['v1_L1']} | {m['v2_L1']} | "
                     f"{m['v1_feas']} | {m['v2_feas']} |")
        L.append("")
        L.append("### Barrier L1 confusion (v1 rows x v2 cols)")
        L.append("```")
        L.append(r["_l1_conf"].to_string())
        L.append("```")
        L.append("")
        L.append("### Feasibility confusion (v1 rows x v2 cols)")
        L.append("```")
        L.append(r["_feas_conf"].to_string())
        L.append("```")
        L.append("")

    path = out_dir / "v1_v2_stage3_report.md"
    path.write_text("\n".join(L), encoding="utf-8")
    return path


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="v1 vs v2 Stage 3 reproducibility comparison",
    )
    ap.add_argument("--surveys", default="cps,foodaps",
                    help="comma-separated subset of: cps, foodaps "
                         "(AHS has no v1 baseline)")
    args = ap.parse_args()
    keys = [k.strip() for k in args.surveys.split(",") if k.strip()]
    for k in keys:
        if k not in V1_PAIRS:
            die(f"survey {k!r} has no v1 baseline. Valid: {list(V1_PAIRS)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("v1 vs v2 STAGE 3 REPRODUCIBILITY COMPARISON")
    print("=" * 70)
    if not _HAVE_SK:
        print("WARNING: scikit-learn not available; kappa will be None.")

    results: list[dict[str, Any]] = []
    combined_rows = []
    for k in keys:
        print(f"\n[{k}] comparing...")
        r = compare_survey(k)
        results.append(r)

        # write per-survey artifacts
        r["_l1_conf"].to_csv(OUT_DIR / f"v1_v2_barrier_confusion_{k}.csv",
                             encoding="utf-8")
        r["_feas_conf"].to_csv(OUT_DIR / f"v1_v2_feasibility_confusion_{k}.csv",
                               encoding="utf-8")
        changed_cols = ["pair_key", "v1_pair_id", "v2_pair_id",
                        "v1_L1", "v2_L1", "v1_feas", "v2_feas",
                        "survey_text", "acs_text"]
        have = [c for c in changed_cols if c in r["_changed"].columns]
        r["_changed"][have].to_csv(
            OUT_DIR / f"v1_v2_changed_pairs_{k}.csv",
            index=False, encoding="utf-8")

        m = r["_merged"][["v1_L1", "v2_L1", "v1_feas", "v2_feas"]].copy()
        m["survey"] = k
        combined_rows.append(m)

        l1, l2 = r["level1"], r["level2"]
        print(f"  Level 1: v1={l1['v1_pairs']:,} v2={l1['v2_pairs']:,} "
              f"common={l1['common_pairs']:,} jaccard={l1['jaccard']:.3f}")
        print(f"  Level 2: L1 agree={l2['l1_agreement_pct']}% "
              f"(k={l2['l1_kappa']})  "
              f"feas agree={l2['feasibility_agreement_pct']}% "
              f"(k={l2['feasibility_kappa']})  "
              f"both={l2['both_agreement_pct']}%")

    # combined metrics across surveys
    combined = {}
    if combined_rows:
        allm = pd.concat(combined_rows, ignore_index=True)
        l1m = (allm["v1_L1"].astype(str) == allm["v2_L1"].astype(str))
        fm = (allm["v1_feas"].astype(str) == allm["v2_feas"].astype(str))
        combined = {
            "n_compared": int(len(allm)),
            "l1_agreement_pct": round(float(l1m.mean()) * 100, 2),
            "feasibility_agreement_pct": round(float(fm.mean()) * 100, 2),
            "both_agreement_pct": round(float((l1m & fm).mean()) * 100, 2),
            "l1_kappa": kappa(allm["v1_L1"], allm["v2_L1"]),
            "feasibility_kappa": kappa(allm["v1_feas"], allm["v2_feas"]),
        }

    # write summary jsons
    (OUT_DIR / "v1_v2_pairset_overlap.json").write_text(
        json.dumps({r["survey"]: r["level1"] for r in results}, indent=2),
        encoding="utf-8")
    (OUT_DIR / "v1_v2_classification_agreement.json").write_text(
        json.dumps(
            {**{r["survey"]: r["level2"] for r in results},
             "combined": combined},
            indent=2),
        encoding="utf-8")

    report_path = write_report(results, OUT_DIR)
    print(f"\nWrote report: {report_path}")
    print(f"Wrote artifacts to: {OUT_DIR}")

    print("\n" + "=" * 70)
    print("HEADLINE")
    print("=" * 70)
    for r in results:
        l1, l2 = r["level1"], r["level2"]
        print(f"  {r['survey'].upper():<8s} "
              f"pairset overlap {l1['jaccard']*100:.1f}%  |  "
              f"L1 {l2['l1_agreement_pct']}%  feas "
              f"{l2['feasibility_agreement_pct']}%")
    if combined:
        print(f"  {'COMBINED':<8s} "
              f"L1 {combined['l1_agreement_pct']}% "
              f"(k={combined['l1_kappa']})  feas "
              f"{combined['feasibility_agreement_pct']}% "
              f"(k={combined['feasibility_kappa']})")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
