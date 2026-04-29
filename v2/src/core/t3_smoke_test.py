#!/usr/bin/env python3
"""T3 smoke test: real concept-mapper Stage 1 prompt against harness 0.4.0+.

Validates that the harness handles this project's actual prompt shape:
  - Full Census taxonomy embedded
  - 10 questions per call (the v1 batch size)
  - Two raters from the pool, selected per task
  - Structured JSON output expected

This is greenfield code in the v2/ tree. Zero imports from the v1 source
tree. Dependency surface is exactly:
  - usai_harness
  - pandas
  - standard library

Run from the v2/ directory:
    cd v2
    python src/core/t3_smoke_test.py
"""

import asyncio
import json
import sys
from pathlib import Path

import pandas as pd
from usai_harness import USAiClient

# Resolve paths relative to this script regardless of CWD
SCRIPT_DIR = Path(__file__).resolve().parent       # v2/src/core/
V2_ROOT = SCRIPT_DIR.parent.parent                  # v2/

QUESTIONS_CSV = V2_ROOT / "data" / "raw" / "PublicSurveyQuestionsMap.csv"
TAXONOMY_JSON = V2_ROOT / "data" / "raw" / "census_survey_explorer_taxonomy.json"
OUTPUT_DIR = V2_ROOT / "output" / "t3_smoke"
REPORT_PATH = OUTPUT_DIR / "t3_smoke_report.md"


# Prompt builder is inlined here intentionally. v2/ has zero v1 imports;
# duplicating the prompt text is the correct trade for dependency isolation.
# When the v2 Stage 1 module is built, this same function moves to
# v2/src/lib/categorization_prompts.py and gets imported from there.
def create_prompt(batch, taxonomy):
    return f"""You are categorizing federal survey questions using the official U.S. Census Bureau taxonomy.

TAXONOMY:
{json.dumps(taxonomy, indent=2)}

TASK:
For each question below, assign:
1. Primary concept: The most relevant Topic and Subtopic
2. Secondary concepts: 0-3 additional relevant subtopics (if applicable)
3. Confidence: 0-1 score for primary assignment
4. Reasoning: Brief explanation (1-2 sentences)

QUESTIONS TO CATEGORIZE:
{json.dumps(batch, indent=2)}

Return a JSON array with one object per question, in the same order. Format:
[
  {{
    "id": 0,
    "primary_topic": "Economic",
    "primary_subtopic": "Income",
    "confidence": 0.95,
    "secondary_concepts": [
      {{"topic": "Economic", "subtopic": "Employment Status"}},
      {{"topic": "Demographic", "subtopic": "Age"}}
    ],
    "reasoning": "Question asks about household income sources."
  }},
  ...
]

Return ONLY the JSON array, no other text."""


def load_questions_sample(n=10, seed=42):
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
        for field_name in ("id", "primary_topic", "primary_subtopic",
                           "confidence", "secondary_concepts", "reasoning"):
            if field_name not in obj:
                errors.append((i, f"missing field: {field_name}"))
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


def write_report(rater_results, ledger_lines_added, log_lines_added, log_files):
    lines = []
    lines.append("# T3 Smoke Test Report (v2)")
    lines.append("")
    lines.append("Real concept-mapper Stage 1 prompt against harness 0.3.0.")
    lines.append("Greenfield script in `v2/`, no v1 imports.")
    lines.append("")
    lines.append(f"- v2 root: `{V2_ROOT}`")
    lines.append(f"- Sample: 10 questions, seed=42 (deterministic)")
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
            lines.append("- Validation: PASS")
        lines.append(f"- Latency: {info.get('latency_ms', 'n/a')} ms")
        lines.append(f"- Status code: {info.get('status_code', 'n/a')}")
        lines.append(f"- Raw response: `{info['output_path']}`")
        lines.append("")

    lines.append("## Cost Ledger")
    lines.append(f"- Lines added during this run: {ledger_lines_added}")
    if ledger_lines_added < 2:
        lines.append("- **FAIL** — expected at least 2 entries (one per rater)")
        overall_pass = False
    else:
        lines.append("- PASS")
    lines.append("")

    lines.append("## Call Log")
    lines.append(f"- Files: {len(log_files)}")
    lines.append(f"- Entries added during this run: {log_lines_added}")
    if log_lines_added < 2:
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

    cfg_path = V2_ROOT / "usai_harness.yaml"
    if not cfg_path.exists():
        sys.exit(
            f"usai_harness.yaml not found at {cfg_path}.\n"
            f"Run `usai-harness project-init` from the v2/ directory first."
        )

    # Ledger and log dir are harness client kwargs, not project-config fields.
    # Define them here so the post-run delta counting reads from the same
    # paths the client writes to.
    ledger_path = V2_ROOT / "cost_ledger.jsonl"
    log_dir = V2_ROOT / "logs"

    questions = load_questions_sample(n=10, seed=42)
    taxonomy_full = load_taxonomy_full()
    prompt = create_prompt(questions, taxonomy_full)

    rater_results = {}
    async with USAiClient(
        project="concept_mapper_v2_t3",
        ledger_path=ledger_path,
        log_dir=log_dir,
    ) as client:
        pool_names = [m.name for m in client.config.models]
        if len(pool_names) < 2:
            sys.exit(
                f"usai_harness.yaml model pool has {len(pool_names)} member(s); "
                f"T3 needs at least 2. Edit the YAML to add a second rater."
            )

        ledger_before = ledger_path.stat().st_size if ledger_path.exists() else 0
        log_lines_before = 0
        if log_dir.exists():
            for lf in log_dir.glob("*.jsonl"):
                log_lines_before += sum(1 for _ in lf.open(encoding="utf-8"))

        # Build one task per rater. Both send the same 10-question batch.
        tasks = []
        for rater_label, model_name in [
            ("rater_a", pool_names[0]),
            ("rater_b", pool_names[1]),
        ]:
            tasks.append({
                "task_id": f"t3_{rater_label}",
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
            })

        print(f"Pool: {pool_names}")
        print(f"Sending T3 batch (2 tasks, 10 questions each)...")
        results = await client.batch(tasks, job_name="t3_smoke")

        rater_label_by_task = {t["task_id"]: rater_label
                                for t, (rater_label, _)
                                in zip(tasks,
                                       [("rater_a", pool_names[0]),
                                        ("rater_b", pool_names[1])])}
        model_by_task = {t["task_id"]: t["model"] for t in tasks}

        for task_result in results:
            label = rater_label_by_task.get(task_result.task_id, task_result.task_id)
            model_name = model_by_task.get(task_result.task_id, "unknown")
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
            validation_errors = (
                validate_categorizations(parsed, taxonomy_full)
                if parsed is not None else []
            )
            rater_results[label] = {
                "model": model_name,
                "parsed": parsed,
                "parse_error": parse_error,
                "validation_errors": validation_errors,
                "latency_ms": task_result.latency_ms,
                "status_code": task_result.status_code,
                "output_path": str(output_path),
            }

        # Compute deltas after the run
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

    overall_pass = write_report(
        rater_results, ledger_lines_added, log_lines_added, log_files,
    )
    print(f"\nReport: {REPORT_PATH}")
    print(f"Verdict: {'PASS' if overall_pass else 'FAIL'}")
    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    asyncio.run(main())
