# CLAUDE.md - Report 03: Harmonization Constraints

**Purpose:** Session guidance for Claude (claude.ai and Claude Code) working on Report 03.

---

## CRITICAL: Date Verification

**Before creating ANY dated file, run:**
```bash
date "+%Y-%m-%d"
```

Claude's internal date is often wrong. Use system time for:
- Handoff filenames
- Log entries
- Changelog updates
- Any timestamped artifacts

---

## Pipeline Architecture

### Actual Stages (as of 2026-01-31)

| Stage | Purpose | Primary Script | Status |
|-------|---------|----------------|--------|
| 1 | Rating | `01_barrier_pipeline.py` | ✅ Complete |
| 2 | Agreement | `03_stage2_agreement.py` | ✅ Complete |
| 3 | Arbitration | `02_arbitration_pipeline.py` | ✅ Complete |
| 4 | Findings | `04_findings_pipeline.py` | ✅ Complete |
| 5 | Deliverables | `05_deliverables_pipeline.py` + `scripts/stage4_*.py` + `scripts/build_expert_review_table.py` | ✅ Complete |

### Data Flow

```
Input: 1,598 pairs from Report 02
    ↓
Stage 1: 3 raters classify each pair → output/results/stage1_*.jsonl
    ↓
Stage 2: Agreement analysis → κ=0.845, disagreement set identified
    ↓
Stage 3: 3 arbitrators resolve disagreements → output/results/stage3_*.jsonl
    ↓
Stage 4: Question-level consolidability, scoring, best-match rollup
    ↓
Stage 5: Expert review tables, stakeholder deliverables
```

### Root Pipeline Files

| File | Stage | Purpose |
|------|-------|---------|
| `01_barrier_pipeline.py` | 1 | 3 models (haiku, gpt-4o-mini, gemini) classify pairs |
| `02_arbitration_pipeline.py` | 3 | 3 arbitrators resolve disagreements |
| `03_stage2_agreement.py` | 2 | Inter-rater reliability analysis |
| `03b_stage2_extended.py` | 2 | Extended agreement analytics |
| `04_findings_pipeline.py` | 4 | Question-level consolidability |
| `05_deliverables_pipeline.py` | 5 | Scoring, rollup, expert review orchestrator |
| `run_pipeline.py` | — | Full pipeline orchestrator (all stages) |

### Stage 4 Scripts (scripts/)

| File | Purpose | Output |
|------|---------|--------|
| `stage4_scoring_bakeoff.py` | 4-method scoring comparison | `stage4_bakeoff_scores.csv` |
| `stage4_best_match_rollup.py` | Best match per question + triage | `stage4_question_best_matches.csv` |
| `stage4_triage_assignment.py` | Triage quadrant assignment | (integrated into best_match) |
| `build_expert_review_table.py` | Expert review deliverables | `expert_review_*.csv` |

### Stage 4 Outputs (output/analysis/)

| File | Description |
|------|-------------|
| `stage4_question_level.csv` | 380 rows, binary consolidable flags |
| `stage4_question_best_matches.csv` | Best ACS match per question with triage quadrant |
| `stage4_bakeoff_scores.csv` | 1,598 pairs with all 4 scoring methods |
| `stage4_survey_summary.json` | Aggregate rates (CPS 41.7%, FoodAPS 48.6%) |
| `stage4_findings_report.md` | Pipeline-generated summary |
| `stage4_topic_breakdown.csv` | By-topic consolidability |
| `stage4_f2_transformations.csv` | F2 pairs needing adjustment |
| `stage4_barrier_patterns.csv` | F3 barrier distribution |

### Documentation Status

All pipeline documentation is current as of 2026-01-31:
- `docs/SOFTWARE.md` — v4.0, all stages and scripts documented
- `docs/pipeline_diagram.md` — v4.0, accurate Mermaid diagrams for all 5 stages
- `run_pipeline.py` — Orchestrates all stages (rate, arbitrate, analyze, findings, deliverables)

---

## File Locations

### Project Root (`/federal-survey-concept-mapper/`)

| Directory | Purpose | Gitignored |
|-----------|---------|------------|
| `handoffs/` | Session handoff documents | ✅ Yes |
| `cc_tasks/` | Claude Code task files | ✅ Yes |
| `reports/03_harmonization_constraints/` | Report 03 working directory | No |

