"""Validation: Question counts from raw source data + corrected question-level results.

Computes ground-truth counts at three levels:
  1. Instrument-level (column counts from raw CSV)
  2. Survey-level (aggregated across multi-instrument surveys like FoodAPS)
  3. Question-level results (corrected for dual-subtopic inflation)

All other scripts and documents should validate against the output JSON.

Sources:
  data/raw/PublicSurveyQuestionsMap.csv
  docs/stages/03_harmonization/data/analysis/stage4_question_level.csv
  docs/stages/03_harmonization/data/analysis/final_verdicts.csv

Outputs:
  docs/validation/question_counts.json  (machine-readable, all levels)
  docs/validation/question_counts.log   (human-readable summary)

Run: python src/validation/validate_question_counts.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW_SOURCE = REPO / "data" / "raw" / "PublicSurveyQuestionsMap.csv"
QUESTION_LEVEL = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage4_question_level.csv"
FINAL_VERDICTS = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "final_verdicts.csv"
OUT_DIR = REPO / "docs" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================================
# 1. INSTRUMENT-LEVEL COUNTS
# =====================================================================
raw = pd.read_csv(RAW_SOURCE)
survey_cols = [c for c in raw.columns if c != "Question" and not c.startswith("Unnamed")]

instrument_counts = {}
for col in survey_cols:
    instrument_counts[col] = int(
        (raw[col].notna() & (raw[col].astype(str).str.strip() != "")).sum()
    )

# =====================================================================
# 2. SURVEY-LEVEL COUNTS (instrument → survey program)
# =====================================================================
INSTRUMENT_TO_SURVEY = {
    "American Community Survey (ACS)": "ACS",
    "Survey of Income and Program Participation (SIPP)": "SIPP",
    "Consumer Expenditure Survey (CE)": "CE",
    "American Housing Survey (AHS)": "AHS",
    "Current Population Survey (CPS)": "CPS",
    "Food Acquisition and Purchase Survey (FoodAPS) Initial Interview/Household Survey": "FoodAPS",
    "Food Acquisition and Purchase Survey (FoodAPS) Profile and Income Questionnaire": "FoodAPS",
    "Food Acquisition and Purchase Survey (FoodAPS) Debriefing Questionnaire": "FoodAPS",
    "FoodAPS food Log": "FoodAPS",
    "National Health Interview Survey (NHIS)": "NHIS",
    "National Sample Survey of Registered Nurses (NSSRN)": "NSSRN",
    "National Survey of Children's Health (NSCH)": "NSCH",
    "National Survey of Children's Health Topical Questionaire (Children, 0-5 years)": "NSCH",
    "National Survey of Children's Health Topical Questionaire (Chilren, 6-11)": "NSCH",
    "National Survey of Children's Health Topical Questionaire (Children, 12-17)": "NSCH",
    "National Teacher and Principal Survey (NTPS) School Questionnaire": "NTPS",
    "National Teacher and Principal Survey (NTPS) Private School Questionnaire": "NTPS",
    "National Teacher and Principal Survey (NTPS) Principal Questionnaire": "NTPS",
    "National Teacher and Principal Survey (NTPS) Private School Principal Questionnaire": "NTPS",
    "National Teacher and Principal Survey (NTPS) Teacher Questionnaire": "NTPS",
    "National Teacher and Principal Survey (NTPS) Private School Teacher Questionnaire": "NTPS",
    "Teacher Follow-up Survey (TFS) Former Teacher Survey": "TFS",
    "Teacher Follow-Up Survey (TFS) Current Teacher Survey": "TFS",
    "Principal Follow-up Survey (PFS)": "PFS",
    "Principal Follow-Up Survey School Head/Principal Status Form": "PFS",
    "School Pulse Panel (SPP)": "SPP",
    "Private School Survey (PSS)": "PSS",
    "National Ambulatory Medical Care Survey (NAMCS)": "NAMCS",
    "National Hospital Ambulatory Medical Care Survey (NHAMCS)": "NHAMCS",
    "National Household Education Survey (NHES)": "NHES",
    "National Training, Education, and Workforce Survey (NTEWS)": "NTEWS",
    "National Survey of College Graduates (NSCG)": "NSCG",
    "American Time Use Survey (ATUS)": "ATUS",
    "Household Trends and Outlook Pulse Survey (HTOPS)": "HTOPS",
    "Enhancing Health Data (EHealth) Program": "EHealth",
    "School Survey on Crime and Safety (SSOCS)": "SSOCS",
    "School Crime Supplement (SCS)/National Crime Victimization Survey (NCVS)": "SCS_NCVS",
    "Identity Theft Supplement (ITS)": "ITS",
    "Supplemental Victimization Survey (SVS)": "SVS",
    "Census Military Panel (CMP)": "CMP",
    "Survey of Market Absorption (SOMA)": "SOMA",
    "Medical Expenditure Panel Survey Insurance Component": "MEPS_IC",
    "Business Enterprise Research and Development Survey": "BERD",
    "Business and Professional Classifcation Report": "BPCR",
    "Survey of State Government Finances Finances of Insurance Trust Systems": "SGFITS",
    "Report of Building or Zoning Permits issued for new privately-ownd housing units": "BZP",
    "Survey of Residential Building or Zoning Permit Systems": "SRBZPS",
}

survey_counts = {}
for survey_name in sorted(set(INSTRUMENT_TO_SURVEY.values())):
    inst_cols = [col for col, s in INSTRUMENT_TO_SURVEY.items() if s == survey_name]
    mask = raw[inst_cols].apply(
        lambda row: row.dropna().astype(str).str.strip().ne("").any(), axis=1
    )
    survey_counts[survey_name] = int(mask.sum())

ACS_FAMILY = ["ACS", "SIPP", "CE", "AHS", "CPS", "FoodAPS"]
acs_family_counts = {s: survey_counts[s] for s in ACS_FAMILY}

# =====================================================================
# 3. LITERAL QUESTION SHARING
# =====================================================================
acs_mask = raw["American Community Survey (ACS)"].notna() & (
    raw["American Community Survey (ACS)"].astype(str).str.strip() != ""
)
cps_mask = raw["Current Population Survey (CPS)"].notna() & (
    raw["Current Population Survey (CPS)"].astype(str).str.strip() != ""
)
foodaps_instrument_cols = [
    "Food Acquisition and Purchase Survey (FoodAPS) Initial Interview/Household Survey",
    "Food Acquisition and Purchase Survey (FoodAPS) Profile and Income Questionnaire",
    "Food Acquisition and Purchase Survey (FoodAPS) Debriefing Questionnaire",
    "FoodAPS food Log",
]
food_mask = raw[foodaps_instrument_cols].apply(
    lambda row: row.dropna().astype(str).str.strip().ne("").any(), axis=1
)

literal_sharing = {
    "ACS_CPS": int((acs_mask & cps_mask).sum()),
    "ACS_FoodAPS": int((acs_mask & food_mask).sum()),
    "CPS_FoodAPS": int((cps_mask & food_mask).sum()),
}

# Multi-survey stats
raw["n_surveys"] = raw[survey_cols].apply(
    lambda row: (row.dropna().astype(str).str.strip() != "").sum(), axis=1
)

# =====================================================================
# 4. CORRECTED QUESTION-LEVEL RESULTS (dual-subtopic deduplication)
# =====================================================================
ql = pd.read_csv(QUESTION_LEVEL)
feas_rank = {"F1": 1, "F2": 2, "F3": 3}
corrected_results = {}

for survey_code, label in [("CPS", "CPS"), ("FOODAPS", "FoodAPS")]:
    s = ql[ql["survey"] == survey_code].copy()
    s["feas_rank"] = s["best_feasibility"].map(feas_rank)

    # Collapse: for each unique question text, take best feasibility
    best = (
        s.groupby("question_text")
        .agg(
            best_rank=("feas_rank", "min"),
            n_ids=("survey_q_id", "count"),
            total_pairs=("pair_count", "sum"),
        )
        .reset_index()
    )
    best["best_feasibility"] = best["best_rank"].map({1: "F1", 2: "F2", 3: "F3"})

    unique_n = len(best)
    f1 = int((best["best_feasibility"] == "F1").sum())
    f2 = int((best["best_feasibility"] == "F2").sum())
    f3 = int((best["best_feasibility"] == "F3").sum())

    corrected_results[label] = {
        "unique_questions": unique_n,
        "inflated_count": int(len(s)),
        "inflation_cause": "dual-subtopic classification assigns multiple IDs to same question text",
        "F1": f1,
        "F2": f2,
        "F3": f3,
        "consolidable": f1 + f2,
        "rate": round(100 * (f1 + f2) / unique_n, 1),
    }

# =====================================================================
# 5. ACS-SIDE PARTICIPATION (how many unique ACS questions in pairs?)
# =====================================================================
# METHOD: Join via q_id through question_level (full texts) to best_matches
# (which has ACS target info but truncated source texts). For each unique
# consolidable source question, union ALL its ACS targets across subtopic contexts.
# This avoids text-truncation collisions in best_matches.
acs_side = {"available": False, "note": ""}

BEST_MATCHES = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage4_question_best_matches.csv"

if QUESTION_LEVEL.exists() and BEST_MATCHES.exists():
    bm = pd.read_csv(BEST_MATCHES)
    
    survey_acs_targets = {}
    for survey_code, label in [("CPS", "CPS"), ("FOODAPS", "FoodAPS")]:
        ql_sub = ql[ql["survey"] == survey_code].copy()
        ql_sub["feas_rank"] = ql_sub["best_feasibility"].map(feas_rank)
        # Dedup by full question text, take best feasibility
        dedup = ql_sub.sort_values("feas_rank").drop_duplicates(subset="question_text", keep="first")
        # Get consolidable question texts
        consol_texts = set(dedup[dedup["best_feasibility"].isin(["F1", "F2"])]["question_text"])
        # Get ALL q_ids for those texts (including duplicates across subtopics)
        consol_qids = set(ql_sub[ql_sub["question_text"].isin(consol_texts)]["survey_q_id"])
        # Get all F1/F2 ACS targets from best_matches for those q_ids
        bm_sub = bm[
            (bm["survey"] == survey_code)
            & (bm["source_q_id"].isin(consol_qids))
            & (bm["best_feasibility"].isin(["F1", "F2"]))
        ]
        survey_acs_targets[label] = set(bm_sub["best_match_text"].dropna().unique())
    
    cps_acs = survey_acs_targets["CPS"]
    food_acs = survey_acs_targets["FoodAPS"]
    combined_acs = cps_acs | food_acs
    three_way = cps_acs & food_acs
    
    acs_side = {
        "available": True,
        "method": "q_id join through question_level (full text) to best_matches, union ACS targets per unique source question",
        "CPS_acs_targets": int(len(cps_acs)),
        "FoodAPS_acs_targets": int(len(food_acs)),
        "combined_unique_acs_targets": int(len(combined_acs)),
        "three_way_bridges": int(len(three_way)),
        "set_arithmetic": f"{len(cps_acs)} + {len(food_acs)} - {len(three_way)} = {len(cps_acs) + len(food_acs) - len(three_way)}",
        "total_acs_questions": acs_family_counts["ACS"],
        "pct_participating": round(100 * len(combined_acs) / acs_family_counts["ACS"], 1),
        "fan_in_ratio": round(
            (corrected_results["CPS"]["consolidable"] + corrected_results["FoodAPS"]["consolidable"])
            / len(combined_acs), 2
        ),
    }
else:
    missing = []
    if not QUESTION_LEVEL.exists():
        missing.append(str(QUESTION_LEVEL))
    if not BEST_MATCHES.exists():
        missing.append(str(BEST_MATCHES))
    acs_side = {"available": False, "note": f"Missing files: {missing}"}

# =====================================================================
# BUILD OUTPUT
# =====================================================================
result = {
    "metadata": {
        "source_files": [
            "data/raw/PublicSurveyQuestionsMap.csv",
            "docs/stages/03_harmonization/data/analysis/stage4_question_level.csv",
            "docs/stages/03_harmonization/data/analysis/final_verdicts.csv",
        ],
        "generated": datetime.now().isoformat(),
        "script": "src/validation/validate_question_counts.py",
    },
    "raw_data": {
        "total_deduplicated_questions": int(len(raw)),
        "total_instrument_columns": len(survey_cols),
        "questions_on_1_survey": int((raw["n_surveys"] == 1).sum()),
        "questions_on_2plus_surveys": int((raw["n_surveys"] > 1).sum()),
        "literal_question_sharing": literal_sharing,
    },
    "instrument_counts": dict(
        sorted(instrument_counts.items(), key=lambda x: x[1], reverse=True)
    ),
    "survey_counts": dict(
        sorted(survey_counts.items(), key=lambda x: x[1], reverse=True)
    ),
    "acs_family_counts": dict(
        sorted(acs_family_counts.items(), key=lambda x: x[1], reverse=True)
    ),
    "pairing_stage": {
        "CPS": {
            "raw_survey_questions": acs_family_counts["CPS"],
            "inflated_entering_pairing": corrected_results["CPS"]["inflated_count"],
            "unique_entering_pairing": corrected_results["CPS"]["unique_questions"],
            "pct_of_survey": round(
                100 * corrected_results["CPS"]["unique_questions"] / acs_family_counts["CPS"], 1
            ),
            "not_paired_reason": "question subtopics with no ACS coverage",
        },
        "FoodAPS": {
            "raw_survey_questions": acs_family_counts["FoodAPS"],
            "inflated_entering_pairing": corrected_results["FoodAPS"]["inflated_count"],
            "unique_entering_pairing": corrected_results["FoodAPS"]["unique_questions"],
            "pct_of_survey": round(
                100 * corrected_results["FoodAPS"]["unique_questions"] / acs_family_counts["FoodAPS"], 1
            ),
            "not_paired_reason": "question subtopics with no ACS coverage",
        },
    },
    "question_level_results": {
        "CPS": corrected_results["CPS"],
        "FoodAPS": corrected_results["FoodAPS"],
        "note": "Corrected counts collapse duplicate question texts to single entries, taking best feasibility across all subtopic-pairings",
    },
    "acs_side_participation": acs_side,
    "known_issues": {
        "inflation_source": "stage4_question_level.csv assigns separate IDs per subtopic-pairing context, not per unique question",
        "numbers_map_corrections_needed": [
            "CPS '240 unique source questions' should be 157",
            "FoodAPS '140 unique source questions' should be 118",
            "CPS F1=37 should be 32, F2=65 should be 54, consolidable=102 should be 86",
            "FoodAPS F1=23 should be 19, F2=45 should be 37, consolidable=68 should be 56",
            "CPS consolidation rate 42.5% should be 54.8%",
            "FoodAPS consolidation rate 48.6% should be 47.5%",
        ],
    },
}

# =====================================================================
# WRITE OUTPUTS
# =====================================================================
json_path = OUT_DIR / "question_counts.json"
with open(json_path, "w") as f:
    json.dump(result, f, indent=2)
print(f"Saved: {json_path}")

# Human-readable log
log_path = OUT_DIR / "question_counts.log"
lines = []
lines.append(f"Question Count Validation - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append(f"Script: src/validation/validate_question_counts.py")
lines.append(f"")
lines.append(f"RAW DATA: {len(raw)} deduplicated questions, {len(survey_cols)} instrument columns")
lines.append(f"  On 1 survey: {(raw['n_surveys'] == 1).sum()}")
lines.append(f"  On 2+ surveys: {(raw['n_surveys'] > 1).sum()}")
lines.append(f"  Literal sharing ACS-CPS: {literal_sharing['ACS_CPS']}")
lines.append(f"  Literal sharing ACS-FoodAPS: {literal_sharing['ACS_FoodAPS']}")
lines.append(f"")
lines.append("=" * 70)
lines.append("ACS FAMILY COUNTS (from raw data)")
lines.append("=" * 70)
for s in ["SIPP", "CE", "AHS", "FoodAPS", "CPS", "ACS"]:
    lines.append(f"  {s:<12} {acs_family_counts[s]:>6}")
lines.append(f"")
lines.append("=" * 70)
lines.append("CORRECTED QUESTION-LEVEL RESULTS")
lines.append("=" * 70)
for label in ["CPS", "FoodAPS"]:
    c = corrected_results[label]
    lines.append(f"")
    lines.append(f"  {label}:")
    lines.append(f"    Unique questions:    {c['unique_questions']} (inflated was {c['inflated_count']})")
    lines.append(f"    F1 (direct recode):  {c['F1']}")
    lines.append(f"    F2 (stat. adjust):   {c['F2']}")
    lines.append(f"    F3 (incompatible):   {c['F3']}")
    lines.append(f"    Consolidable:        {c['consolidable']} ({c['rate']}%)")
lines.append(f"")
lines.append("=" * 70)
lines.append("ACS-SIDE PARTICIPATION")
lines.append("=" * 70)
if acs_side.get("available"):
    lines.append(f"  Method: {acs_side['method']}")
    lines.append(f"  CPS ACS targets: {acs_side['CPS_acs_targets']}")
    lines.append(f"  FoodAPS ACS targets: {acs_side['FoodAPS_acs_targets']}")
    lines.append(f"  Combined unique: {acs_side['combined_unique_acs_targets']} of {acs_side['total_acs_questions']} ({acs_side['pct_participating']}%)")
    lines.append(f"  Three-way bridges: {acs_side['three_way_bridges']}")
    lines.append(f"  Set arithmetic: {acs_side['set_arithmetic']}")
    lines.append(f"  Fan-in ratio: {acs_side['fan_in_ratio']}")
else:
    lines.append(f"  {acs_side.get('note', 'Not computed')}")

with open(log_path, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"Saved: {log_path}")

# Print key findings to stdout
print(f"\n{'='*60}")
print("KEY FINDINGS")
print(f"{'='*60}")
for label in ["CPS", "FoodAPS"]:
    c = corrected_results[label]
    print(f"  {label}: {c['unique_questions']} unique Qs, {c['consolidable']} consolidable ({c['rate']}%)")
if acs_side.get("available"):
    print(f"  ACS side: {acs_side['unique_acs_questions_in_pairs']} of {acs_side['total_acs_questions']} participate")
else:
    print(f"  ACS side: {acs_side.get('note', 'check final_verdicts.csv columns')}")
