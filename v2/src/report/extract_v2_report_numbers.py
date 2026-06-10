#!/usr/bin/env python3
"""v2 report numbers extraction + pipeline diagnostic (one script, two jobs).

JOB 1 -- DIAGNOSTIC. Verify every expected v2 pipeline output exists, with
size, mtime, a short content hash, and row/line counts. Seldon task state on
DEV is stale (execution happens on WORK, closure on DEV); this manifest is the
ground truth for reconciling the graph afterward.

JOB 2 -- EXTRACTION. Emit every number the v2 results report needs, in one
paste-friendly stdout digest, each value keyed to its source file. No analysis
in the transcript; the digest is transport only. The report is drafted on DEV
from the digest alone.

CONSTRAINTS
-----------
Python stdlib only. No pandas, no harness, no API calls, no subprocess. Runs
from v2/ (cwd), same convention as every other v2 script. Read-only except its
own output under output/report/; it touches nothing under output/stage*.

The `socket` import is used only for the local hostname (machine label in the
paste-back, so DEV and WORK digests are distinguishable). It performs a local
syscall, no network, consistent with the stdlib-only / no-subprocess rule.

PATHS
-----
Manifest paths are hardcoded because stdlib has no YAML reader; each entry
records the config key it mirrors (e.g. `stage3.yaml:output.pairs_subdir`). A
path that 404s is reported MISSING; the script never guesses alternatives.

The TEVV evidence path is the one repo-root path: from v2/ it is
`../docs/stages/tevv/...`, matching the `../docs/...` convention stage2.yaml
already uses for repo-root artifacts. The task spec names the file
`prompt_equivalence_report.json`, but the committed evidence JSON is
`prompt_equivalence_evidence.json` (the `.md` sibling is the human report);
this script reads the committed `.json` because that is the file that carries
the stage3 verdict the TEVV check verifies. The discrepancy is recorded in the
manifest entry note, not silently resolved.

Run from v2/:
    python src/report/extract_v2_report_numbers.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# =============================================================================
# CONSTANTS (thresholds mirrored from config / the task spec, with provenance)
# =============================================================================

# Mirrors stage2.yaml finalize.expected_row_count. Data rows (header excluded).
EXPECTED_MASTER_ROWS = 6987

# Per-JSON serialized-size cap applied ONLY to the stdout digest copy. The
# on-disk file output keeps every JSON whole. dashboard_data.json is the likely
# trigger. Never a silent truncation: the capped copy carries a loud marker.
JSON_CAP_CHARS = 25_000

# TEVV expectations (from the 2026-06-10 task spec). The stage3 prompt diverged
# from v1 in 21 acknowledged ways; the verdict is an accepted divergence, not a
# bug. The directional_bias strings are PROVISIONAL (pending SME review).
TEVV_VERDICT_EXPECTED = "ACKNOWLEDGED_DIVERGENCE"
TEVV_DIVERGENCE_EXPECTED = 21
TEVV_STAGE = "stage3"

SURVEYS = ["cps", "foodaps", "ahs"]

# AHS rollup revision keys (task 4615d8ee). In the revised rollup these live
# under the `question_level` block, so the check looks there first then falls
# back to top level.
AHS_REVISION_KEYS = [
    "ahs_questions_entered_pairing",
    "unique_ahs_questions_with_candidate",
    "no_candidate_entered_all_f3",
    "no_pair_no_shared_subtopic",
]

# TEVV evidence file, relative to v2/ (repo-root docs/ via ../). See module
# docstring for the report-vs-evidence filename note.
TEVV_PATH = "../docs/stages/tevv/prompt_equivalence_evidence.json"


# =============================================================================
# MANIFEST SPEC
# =============================================================================
# (path, count_kind, config_key, note). count_kind in {"lines","rows",None}.
# Per-survey and glob entries are expanded in build_manifest().

STATIC_SPEC: list[tuple[str, str | None, str, str | None]] = [
    # Stage 1
    ("output/stage1/results_rater_a_claude_4_5_sonnet.jsonl", "lines",
     "stage2.yaml:stage1.rater_a_results", None),
    ("output/stage1/results_rater_b_gemini-2_5-flash.jsonl", "lines",
     "stage2.yaml:stage1.rater_b_results", None),
    ("output/stage1/comparison/comparison_summary.json", None,
     "stage2.yaml:stage1_comparison.summary_json", None),
    ("output/stage1/comparison/stage1_comparison_report.md", None,
     "stage1 comparison report (derivative of comparison_summary.json)", None),
    # Stage 2
    ("output/stage2/master_dataset.csv", "rows",
     "stage2.yaml:output.output_dir+finalize.v2_master "
     "(expected==finalize.expected_row_count)", None),
    ("output/stage2/all_disagreement_resolutions.csv", "rows",
     "stage2.yaml:output.all_resolutions_csv", None),
    ("output/stage2/v1_v2_comparison_summary.json", None,
     "stage2.yaml:finalize.comparison_summary_json", None),
    ("output/stage2/v1_v2_changed_questions.csv", "rows",
     "stage2.yaml:finalize.changed_questions_csv", None),
    ("output/stage2/stage2_run_report.md", None,
     "stage2.yaml:output.run_report", None),
    ("output/stage2/dashboard/dashboard_data.json", None,
     "stage2.yaml:dashboard.output_subdir+data_files.combined_json", None),
    # Stage 3 -- pair builder
    ("output/stage3/candidate_pairs/pair_summary.json", None,
     "stage3.yaml:output.output_dir+pairs_subdir+pair_summary_json", None),
    ("output/stage3/candidate_pairs/pairs_cps.csv", "rows",
     "stage3.yaml:output.pairs_subdir (pairs_<survey>.csv)", None),
    ("output/stage3/candidate_pairs/pairs_foodaps.csv", "rows",
     "stage3.yaml:output.pairs_subdir (pairs_<survey>.csv)", None),
    ("output/stage3/candidate_pairs/pairs_ahs.csv", "rows",
     "stage3.yaml:output.pairs_subdir (pairs_<survey>.csv)", None),
    # Stage 3 -- v1/v2 comparison
    ("output/stage3/v1_v2_comparison/v1_v2_pairset_overlap.json", None,
     "stage3 v1_v2_comparison output", None),
    ("output/stage3/v1_v2_comparison/v1_v2_classification_agreement.json", None,
     "stage3 v1_v2_comparison output", None),
    ("output/stage3/v1_v2_comparison/v1_v2_signal_stratified_summary.json", None,
     "stage3 v1_v2_comparison output", None),
    # Stage 3 -- AHS rollup
    ("output/stage3/results/ahs/ahs_candidates.csv", "rows",
     "stage3 AHS rollup output (ahs_candidates.csv)", None),
    ("output/stage3/results/ahs/ahs_candidate_summary.json", None,
     "stage3 AHS rollup output (ahs_candidate_summary.json)", None),
    ("output/stage3/results/ahs/ahs_rollup.md", None,
     "stage3 AHS rollup output (ahs_rollup.md)", None),
    # TEVV
    (TEVV_PATH, None,
     "task spec names prompt_equivalence_report.json; on-disk evidence JSON is "
     "prompt_equivalence_evidence.json (the .md sibling is the report)",
     "Spec/on-disk filename discrepancy: report(.md) vs evidence(.json). "
     "Reading the committed evidence JSON, which carries the stage3 verdict."),
    # Ledger (optional)
    ("cost_ledger.jsonl", "lines",
     "stage3.yaml:harness.ledger_path (== stage2.yaml:harness.ledger_path)",
     "optional / nice-to-have"),
]


# =============================================================================
# FILE INSPECTION HELPERS
# =============================================================================

def _count_lines(p: Path) -> int:
    """Non-empty line count (jsonl)."""
    n = 0
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _count_rows_csv(p: Path) -> int:
    """Data-row count for a CSV (header excluded). csv.reader is used rather
    than a line count because the survey text fields carry embedded newlines
    inside quoted cells, which would inflate a naive line count."""
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        n = sum(1 for _ in csv.reader(f))
    return max(n - 1, 0)


def _sha16(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def inspect(path_str: str, count_kind: str | None, config_key: str,
            note: str | None) -> dict[str, Any]:
    """Build one manifest entry. Never raises on a missing file: records
    MISSING and continues."""
    p = Path(path_str)
    entry: dict[str, Any] = {
        "path": path_str,
        "config_key": config_key,
        "exists": False,
        "size_bytes": None,
        "mtime_utc": None,
        "sha256_16": None,
        "count_kind": count_kind,
        "count": None,
        "status": "MISSING",
    }
    if note:
        entry["note"] = note
    if not p.exists() or not p.is_file():
        return entry
    st = p.stat()
    entry["exists"] = True
    entry["status"] = "OK"
    entry["size_bytes"] = st.st_size
    entry["mtime_utc"] = _iso(st.st_mtime)
    try:
        entry["sha256_16"] = _sha16(p)
    except OSError as e:
        entry["sha256_16"] = f"HASH_ERROR:{e}"
    if count_kind == "lines":
        entry["count"] = _count_lines(p)
    elif count_kind == "rows":
        entry["count"] = _count_rows_csv(p)
    return entry


def git_head() -> str:
    """Short HEAD hash via stdlib file reads (no subprocess). Walks up from cwd
    to find .git, resolves the ref (loose then packed-refs). 'unknown' on any
    failure or a detached/unresolvable state we cannot read."""
    cur = Path.cwd()
    for d in [cur, *cur.parents]:
        g = d / ".git"
        if not g.is_dir():
            continue
        try:
            head = (g / "HEAD").read_text(encoding="utf-8").strip()
        except OSError:
            return "unknown"
        if not head.startswith("ref:"):
            return head[:12]  # detached HEAD: HEAD is a raw hash
        ref = head[4:].strip()
        loose = g / ref
        if loose.exists():
            try:
                return loose.read_text(encoding="utf-8").strip()[:12]
            except OSError:
                return "unknown"
        packed = g / "packed-refs"
        if packed.exists():
            try:
                for ln in packed.read_text(encoding="utf-8").splitlines():
                    if ln and not ln.startswith(("#", "^")) and ln.endswith(ref):
                        return ln.split(" ", 1)[0][:12]
            except OSError:
                return "unknown"
        return "unknown"
    return "unknown"


# =============================================================================
# MANIFEST + CONTENT CAPTURE
# =============================================================================

def build_manifest() -> tuple[list[dict[str, Any]], set[Path]]:
    """Expand the spec (static + per-survey + glob) into manifest entries.
    Returns (entries, accounted_paths) where accounted_paths is the resolved
    set of every file we looked for under output/, used to compute
    unexpected_files."""
    entries: list[dict[str, Any]] = []
    accounted: set[Path] = set()

    def add(path_str: str, kind: str | None, key: str,
            note: str | None = None) -> None:
        entries.append(inspect(path_str, kind, key, note))
        p = Path(path_str)
        try:
            accounted.add(p.resolve())
        except OSError:
            accounted.add(p)

    # Static block, but inject the per-survey stage3 results in spec order so
    # the manifest reads top-to-bottom by stage.
    for path_str, kind, key, note in STATIC_SPEC:
        add(path_str, kind, key, note)
        # After the last candidate_pairs entry, splice in per-survey results.
        if path_str.endswith("pairs_ahs.csv"):
            for sv in SURVEYS:
                add(f"output/stage3/results/{sv}/final_barrier_classifications.csv",
                    "rows", "stage3.yaml:output.results_subdir+final_csv")
                add(f"output/stage3/results/{sv}/comparison_summary.json",
                    None, "stage3.yaml:output.comparison_summary_json "
                          "(per survey, if present)")

    # Glob: gold_candidates_*.csv under v1_v2_comparison.
    gold_dir = Path("output/stage3/v1_v2_comparison")
    if gold_dir.is_dir():
        gold = sorted(gold_dir.glob("gold_candidates_*.csv"))
        if gold:
            for gp in gold:
                add(str(gp), "rows",
                    "stage3 v1_v2_comparison gold_candidates_*.csv (glob)")
        else:
            entries.append({
                "path": "output/stage3/v1_v2_comparison/gold_candidates_*.csv",
                "config_key": "stage3 v1_v2_comparison gold_candidates_*.csv (glob)",
                "exists": False, "size_bytes": None, "mtime_utc": None,
                "sha256_16": None, "count_kind": "rows", "count": None,
                "status": "MISSING", "note": "glob matched zero files",
            })
    else:
        entries.append({
            "path": "output/stage3/v1_v2_comparison/gold_candidates_*.csv",
            "config_key": "stage3 v1_v2_comparison gold_candidates_*.csv (glob)",
            "exists": False, "size_bytes": None, "mtime_utc": None,
            "sha256_16": None, "count_kind": "rows", "count": None,
            "status": "MISSING", "note": "parent dir absent",
        })

    return entries, accounted


def find_unexpected(accounted: set[Path]) -> list[dict[str, Any]]:
    """Recursively list *.json/*.csv/*.md under output/ that no manifest entry
    accounted for. Recursive (not just two levels) so a deeper unanticipated
    output is still caught; that is the stated purpose of this sweep."""
    out = Path("output")
    if not out.is_dir():
        return []
    found: list[dict[str, Any]] = []
    for p in sorted(out.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in {".json", ".csv", ".md"}:
            continue
        try:
            rp = p.resolve()
        except OSError:
            rp = p
        if rp in accounted:
            continue
        found.append({"path": str(p), "size_bytes": p.stat().st_size})
    return found


def capture_json_contents(entries: list[dict[str, Any]]
                          ) -> tuple[dict[str, Any], list[str]]:
    """Load every existing *.json in the manifest whole. Returns (contents,
    parse_error_flags). No truncation here; the digest cap is applied later."""
    contents: dict[str, Any] = {}
    flags: list[str] = []
    for e in entries:
        path_str = e["path"]
        if not e["exists"] or not path_str.lower().endswith(".json"):
            continue
        try:
            contents[path_str] = json.loads(
                Path(path_str).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            contents[path_str] = {"JSON_PARSE_ERROR": str(exc)}
            flags.append(f"JSON_PARSE_ERROR:{path_str}")
    return contents, flags


def cap_json_contents(contents: dict[str, Any]) -> dict[str, Any]:
    """Digest copy: any single JSON whose serialized size exceeds the cap is
    replaced by a loud marker plus its top-level key list. Never silent."""
    capped: dict[str, Any] = {}
    for k, obj in contents.items():
        serialized = json.dumps(obj, default=str)
        if len(serialized) > JSON_CAP_CHARS:
            capped[k] = {
                "TRUNCATED_SEE_FILE": True,
                "serialized_chars": len(serialized),
                "top_level_keys": (list(obj.keys())
                                   if isinstance(obj, dict) else "<non-dict>"),
            }
        else:
            capped[k] = obj
    return capped


# =============================================================================
# CHECKS
# =============================================================================

def _entry_by_path(entries: list[dict[str, Any]], path_str: str
                   ) -> dict[str, Any] | None:
    for e in entries:
        if e["path"] == path_str:
            return e
    return None


def _ahs_revision_block(summary: dict[str, Any]) -> dict[str, Any]:
    """The revised rollup nests the question-unit keys under `question_level`;
    fall back to top level so an older flat layout still resolves."""
    if isinstance(summary, dict) and isinstance(summary.get("question_level"),
                                                dict):
        ql = summary["question_level"]
        if any(k in ql for k in AHS_REVISION_KEYS):
            return ql
    return summary if isinstance(summary, dict) else {}


def run_checks(entries: list[dict[str, Any]],
               contents: dict[str, Any]) -> tuple[list[dict[str, Any]],
                                                   list[str], dict[str, Any]]:
    """Every check runs and emits PASS / FAIL / SKIP with the observed value;
    none abort. Returns (checks, flags, extras) where extras carries the
    PROVISIONAL TEVV directional_bias payload for the digest."""
    checks: list[dict[str, Any]] = []
    flags: list[str] = []
    extras: dict[str, Any] = {}

    def emit(cid: str, name: str, status: str, observed: Any,
             expected: Any = None, detail: str = "") -> dict[str, Any]:
        c = {"id": cid, "name": name, "status": status, "observed": observed}
        if expected is not None:
            c["expected"] = expected
        if detail:
            c["detail"] = detail
        checks.append(c)
        return c

    # --- Check 1: master row count == EXPECTED_MASTER_ROWS
    me = _entry_by_path(entries, "output/stage2/master_dataset.csv")
    if not me or not me["exists"]:
        emit("1", "stage2 master row count == 6987", "SKIP", "MISSING",
             EXPECTED_MASTER_ROWS, "master_dataset.csv not present")
    else:
        obs = me["count"]
        emit("1", "stage2 master row count == 6987",
             "PASS" if obs == EXPECTED_MASTER_ROWS else "FAIL",
             obs, EXPECTED_MASTER_ROWS)

    # --- Check 2: AHS revision keys present
    ahs_summary = contents.get(
        "output/stage3/results/ahs/ahs_candidate_summary.json")
    check2_pass = False
    if ahs_summary is None:
        emit("2", "AHS rollup revision keys present", "SKIP", "MISSING", None,
             "ahs_candidate_summary.json not present")
    else:
        block = _ahs_revision_block(ahs_summary)
        present = {k: (k in block) for k in AHS_REVISION_KEYS}
        missing = [k for k, ok in present.items() if not ok]
        if missing:
            emit("2", "AHS rollup revision keys present", "FAIL", present, None,
                 f"missing keys {missing} -> revised rollup script was not run")
            flags.append("AHS_ROLLUP_REVISION_NOT_RUN")
        else:
            check2_pass = True
            emit("2", "AHS rollup revision keys present", "PASS",
                 {k: block[k] for k in AHS_REVISION_KEYS})

    # --- Check 3: entered_pairing == pair_summary surveys.ahs.source_after_master_join
    pair_summary = contents.get("output/stage3/candidate_pairs/pair_summary.json")
    if not check2_pass:
        emit("3", "entered_pairing == pair_summary source_after_master_join",
             "SKIP", "depends on check 2")
    elif not isinstance(pair_summary, dict):
        emit("3", "entered_pairing == pair_summary source_after_master_join",
             "SKIP", "MISSING", None, "pair_summary.json not present")
    else:
        block = _ahs_revision_block(ahs_summary)
        ep = block.get("ahs_questions_entered_pairing")
        sam = (pair_summary.get("surveys", {}).get("ahs", {})
               .get("source_after_master_join"))
        emit("3", "entered_pairing == pair_summary source_after_master_join",
             "PASS" if ep == sam and ep is not None else "FAIL",
             {"entered_pairing": ep, "source_after_master_join": sam}, "equal")

    # --- Check 4: question-bucket partition. The task spec writes a 2-way
    # equation (with_candidate + all_f3 == entered); the revised rollup is a
    # 3-way partition (+ no_pair_no_shared_subtopic), which is the form that
    # actually holds. We verify the 3-way partition and also surface the 2-way
    # sum so the spec's literal form is visible.
    if not check2_pass:
        emit("4", "AHS question buckets partition entered-pairing population "
                  "(3-way)", "SKIP", "depends on check 2")
    else:
        block = _ahs_revision_block(ahs_summary)
        wc = block.get("unique_ahs_questions_with_candidate")
        f3 = block.get("no_candidate_entered_all_f3")
        npp = block.get("no_pair_no_shared_subtopic")
        ep = block.get("ahs_questions_entered_pairing")
        vals = [wc, f3, npp, ep]
        if any(v is None for v in vals):
            emit("4", "AHS question buckets partition entered-pairing "
                      "population (3-way)", "FAIL",
                 {"with_candidate": wc, "all_f3": f3, "no_pair": npp,
                  "entered": ep}, None, "a partition term is null")
        else:
            three_way = wc + f3 + npp
            two_way = wc + f3
            emit("4", "AHS question buckets partition entered-pairing "
                      "population (3-way)",
                 "PASS" if three_way == ep else "FAIL",
                 {"with_candidate": wc, "all_f3": f3, "no_pair": npp,
                  "three_way_sum": three_way, "two_way_sum_spec_literal": two_way,
                  "entered": ep}, ep,
                 "spec literal is 2-way (omits no_pair); 3-way is the partition "
                 "the revised rollup asserts")

    # --- Check 5: TEVV stage3 verdict + divergence count; extract directional_bias
    tevv = contents.get(TEVV_PATH)
    if not isinstance(tevv, dict):
        emit("5", "TEVV stage3 ACKNOWLEDGED_DIVERGENCE, 21 divergences",
             "FAIL" if tevv is not None else "SKIP", "MISSING", None,
             "TEVV evidence JSON not present (it should be committed under docs/)")
    else:
        results = tevv.get("results", [])
        s3 = next((r for r in results if isinstance(r, dict)
                   and r.get("stage") == TEVV_STAGE), None)
        if s3 is None:
            emit("5", "TEVV stage3 ACKNOWLEDGED_DIVERGENCE, 21 divergences",
                 "FAIL", "no stage3 result block", None,
                 "results[] has no entry with stage=='stage3'")
        else:
            verdict = s3.get("verdict")
            divs = s3.get("divergences", [])
            ndiv = len(divs) if isinstance(divs, list) else None
            ok = (verdict == TEVV_VERDICT_EXPECTED
                  and ndiv == TEVV_DIVERGENCE_EXPECTED)
            emit("5", "TEVV stage3 ACKNOWLEDGED_DIVERGENCE, 21 divergences",
                 "PASS" if ok else "FAIL",
                 {"verdict": verdict, "divergence_count": ndiv},
                 {"verdict": TEVV_VERDICT_EXPECTED,
                  "divergence_count": TEVV_DIVERGENCE_EXPECTED})
            bias = [{"signature": d.get("signature"),
                     "dimension": d.get("dimension"),
                     "directional_bias": d.get("directional_bias")}
                    for d in (divs if isinstance(divs, list) else [])]
            extras["tevv_directional_bias_PROVISIONAL"] = {
                "WARNING": "PROVISIONAL -- pending SME review. MUST NOT enter "
                           "the report as fact; carried only so the report can "
                           "say these biases exist and are provisional.",
                "count": len(bias),
                "biases": bias,
            }
            flags.append("TEVV_DIRECTIONAL_BIAS_PROVISIONAL")

    # --- Check 6: cross-foot pairs vs final classifications per survey
    for sv in SURVEYS:
        pe = _entry_by_path(entries,
                            f"output/stage3/candidate_pairs/pairs_{sv}.csv")
        fe = _entry_by_path(
            entries,
            f"output/stage3/results/{sv}/final_barrier_classifications.csv")
        pc = pe["count"] if pe and pe["exists"] else None
        fc = fe["count"] if fe and fe["exists"] else None
        if pc is None or fc is None:
            emit(f"6.{sv}", f"cross-foot pairs vs final ({sv})", "SKIP",
                 {"pairs": pc, "final": fc}, None,
                 "one or both files missing")
        else:
            emit(f"6.{sv}", f"cross-foot pairs vs final ({sv})",
                 "PASS" if pc == fc else "FAIL",
                 {"pairs": pc, "final": fc, "match": pc == fc}, None,
                 "" if pc == fc else
                 "non-fatal: arbitration drops can make final < pairs")

    return checks, flags, extras


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="v2 report numbers extraction + pipeline diagnostic.")
    ap.add_argument("--output-dir", default="output/report",
                    help="directory for v2_report_numbers.json "
                         "(its own output; default: output/report)")
    args = ap.parse_args()

    machine = socket.gethostname()
    generated_at = datetime.now(timezone.utc).isoformat()
    ghead = git_head()
    cwd = Path.cwd()
    v2_sentinel = Path("config/stage3.yaml").exists()

    entries, accounted = build_manifest()
    unexpected = find_unexpected(accounted)
    contents, parse_flags = capture_json_contents(entries)
    checks, check_flags, extras = run_checks(entries, contents)

    flags = parse_flags + check_flags
    if not v2_sentinel:
        flags.append("NOT_IN_V2_CWD")

    found = sum(1 for e in entries if e["exists"])
    missing = sum(1 for e in entries if not e["exists"])
    n_pass = sum(1 for c in checks if c["status"] == "PASS")
    n_fail = sum(1 for c in checks if c["status"] == "FAIL")
    n_skip = sum(1 for c in checks if c["status"] == "SKIP")

    structure: dict[str, Any] = {
        "generated_at": generated_at,
        "machine": machine,
        "git_head": ghead,
        "cwd": str(cwd),
        "v2_sentinel_present": v2_sentinel,
        "summary": {
            "files_total": len(entries),
            "files_found": found,
            "files_missing": missing,
            "checks_pass": n_pass,
            "checks_fail": n_fail,
            "checks_skip": n_skip,
            "flags": flags,
        },
        "manifest": entries,
        "unexpected_files": unexpected,
        "checks": checks,
        "tevv_provisional": extras.get("tevv_directional_bias_PROVISIONAL"),
        "json_contents": contents,
    }

    # --- File output: full, uncapped json_contents. This is the script's own
    # output, not under output/stage*.
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "v2_report_numbers.json"
    out_file.write_text(json.dumps(structure, indent=2, default=str),
                        encoding="utf-8")

    # --- Stdout digest: capped json_contents.
    digest_struct = dict(structure)
    digest_struct["json_contents"] = cap_json_contents(contents)

    headline = "\n".join([
        "v2 REPORT NUMBERS DIGEST",
        f"machine: {machine}",
        f"generated_at: {generated_at}",
        f"git_head: {ghead}",
        f"cwd: {cwd}  (v2_sentinel: {v2_sentinel})",
        f"files: {found}/{len(entries)} present, {missing} MISSING",
        f"checks: {n_pass} PASS / {n_fail} FAIL / {n_skip} SKIP",
        f"flags: {len(flags)}",
        f"flag_list: {', '.join(flags) if flags else 'none'}",
        f"unexpected_files: {len(unexpected)}",
    ])
    fenced = ("```json\n"
              + json.dumps(digest_struct, indent=2, default=str)
              + "\n```")
    digest = headline + "\n\n" + fenced

    print(digest)
    print(f"DIGEST_CHARS: {len(digest)}")
    print(f"WROTE: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