**Handoffs go in root `handoffs/`, NOT in report directory.**
**Claude Code tasks go in root `cc_tasks/`, NOT in report directory.**

### Report 03 Directory Structure

```
reports/03_harmonization_constraints/
├── CLAUDE.md              # This file - session guidance
├── README.md              # Setup instructions
├── config.yaml            # Pipeline configuration
├── 01_barrier_pipeline.py # Stage 1: Rating
├── 02_arbitration_pipeline.py # Stage 3: Arbitration
├── 03_stage2_agreement.py # Stage 2: Agreement
├── 03b_stage2_extended.py # Stage 2: Extended
├── 04_findings_pipeline.py # Stage 4: Findings
├── run_pipeline.py        # Orchestrator
│
├── docs/                  # Documentation (see catalogue below)
├── scripts/               # Supporting scripts
│   ├── lib/               # Shared library code
│   ├── stage4_*.py        # Stage 4 analysis scripts
│   └── build_expert_review_table.py  # Stage 5
├── data/                  # Input data (from Report 02)
└── output/                # Pipeline outputs
    ├── results/           # Raw JSONL from raters/arbitrators
    ├── analysis/          # Cleaned/merged analysis files
    └── checkpoints/       # Resume state
```

---

## Naming Conventions

### Handoffs
```
handoffs/YYYY-MM-DD_brief_description.md
```
Example: `handoffs/2026-01-30_stage1_validation_complete.md`

### Claude Code Tasks
```
cc_tasks/CLAUDE_CODE_TASK_brief_description.md
```
Example: `cc_tasks/CLAUDE_CODE_TASK_fix_google_rate_limit.md`

### Scripts
- Pipeline stages: `NN_name_pipeline.py` (01, 02, 03, 04...)
- Stage scripts: `scripts/stageN_verb_noun.py`
- Analysis scripts: `scripts/verb_noun.py` (analyze_*, clean_*, compare_*)
- Library modules: `scripts/lib/noun.py` (io_utils, stats, taxonomy)

### Output Files
- Raw results: `output/results/{stage}_{rater/arbitrator}_{model}.jsonl`
- Cleaned data: `output/analysis/{stage}_deduped_{source}.jsonl`
- Merged data: `output/analysis/{stage}_merged.csv`
- Stats/reports: `output/analysis/{name}_report.{json,md}`

---

## Document Catalogue

### Primary Reference Documents

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| `docs/ANALYSIS_VV_PLAN.md` | Validation status and findings | Per validation stage |
| `docs/SOFTWARE.md` | Script documentation and usage (v4.0) | When scripts change |
| `docs/methodology_log.md` | Decision log with rationale | Per major decision |
| `docs/pipeline_diagram.md` | Visual pipeline flow (v4.0, Mermaid) | When pipeline changes |

### Supporting Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| `docs/taxonomy_v1.md` | Barrier code definitions (TC, CC, RS, etc.) | Stable |
| `docs/coding_procedure.md` | How raters should apply taxonomy | Stable |
| `docs/framing_ai_assisted.md` | Research framing for AI-assisted analysis | Stable |
| `docs/barrier_coding_pipeline_documentation.md` | High-level methodology description for report | Stable - report content |
| `docs/stage4_research_framing.md` | Stage 4 research question framing and combinatorial math context | Active |
| `docs/stage4_ensemble_methodology.md` | Ensemble scoring theory (entropy, Bayesian, Borda) - **sober framing applied** | Active |
| `docs/methodology_log_decision_016.md` | Detailed Decision 016 justification with citation queries | Active |

### Literature

| Document | Purpose |
|----------|---------|
| `docs/literature/README.md` | Literature review index |
| `docs/literature/literature_frameworks.md` | Survey harmonization frameworks |
| `docs/literature/perplexity_research_summary.md` | Background research |
| `docs/literature/perplexity_entropy_methodology_review.md` | Decision 016 novelty assessment (full Perplexity response) |
| `docs/literature/decision_016_citations.md` | Extracted citations (has disclaimer re: sober framing) |

---

## Current State (Update as needed)

**Last updated:** 2026-01-31

