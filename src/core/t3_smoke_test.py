#!/usr/bin/env python3
"""T3 smoke test: real concept-mapper Stage 1 prompt against the harness.

Validates that the harness 0.2.0 handles this project's actual prompt shape:
- Full Census taxonomy embedded
- 10 questions per call (the v1 batch size)
- Two raters from a model pool, selected per task
- Structured JSON output expected

Touches NO validated work. Output goes to output/t3_smoke/ (gitignored).

Pre-requisites:
  - usai-harness 0.2.0 installed in this Python env
  - usai-harness project-init has been run (so usai_harness.yaml exists at repo root)
  - usai_harness.yaml has been edited to include both raters in the pool
    (see "Required edit to usai_harness.yaml" section in the task notes)

Usage from concept-mapper repo root:
    python src/core/t3_smoke_test.py
"""

import asyncio
import json
import sys
from pathlib import Path

import pandas as pd

# Resolve paths relative to this script regardless of CWD
SCRIPT_DIR = Path(__file__).resolve().parent  # src/core/
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # concept-mapper root

# Make src/core/ importable so we can reuse v1's prompt builder unchanged
sys.path.insert(0, str(SCRIPT_DIR))
from llm_categorization import create_prompt  # noqa: E402

from usai_harness import USAiClient  # noqa: E402

QUESTIONS_CSV = PROJECT_ROOT / "data" / "raw" / "PublicSurveyQuestionsMap.csv"
TAXONOMY_JSON = PROJECT_ROOT / "data" / "raw" / "census_survey_explorer_taxonomy.json"
OUTPUT_DIR = PROJECT_ROOT / "output" / "t3_smoke"
REPORT_PATH = OUTPUT_DIR / "t3_smoke_report.md"

# Rater label -> exact model name from the catalog. Both must be in the
# pool declared in usai_harness.yaml at repo root.
RATERS = {
    "rater_a": None,  # filled in at runtime from pool
    "rater_b": None,  # filled in at runtime from pool
}


def load_questions_sample(n: int = 10, seed: int = 42):
    """Deterministic 10-question sample matching v1's expected shape."""
    df = pd.read_csv(QUESTIONS_CSV)
    df = df[df["Question"].notna() & (df["Question"].astype(str).str.strip() != "")]
    sample = df.sample(n=n, random_state=seed).reset_index(drop=True)

    questions = []
    for idx, row in sample.iterrows():
        question = row["Question"]
        surveys = [c for c in sample.columns if c != "Question" and pd.notna(row[c])]
        survey = surveys[0] if surveys else "Unknown"
        questions.append({"id": int(idx), "survey": survey, "question": question})
    return questions


def load_taxonomy_full():
    with open(TAXONOMY_JSON, "r", encoding="utf-8") as f:
        return json.load(f)["taxonomy"]


def parse_response(task_result):
    """Pull the assistant text out of an OpenAI-format response and parse JSON."""
    if task_result is None:
        return None, "no task result"
    if not task_result.success:
        return None, f"task failed: {task_result.error} (status {task_result.status_code})"
    response = task_result.response
    if not isinstance(response, dict):
        return None, f"response is not a dict: {type(response).__name__}"
    choices = response.get("choices")
    if not choices:
        return None, "no choices in response"
    content = choices[0].get("message", {}).get("content", "")
    if not content:
        return None, "empty content"

    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse: {e}; first 300 chars: {content[:300]!r}"


def validate_categorizations(parsed, taxonomy, expected_n=10):
    errors = []
    if not isinstance(parsed, list):
        return [(-1, f"expected list, got {type(parsed).__name__}")]
    if len(parsed) != expected_n:
        errors.append((-1, f"expected {expected_n} categorizations, got {len(parsed)}"))

    valid_topics = set(taxonomy.keys())

    for i, obj in enumerate(parsed):
        if not isinstance(obj, dict):
            errors.append((i, f"not a dict: {type(obj).__name__}"))
            continue
        for field in ("id", "primary_topic", "primary_subtopic", "confidence",
                      "secondary_concepts", "reasoning"):
            if field not in obj:
                errors.append((i, f"missing field: {field}"))
        topic = obj.get("primary_topic")
        if topic and topic not in valid_topics:
            errors.append((i, f"primary_topic '{topic}' not in taxonomy"))
        subtopic = obj.get("primary_subtopic")
        if topic in taxonomy and subtopic not in taxonomy[topic]:
            errors.append((i, f"subtopic '{subtopic}' not under '{topic}'"))
        conf = obj.get("confidence")
        try:
            conf_f = float(conf)
            if not (0.0 <= conf_f <= 1.0):
                errors.append((i, f"confidence out of range: {conf_f}"))
        except (TypeError, ValueError):
            errors.append((i, f"confidence not numeric: {conf!r}"))
    return errors


