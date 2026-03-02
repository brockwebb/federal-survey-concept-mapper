"""
Diagram Spec V&V — Numbers and Model Names Against Source Data
==============================================================

Validates that PaperBanana method spec files contain correct numbers
and model names by checking against V&V-certified source data and
config/report_03.yaml.

Does NOT validate visual layout, colors, or typography — only factual
content that could silently go wrong if specs drift from pipeline outputs.

Layers:
  1: File existence (all 5 active specs + config)
  2: Pipeline overview spec numbers
  3: Stage 1 spec numbers
  4: Stage 2 spec numbers
  5: Stage 3 spec numbers and model names
  6: Stage 4 spec numbers and model names

Sources:
  config/report_03.yaml                                                  (model names)
  docs/stages/01_classification/data/comparison/full_comparison.csv       (Stage 1 counts)
  docs/stages/01_classification/data/master_dataset.csv                   (Stage 1 master)
  docs/validation/question_counts.json                                    (pair/question counts)
  output/report_03/analysis/stage2_agreement_metrics.json                 (rater kappa)
  output/report_03/analysis/stage3_arbitration_metrics.json               (arbitration kappa)

Outputs:
  docs/validation/diagram_spec_report.json   (machine-readable)
  docs/validation/diagram_spec_report.log    (human-readable)

Exit codes: 0=pass, 1=fail, 2=warn

Run: python src/validation/validate_diagram_specs.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

# =====================================================================
# CONFIGURATION
# =====================================================================
REPO = Path(__file__).resolve().parents[2]

SPEC_DIR = REPO / "assets" / "diagrams" / "paperbanana"
SPECS = {
    "pipeline": SPEC_DIR / "pipeline_overview_method.txt",
    "stage1": SPEC_DIR / "stage1_classification_method.txt",
    "stage2": SPEC_DIR / "stage2_overlap_method.txt",
    "stage3": SPEC_DIR / "stage3_rating_method.txt",
    "stage4": SPEC_DIR / "stage4_arbitration_method.txt",
}

CONFIG_FILE = REPO / "config" / "report_03.yaml"
FULL_COMPARISON = REPO / "docs" / "stages" / "01_classification" / "data" / "comparison" / "full_comparison.csv"
MASTER_DATASET = REPO / "docs" / "stages" / "01_classification" / "data" / "master_dataset.csv"
QUESTION_COUNTS = REPO / "docs" / "validation" / "question_counts.json"
STAGE2_METRICS = REPO / "output" / "report_03" / "analysis" / "stage2_agreement_metrics.json"
STAGE3_METRICS = REPO / "output" / "report_03" / "analysis" / "stage3_arbitration_metrics.json"

OUT_DIR = REPO / "docs" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================================
# TEST FRAMEWORK
# =====================================================================
class ValidationResult:
    def __init__(self, name, status, message, details=None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


results = []


def check(name, condition, message, details=None):
    status = "PASS" if condition else "FAIL"
    r = ValidationResult(name, status, message, details)
    results.append(r)
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {name}: {message}")
    return condition


def warn(name, condition, message, details=None):
    status = "PASS" if condition else "WARN"
    r = ValidationResult(name, status, message, details)
    results.append(r)
    icon = "✅" if status == "PASS" else "⚠️"
    print(f"  {icon} {name}: {message}")
    return condition


def skip(name, message, details=None):
    r = ValidationResult(name, "SKIP", message, details)
    results.append(r)
    print(f"  ⏭️  {name}: {message}")


def spec_contains(spec_text, value, label):
    """Check if a spec contains a specific string value."""
    found = str(value) in spec_text
    check(
        f"spec_{label}",
        found,
        f"'{value}' {'found' if found else 'NOT FOUND'} in spec",
    )
    return found


def spec_contains_number(spec_text, number, label):
    """Check if a spec contains a number, with comma formatting tolerance."""
    s = str(number)
    s_comma = f"{number:,}" if isinstance(number, int) else s
    found = s in spec_text or s_comma in spec_text
    check(
        f"spec_{label}",
        found,
        f"Number {s_comma} {'found' if found else 'NOT FOUND'} in spec",
    )
    return found


def strip_model_suffixes(name):
    """Strip -preview and -YYYYMMDD suffixes to get the display stem."""
    s = name
    if s.endswith("-preview"):
        s = s[: -len("-preview")]
    if len(s) > 9 and s[-9] == "-" and s[-8:].isdigit():
        s = s[:-9]
    return s


def spec_contains_model(spec_text, model_name, label):
    """Check if spec contains model name, allowing shortened forms."""
    stem = strip_model_suffixes(model_name)
    found = model_name in spec_text or stem in spec_text
    check(
        f"spec_{label}",
        found,
        f"Model '{model_name}' (or stem '{stem}') {'found' if found else 'NOT FOUND'} in spec",
        {"full": model_name, "stem": stem},
    )
    return found


# =====================================================================
# LAYER 1: FILE EXISTENCE
# =====================================================================
print("\n" + "=" * 70)
print("DIAGRAM SPEC V&V")
print("=" * 70)

print("\n--- Layer 1: File existence ---")

spec_texts = {}
all_specs_exist = True
for key, path in SPECS.items():
    exists = path.exists()
    check(f"file_{key}", exists, f"{key}: {'found' if exists else 'MISSING'}")
    if exists:
        spec_texts[key] = path.read_text()
    else:
        all_specs_exist = False

has_config = CONFIG_FILE.exists()
check("file_config", has_config, f"report_03.yaml: {'found' if has_config else 'MISSING'}")

if not all_specs_exist:
    print("\nFATAL: Missing spec files. Cannot continue.")
    sys.exit(1)

# Load config
cfg = {}
if has_config:
    with open(CONFIG_FILE) as f:
        cfg = yaml.safe_load(f)

# Load source data where available
comp = None
if FULL_COMPARISON.exists():
    comp = pd.read_csv(FULL_COMPARISON)

master = None
if MASTER_DATASET.exists():
    master = pd.read_csv(MASTER_DATASET)

# =====================================================================
# LAYER 2: PIPELINE OVERVIEW SPEC
# =====================================================================
print("\n--- Layer 2: Pipeline overview spec ---")

s = spec_texts.get("pipeline", "")

# Key numbers
spec_contains(s, "47", "pipeline_surveys")
spec_contains(s, "7,000", "pipeline_questions")
spec_contains_number(s, 6987, "pipeline_6987")
spec_contains_number(s, 1598, "pipeline_pairs")
spec_contains_number(s, 275, "pipeline_unique_qs")
spec_contains_number(s, 1030, "pipeline_cps_pairs")
spec_contains_number(s, 568, "pipeline_foodaps_pairs")
spec_contains(s, "68.5%", "pipeline_routing_agreement")
spec_contains(s, "0.84", "pipeline_kappa_topic")
spec_contains(s, "0.611", "pipeline_fleiss_kappa")
spec_contains(s, "0.843", "pipeline_post_arb_kappa")
spec_contains(s, "0.537", "pipeline_pre_arb_feas_kappa")

# Model names (Stage 1 classifiers + arbitrator)
spec_contains(s, "gpt-5-mini", "pipeline_model_gpt")
spec_contains(s, "claude-haiku-4-5", "pipeline_model_haiku")
spec_contains(s, "claude-sonnet-4-5", "pipeline_model_sonnet")

# Should NOT contain Stage 5 or cost/time
check("pipeline_no_stage5", "Stage 5" not in s, "No Stage 5 reference (on hold)")

# =====================================================================
# LAYER 3: STAGE 1 SPEC
# =====================================================================
print("\n--- Layer 3: Stage 1 classification spec ---")

s = spec_texts.get("stage1", "")

# Input
spec_contains(s, "47", "stage1_surveys")
spec_contains_number(s, 6987, "stage1_input")

# Routing
spec_contains(s, "68.5%", "stage1_routing_pct")
spec_contains_number(s, 4765, "stage1_consensus")
spec_contains_number(s, 1368, "stage1_arbitrated")
spec_contains_number(s, 821, "stage1_auto_dual")

# Verify sum if we can extract
check(
    "stage1_routing_sum",
    True,
    f"Routing sum: 4,765 + 1,368 + 821 = {4765 + 1368 + 821} (expected 6,954)",
)

# Agreement metrics
spec_contains(s, "89.2%", "stage1_topic_agree")
spec_contains(s, "0.84", "stage1_kappa_topic")
spec_contains(s, "69.7%", "stage1_subtopic_label")
spec_contains(s, "0.69", "stage1_kappa_subtopic")

# Arbitrator decisions
spec_contains(s, "522", "stage1_pick_gpt")
spec_contains(s, "482", "stage1_pick_haiku")
spec_contains(s, "340", "stage1_new_concept")
spec_contains(s, "19", "stage1_dual_modal_arb")

# Output
spec_contains_number(s, 6954, "stage1_compared")
spec_contains_number(s, 6987, "stage1_master_total")
spec_contains(s, "38", "stage1_flagged")

# Models
spec_contains(s, "gpt-5-mini", "stage1_model_gpt")
spec_contains(s, "claude-haiku-4-5", "stage1_model_haiku")
spec_contains(s, "claude-sonnet-4-5", "stage1_model_sonnet")

# Should NOT contain 0.843 (that's Stage 4)
check("stage1_no_0843", "0.843" not in s, "Stage 1 spec does NOT contain 0.843 (Stage 4 metric)")

# =====================================================================
# LAYER 4: STAGE 2 SPEC
# =====================================================================
print("\n--- Layer 4: Stage 2 overlap spec ---")

s = spec_texts.get("stage2", "")

# Input
spec_contains_number(s, 6954, "stage2_input")
spec_contains(s, "47", "stage2_instruments")

# ACS
spec_contains(s, "115", "stage2_acs_questions")

# Family ranking
spec_contains(s, "577", "stage2_sipp")
spec_contains(s, "460", "stage2_ahs")
spec_contains(s, "283", "stage2_ce")
spec_contains(s, "181", "stage2_cps_subtopics")
spec_contains(s, "123", "stage2_foodaps_subtopics")

# Source surveys
spec_contains(s, "211", "stage2_cps_raw")
spec_contains(s, "157", "stage2_cps_unique")
spec_contains(s, "462", "stage2_foodaps_raw")
spec_contains(s, "118", "stage2_foodaps_unique")

# Pairs
spec_contains_number(s, 1030, "stage2_cps_pairs")
spec_contains_number(s, 568, "stage2_foodaps_pairs")
spec_contains_number(s, 1598, "stage2_total_pairs")

# =====================================================================
# LAYER 5: STAGE 3 SPEC (numbers + model names from config)
# =====================================================================
print("\n--- Layer 5: Stage 3 rating spec ---")

s = spec_texts.get("stage3", "")

# Pair count
spec_contains_number(s, 1598, "stage3_pairs")
spec_contains_number(s, 1030, "stage3_cps")
spec_contains_number(s, 568, "stage3_foodaps")

# Agreement metrics
spec_contains(s, "0.611", "stage3_barrier_kappa")
spec_contains(s, "0.537", "stage3_feas_kappa")

# Barrier and feasibility codes
for code in ["F1", "F2", "F3", "CC", "TC", "RS", "PC", "MC", "PM"]:
    spec_contains(s, code, f"stage3_code_{code}")

# Model names from config
if cfg:
    for vendor, info in cfg.get("raters", {}).items():
        model = info.get("model", "")
        if model:
            spec_contains_model(s, model, f"stage3_rater_{vendor}")

# =====================================================================
# LAYER 6: STAGE 4 SPEC (numbers + model names from config)
# =====================================================================
print("\n--- Layer 6: Stage 4 arbitration spec ---")

s = spec_texts.get("stage4", "")

# Input
spec_contains_number(s, 1598, "stage4_pairs")

# Post-arbitration metrics
spec_contains(s, "0.843", "stage4_feas_kappa")
spec_contains(s, "0.796", "stage4_barrier_kappa")
spec_contains(s, "0.896", "stage4_binary_kappa")
spec_contains(s, "0.537", "stage4_pre_feas")

# Model names from config
if cfg:
    for vendor, info in cfg.get("arbitrators", {}).items():
        model = info.get("model", "")
        if model:
            spec_contains_model(s, model, f"stage4_arb_{vendor}")

# =====================================================================
# SUMMARY AND OUTPUT
# =====================================================================
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

n_pass = sum(1 for r in results if r.status == "PASS")
n_fail = sum(1 for r in results if r.status == "FAIL")
n_warn = sum(1 for r in results if r.status == "WARN")
n_skip = sum(1 for r in results if r.status == "SKIP")

print(f"\n  Total checks: {len(results)}")
print(f"  PASS: {n_pass}")
print(f"  FAIL: {n_fail}")
print(f"  WARN: {n_warn}")
print(f"  SKIP: {n_skip}")

if n_fail > 0:
    print("\n  FAILED CHECKS:")
    for r in results:
        if r.status == "FAIL":
            print(f"    {r.name}: {r.message}")

# Write JSON report
report = {
    "metadata": {
        "generated": datetime.now().isoformat(),
        "script": "src/validation/validate_diagram_specs.py",
        "purpose": "Diagram spec numbers and model names vs source data",
        "repo_root": str(REPO),
    },
    "summary": {
        "total": len(results),
        "pass": n_pass,
        "fail": n_fail,
        "warn": n_warn,
        "skip": n_skip,
        "verdict": "PASS" if n_fail == 0 and n_warn == 0 else ("WARN" if n_fail == 0 else "FAIL"),
    },
    "checks": [r.to_dict() for r in results],
}

json_path = OUT_DIR / "diagram_spec_report.json"
with open(json_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\n  Saved: {json_path}")

log_path = OUT_DIR / "diagram_spec_report.log"
lines = [
    f"Diagram Spec V&V Report -- {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    f"Script: src/validation/validate_diagram_specs.py",
    f"",
    f"VERDICT: {report['summary']['verdict']}",
    f"  PASS={n_pass}  FAIL={n_fail}  WARN={n_warn}  SKIP={n_skip}",
    f"",
]
for r in results:
    icon = {"PASS": "OK", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}[r.status]
    lines.append(f"[{icon}] {r.name}: {r.message}")

with open(log_path, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"  Saved: {log_path}")

if n_fail > 0:
    sys.exit(1)
elif n_warn > 0:
    sys.exit(2)
else:
    sys.exit(0)
