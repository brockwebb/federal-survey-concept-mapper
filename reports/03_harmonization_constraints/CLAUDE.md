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
├── 03_analysis_pipeline.py # Stage 5: Analysis
├── run_pipeline.py        # Orchestrator
│
├── docs/                  # Documentation (see catalogue below)
├── scripts/               # Supporting scripts
│   └── lib/               # Shared library code
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
- Pipeline stages: `NN_name_pipeline.py` (01, 02, 03...)
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
| `docs/SOFTWARE.md` | Script documentation and usage | When scripts change |
| `docs/methodology_log.md` | Decision log with rationale | Per major decision |

### Supporting Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| `docs/taxonomy_v1.md` | Barrier code definitions (TC, CC, RS, etc.) | Stable |
| `docs/coding_procedure.md` | How raters should apply taxonomy | Stable |
| `docs/pipeline_diagram.md` | Visual pipeline flow | Stable |
| `docs/framing_ai_assisted.md` | Research framing for AI-assisted analysis | Stable |
| `docs/barrier_coding_pipeline_documentation.md` | High-level methodology description for report | Stable - report content |

### Literature

| Document | Purpose |
|----------|---------|
| `docs/literature/README.md` | Literature review index |
| `docs/literature/literature_frameworks.md` | Survey harmonization frameworks |
| `docs/literature/perplexity_research_summary.md` | Background research |

---

## Cross-References

### V&V and Pipeline Relationship

The V&V plan (`docs/ANALYSIS_VV_PLAN.md`) validates the pipeline defined in `docs/SOFTWARE.md`:

| V&V Stage | Pipeline Stage | Key Script |
|-----------|----------------|------------|
| Stage 1: Rating | Pipeline Stage 1 | `01_barrier_pipeline.py` |
| Stage 2: Agreement | Pipeline Stage 2 | `scripts/analyze_barrier_results.py` |
| Stage 3: Arbitration | Pipeline Stage 3 | `02_arbitration_pipeline.py` |
| Stage 4: Cleanup | Pipeline Stage 4 | `scripts/clean_arbitration_data.py` |
| Stage 5: Analysis | Pipeline Stage 5 | `scripts/analyze_arbitration_agreement.py` |

**Rule:** Pipeline execution may run ahead of validation. Do not draw conclusions from unvalidated stages. Check V&V plan status before interpreting results.

### Config-Driven Paths

All scripts should read paths from `config.yaml`, not hardcode them. Check config before assuming file locations.

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

### Ending a Session

1. **Create handoff:** `../../handoffs/YYYY-MM-DD_description.md` (use system date!)
2. **Update V&V plan** if validation status changed
3. **Commit changes** with descriptive message

---

## Current State (Update as needed)

**Last updated:** 2026-01-30

| Item | Status |
|------|--------|
| V&V Stage 1 (Rating) | ✅ COMPLETE |
| V&V Stage 2 (Agreement) | ⏳ NOT STARTED |
| V&V Stage 3 (Arbitration) | 🟡 IN PROGRESS (Google at 503/1598) |
| V&V Stage 4 (Cleanup) | ⏳ NOT STARTED |
| V&V Stage 5 (Analysis) | ⏳ NOT STARTED |
| Google rate limit | 250 requests/day - data collection ongoing |

---

## Anti-Patterns to Avoid

1. **Don't create files in report root** - Use appropriate subdirectory
2. **Don't hardcode paths** - Use config.yaml
3. **Don't skip validation** - Waterfall methodology means no conclusions from unvalidated stages
4. **Don't create duplicate docs** - Check catalogue first
5. **Don't put handoffs/tasks in report dir** - They go in project root
6. **Don't trust Claude's internal date** - Always verify with `date` command
7. **Don't create monolithic scripts** - Use `scripts/lib/` for shared code

---

## Key Contacts

- **Primary researcher:** Brock Webb
- **Project repo:** federal-survey-concept-mapper

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-30 | Initial CLAUDE.md created for Report 03 |