def write_report(rater_results, ledger_lines, log_lines, log_files):
    lines = []
    lines.append("# T3 Smoke Test Report")
    lines.append("")
    lines.append("Real concept-mapper Stage 1 prompt against the harness.")
    lines.append("")
    lines.append(f"- Repo: `{PROJECT_ROOT}`")
    lines.append(f"- Sample: 10 questions, seed=42 (deterministic)")
    lines.append(f"- Prompt builder: imported from `src/core/llm_categorization.py` (unchanged)")
    lines.append("")

    overall_pass = True

    for rater_label, info in rater_results.items():
        lines.append(f"## {rater_label} — model: `{info['model']}`")
        lines.append("")
        if info.get("parse_error"):
            lines.append(f"- Parse: **FAIL** — {info['parse_error']}")
            overall_pass = False
        else:
            lines.append(f"- Parse: PASS — {len(info['parsed'])} entries returned")
        if info.get("validation_errors"):
            lines.append(f"- Validation: **FAIL** — {len(info['validation_errors'])} issue(s)")
            for idx, msg in info["validation_errors"]:
                lines.append(f"    - obj[{idx}]: {msg}")
            overall_pass = False
        elif not info.get("parse_error"):
            lines.append("- Validation: PASS — schema and taxonomy conformance OK")
        lines.append(f"- Latency: {info.get('latency_ms', 'n/a')} ms")
        lines.append(f"- Status code: {info.get('status_code', 'n/a')}")
        lines.append(f"- Raw response: `{info['output_path']}`")
        lines.append("")

    lines.append("## Cost Ledger")
    lines.append(f"- Lines added during this run: {ledger_lines}")
    if ledger_lines < 2:
        lines.append("- **FAIL** — expected at least 2 entries (one per rater)")
        overall_pass = False
    else:
        lines.append("- PASS")
    lines.append("")

    lines.append("## Call Log")
    lines.append(f"- Files: {len(log_files)}")
    lines.append(f"- Entries across files: {log_lines}")
    if log_lines < 2:
        lines.append("- **FAIL** — expected at least 2 entries")
        overall_pass = False
    else:
        lines.append("- PASS")
    lines.append("")

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**{'PASS' if overall_pass else 'FAIL'}**")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return overall_pass


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Snapshot ledger and log state BEFORE the run so we can count delta
    cfg_path = PROJECT_ROOT / "usai_harness.yaml"
    if not cfg_path.exists():
        sys.exit(f"usai_harness.yaml not found at {cfg_path}. Run `usai-harness project-init` first.")

    questions = load_questions_sample(n=10, seed=42)
    taxonomy_full = load_taxonomy_full()
    prompt = create_prompt(questions, taxonomy_full)

    # Single client; per-task model selection
    rater_results = {}
    async with USAiClient(project="concept_mapper_t3") as client:
        # Discover the pool from the loaded config
        pool_names = [m.name for m in client.config.models]
        if len(pool_names) < 2:
            sys.exit(
                f"usai_harness.yaml model pool has {len(pool_names)} member(s); T3 needs at least 2.\n"
                f"Edit usai_harness.yaml to add a second model to the `models:` list."
            )

        RATERS["rater_a"] = pool_names[0]
        RATERS["rater_b"] = pool_names[1]

        # Snapshot ledger and log state BEFORE the calls
        ledger_path = client.config.ledger_path
        log_dir = client.config.log_dir
        ledger_before = ledger_path.stat().st_size if ledger_path.exists() else 0
        log_lines_before = 0
        if log_dir.exists():
            for lf in log_dir.glob("*.jsonl"):
                log_lines_before += sum(1 for _ in lf.open(encoding="utf-8"))

        tasks = []
        for label, model_name in RATERS.items():
            tasks.append({
                "task_id": f"t3_{label}_001",
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
            })

        print(f"Running 2 tasks against {pool_names[0]} and {pool_names[1]}...")
        results = await client.batch(tasks, job_name="t3_smoke")

        for task_result in results:
            label = task_result.task_id.replace("t3_", "").replace("_001", "")
            model_name = RATERS[label]
            output_path = OUTPUT_DIR / f"raw_response_{label}.json"
            output_path.write_text(
                json.dumps({
                    "task_id": task_result.task_id,
                    "model": model_name,
                    "success": task_result.success,
                    "status_code": task_result.status_code,
                    "latency_ms": task_result.latency_ms,
                    "error": task_result.error,
                    "response": task_result.response,
                }, indent=2, default=str),
                encoding="utf-8",
            )

            parsed, parse_error = parse_response(task_result)
            validation_errors = validate_categorizations(parsed, taxonomy_full) if parsed is not None else []
            rater_results[label] = {
                "model": model_name,
                "parsed": parsed,
                "parse_error": parse_error,
                "validation_errors": validation_errors,
                "latency_ms": task_result.latency_ms,
                "status_code": task_result.status_code,
                "output_path": str(output_path),
            }

        # Compute delta after run
        ledger_after_size = ledger_path.stat().st_size if ledger_path.exists() else 0
        ledger_lines_added = 0
        if ledger_path.exists():
            with ledger_path.open(encoding="utf-8") as f:
                f.seek(ledger_before)
                ledger_lines_added = sum(1 for _ in f)

        log_lines_after = 0
        log_files = []
        if log_dir.exists():
            log_files = list(log_dir.glob("*.jsonl"))
            for lf in log_files:
                log_lines_after += sum(1 for _ in lf.open(encoding="utf-8"))
        log_lines_added = log_lines_after - log_lines_before

    overall_pass = write_report(rater_results, ledger_lines_added, log_lines_added, log_files)
    print(f"\nReport: {REPORT_PATH}")
    print(f"Verdict: {'PASS' if overall_pass else 'FAIL'}")
    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    asyncio.run(main())