| Item | Status |
|------|--------|
| V&V Stage 1 (Rating) | ✅ COMPLETE (2026-01-30) |
| V&V Stage 2 (Agreement) | ✅ COMPLETE (2026-01-30) |
| V&V Stage 3 (Arbitration) | ✅ COMPLETE (2026-01-31) - QC passed 11/11 |
| V&V Stage 4 (Findings) | ✅ COMPLETE (2026-01-31) |
| V&V Stage 5 (Deliverables) | ✅ COMPLETE (2026-01-31) |

### Stage 3 Summary (Complete)

**Data:** OpenAI/Anthropic 1,598 pairs each, Google 751 pairs (47%)  
**Agreement:** Two-way κ=0.796, Three-way κ=0.833  
**QC:** 11/11 checks passed (2026-01-31)

### Stage 4 & 5 Summary (Complete)

- Question-level consolidability: CPS 41.7%, FoodAPS 48.6%
- Scoring bake-off: 4 methods tested (Composite, Entropy, Bayesian, Borda)
- Best-match rollup: `stage4_question_best_matches.csv` (380 questions)
- Triage quadrants: Q1=151, Q2=136, Q3=40, Q4=53
- Expert review tables: `expert_review_combined.csv` (380 rows, 17 columns)
- Pipeline integrated: `run_pipeline.py --stage findings` and `--stage deliverables`

**Key Decisions:**
- Decision 016: Two-axis triage (Borda for direction, Entropy for stability)
- Sober framing: Useful operational tool, not theoretical discovery
- Research threads parked in `docs/stage4_ensemble_methodology.md` "Future Exploration" section

### Triage Framework (Two-Axis)

| Quadrant | Borda | Entropy | Count | Action |
|----------|-------|---------|-------|--------|
| Q1 | High | High | 151 | Auto-accept (confident consolidable) |
| Q2 | Low | High | 136 | Auto-reject (confident non-consolidable) |
| Q3 | High | Low | 40 | Expert review (edge case) |
| Q4 | Low | Low | 53 | Expert review (ambiguous) |

---

## Session Workflow

### Starting a Session

1. **Check system date:** `date "+%Y-%m-%d"`
2. **Read recent handoffs:** `ls -la ../../handoffs/ | tail -5`
3. **Check V&V status:** Review `docs/ANALYSIS_VV_PLAN.md` stage tracker
4. **Check pipeline status:** `ls output/results/` and `ls output/analysis/`

### During Session

- **Document decisions** in `docs/methodology_log.md`
- **Update V&V plan** when validating stages
- **Update SOFTWARE.md** when creating/modifying scripts
- **Create scripts in `scripts/`**, not inline in notebooks or terminals
- **Integrate scripts into pipeline** - no orphaned scripts

### Ending a Session

1. **Create handoff:** `../../handoffs/YYYY-MM-DD_description.md` (use system date!)
2. **Update V&V plan** if validation status changed
3. **Commit changes** with descriptive message

---

## Anti-Patterns to Avoid

1. **Don't create files in report root** - Use appropriate subdirectory
2. **Don't hardcode paths** - Use config.yaml
3. **Don't skip validation** - Waterfall methodology means no conclusions from unvalidated stages
4. **Don't create duplicate docs** - Check catalogue first
5. **Don't put handoffs/tasks in report dir** - They go in project root
6. **Don't trust Claude's internal date** - Always verify with `date` command
7. **Don't create monolithic scripts** - Use `scripts/lib/` for shared code
8. **Don't create orphan scripts** - Integrate into pipeline architecture
9. **Don't skip SOFTWARE.md updates** - Document what you build

---

## Key Contacts

- **Primary researcher:** Brock Webb
- **Project repo:** federal-survey-concept-mapper

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-30 | Initial CLAUDE.md created for Report 03 |
| 2026-01-31 | Updated Current State: Stage 2 COMPLETE, Stage 3 metrics/issues, arbitrator behavioral findings |
| 2026-01-31 | Stage 3 QC passed (11/11), Stage 4 in progress. Added docs: stage4_research_framing.md, stage4_ensemble_methodology.md. Decision 016 documented. |
| 2026-01-31 | Added Pipeline Architecture section with actual stage mapping. Marked stale docs. Added triage framework summary. Added anti-patterns 8-9. |
| 2026-01-31 | Stages 4+5 COMPLETE. SOFTWARE.md v4.0. run_pipeline.py integrated. 05_deliverables_pipeline.py created. |
