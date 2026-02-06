#!/bin/bash
# =============================================================================
# REPO RESTRUCTURE MIGRATION SCRIPT
# federal-survey-concept-mapper
# Date: 2026-02-06
#
# Usage:
#   chmod +x migrate.sh
#   ./migrate.sh          # Dry run (shows what would happen)
#   ./migrate.sh --execute # Actually do it
# =============================================================================

set -euo pipefail

REPO_ROOT="/Users/brock/Documents/GitHub/federal-survey-concept-mapper"
R03="$REPO_ROOT/reports/03_harmonization_constraints"
R02="$REPO_ROOT/reports/02_question_consolidation"
R01="$REPO_ROOT/reports/01_llm_concept_mapping"
DRY_RUN=true

if [[ "${1:-}" == "--execute" ]]; then
    DRY_RUN=false
    echo "🔥 EXECUTING MIGRATION (not a dry run)"
else
    echo "🔍 DRY RUN — pass --execute to actually migrate"
fi

cd "$REPO_ROOT"

run() {
    if $DRY_RUN; then
        echo "  [DRY] $*"
    else
        echo "  [RUN] $*"
        eval "$@"
    fi
}

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 0: Safety — tag current state"
echo "=========================================="

if ! $DRY_RUN; then
    git add -A && git commit -m "pre-restructure: snapshot current state" --allow-empty || true
    git tag -f pre-restructure
    echo "  Tagged as 'pre-restructure'. Rollback: git reset --hard pre-restructure"
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 1: Delete build artifacts"
echo "=========================================="

echo "--- Quarto build output (_output dirs) ---"
run "rm -rf '$R03/presentation/_output'"
run "rm -rf '$R03/report/_output'"
run "rm -rf '$R02/_output'"

echo "--- Quarto cache (.quarto dirs) ---"
run "rm -rf '$R03/presentation/.quarto'"
run "rm -rf '$R03/report/.quarto'"
run "rm -rf '$R02/.quarto'"

echo "--- LaTeX intermediates ---"
run "rm -f '$R03/report/index.aux' '$R03/report/index.log' '$R03/report/index.toc' '$R03/report/index.tex'"

echo "--- Empty mediabag dirs ---"
run "rm -rf '$R03/report/index_files'"

echo "--- Nested report/report ---"
run "rm -rf '$R03/report/report'"

echo "--- Duplicate slides_files (libs 2 through libs 10) ---"
for i in 2 3 4 5 6 7 8 9 10; do
    run "rm -rf '$R03/presentation/_output/slides_files/libs $i'"
done
# The entire _output was already deleted above, but being explicit

echo "--- Presentation tracking/summary docs (superseded) ---"
run "rm -f '$R03/presentation/BACKUP_SLIDES_SUMMARY.md'"
run "rm -f '$R03/presentation/CHANGES_COMPLETE.md'"
run "rm -f '$R03/presentation/HARMONIZATION_DISTRIBUTION_SUMMARY.md'"
run "rm -f '$R03/presentation/IMAGE_UPDATE_SUMMARY.md'"
run "rm -f '$R03/presentation/MERMAID_TO_PNG_SUMMARY.md'"
run "rm -f '$R03/presentation/PIPELINE_INTEGRATION_SUMMARY.md'"
run "rm -f '$R03/presentation/QUESTION_CONSOLIDATION_DISTRIBUTION_SUMMARY.md'"
run "rm -f '$R03/presentation/RESPONDENT_BURDEN_RESTORATION.md'"
run "rm -f '$R03/presentation/SCAFFOLD_VERIFICATION.md'"
run "rm -f '$R03/presentation/THREE_LAYER_VALUE_VERIFICATION.md'"
run "rm -f '$R03/presentation/VALUE_PROPOSITION_UPDATES_SUMMARY.md'"
run "rm -f '$R03/presentation/QUICK_START.md'"
run "rm -f '$R03/presentation/README.md'"

echo "--- R03 pycache ---"
run "rm -rf '$R03/__pycache__'"

echo "--- DS_Store files ---"
run "find '$REPO_ROOT' -name '.DS_Store' -delete 2>/dev/null || true"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 1 — remove build artifacts and duplicates" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 2: Create target directories"
echo "=========================================="

run "mkdir -p '$REPO_ROOT/src/core'"
run "mkdir -p '$REPO_ROOT/src/report_02'"
run "mkdir -p '$REPO_ROOT/src/report_03/pipelines'"
run "mkdir -p '$REPO_ROOT/src/report_03/scripts/lib'"
run "mkdir -p '$REPO_ROOT/src/notebooks'"
run "mkdir -p '$REPO_ROOT/output/report_01'"
run "mkdir -p '$REPO_ROOT/output/report_02/data'"
run "mkdir -p '$REPO_ROOT/output/report_03'"
run "mkdir -p '$REPO_ROOT/output/archive'"
run "mkdir -p '$REPO_ROOT/docs/project'"
run "mkdir -p '$REPO_ROOT/docs/report_03/literature'"

if ! $DRY_RUN; then
    # Git needs files in dirs to track them
    :
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 3: Move code → src/"
echo "=========================================="

echo "--- Original src/ scripts → src/core/ ---"
for f in "$REPO_ROOT/src/"*.py; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/src/core/$fname'"
done

echo "--- Notebooks → src/notebooks/ ---"
for f in "$REPO_ROOT/notebooks/"*.ipynb; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/src/notebooks/$fname'"
done
run "rm -rf '$REPO_ROOT/notebooks'" 

echo "--- Report 03 pipeline scripts → src/report_03/pipelines/ ---"
for f in 01_barrier_pipeline.py 02_arbitration_pipeline.py 03_analysis_pipeline.py \
         03_stage2_agreement.py 03b_stage2_extended.py 04_findings_pipeline.py \
         05_deliverables_pipeline.py run_pipeline.py run_full_pipeline.py; do
    [ -f "$R03/$f" ] || continue
    run "git mv '$R03/$f' '$REPO_ROOT/src/report_03/pipelines/$f'"
done

echo "--- Report 03 analysis scripts → src/report_03/scripts/ ---"
for f in "$R03/scripts/"*.py; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/src/report_03/scripts/$fname'"
done

echo "--- Report 03 scripts/lib → src/report_03/scripts/lib/ ---"
for f in "$R03/scripts/lib/"*.py; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/src/report_03/scripts/lib/$fname'"
done
# Clean up pycache in lib
run "rm -rf '$R03/scripts/lib/__pycache__'"
run "rm -rf '$R03/scripts/lib'" 
run "rm -rf '$R03/scripts'"

echo "--- Report 03 CLAUDE.md → src/report_03/ ---"
run "git mv '$R03/CLAUDE.md' '$REPO_ROOT/src/report_03/CLAUDE.md'"

echo "--- Report 02 build scripts → src/report_02/ ---"
[ -f "$R02/build_report.py" ] && run "git mv '$R02/build_report.py' '$REPO_ROOT/src/report_02/build_report.py'"
for f in "$R02/scripts/"*.py; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/src/report_02/$fname'"
done
# Move non-python config files from scripts too
for f in "$R02/scripts/"*.json "$R02/scripts/"*.css; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/src/report_02/$fname'"
done
run "rm -rf '$R02/scripts'"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 3 — move all code to src/" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 4: Move output/data → output/"
echo "=========================================="

echo "--- Report 03 output/ → output/report_03/ ---"
# Move subdirectories
for d in analysis checkpoints results visuals; do
    [ -d "$R03/output/$d" ] || continue
    run "git mv '$R03/output/$d' '$REPO_ROOT/output/report_03/$d'"
done

echo "--- Report 03 archive → output/archive/gpt4omini_error ---"
[ -d "$R03/output_archive_gpt4omini_error" ] && \
    run "git mv '$R03/output_archive_gpt4omini_error' '$REPO_ROOT/output/archive/gpt4omini_error'"

echo "--- Report 03 input data → data/processed/ ---"
for f in "$R03/data/"*.csv; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    # These are derived from Report 02, so they're processed data
    run "git mv '$f' '$REPO_ROOT/data/processed/$fname'"
done
run "rm -rf '$R03/data'"
run "rm -rf '$R03/output'"

echo "--- Report 02 data → output/report_02/data/ ---"
for f in "$R02/data/"*.csv "$R02/data/"*.json; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/output/report_02/data/$fname'"
done
run "rm -rf '$R02/data'"

echo "--- Report 01 data → output/report_01/ ---"
run "mkdir -p '$REPO_ROOT/output/report_01'"
for f in "$R01/data/"*.csv; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/output/report_01/$fname'"
done
run "rm -rf '$R01/data'"

echo "--- Report 01 figures → output/report_01/ ---"
for f in "$R01/figures/"*.png; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/output/report_01/$fname'"
done
run "rm -rf '$R01/figures'"

echo "--- Report 01 FULL_REPORT → output/report_01/ ---"
[ -f "$R01/FULL_REPORT.md" ] && run "git mv '$R01/FULL_REPORT.md' '$REPO_ROOT/output/report_01/FULL_REPORT.md'"

echo "--- Report 02 figures → output/report_02/ ---"
run "mkdir -p '$REPO_ROOT/output/report_02/figures'"
for f in "$R02/figures/"*.png; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/output/report_02/figures/$fname'"
done
run "rm -rf '$R02/figures'"

echo "--- Report 03 report figures (duplicates of visuals) → remove ---"
# These are copies of what's now in output/report_03/visuals/
run "rm -rf '$R03/report/figures'"

echo "--- Report 03 presentation images (duplicates) → remove ---"
# These are copies of what's now in output/report_03/visuals/
run "rm -rf '$R03/presentation/images'"

echo "--- Report 03 presentation PDFs → output/report_03/ ---"
run "mkdir -p '$REPO_ROOT/output/report_03/pdf'"
for f in "$R03/presentation/"*.pdf; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/output/report_03/pdf/$fname'"
done

echo "--- Report 02 FULL_REPORT files → output/report_02/ ---"
[ -f "$R02/FULL_REPORT.md" ] && run "git mv '$R02/FULL_REPORT.md' '$REPO_ROOT/output/report_02/FULL_REPORT.md'"
[ -f "$R02/FULL_REPORT.pdf" ] && run "git mv '$R02/FULL_REPORT.pdf' '$REPO_ROOT/output/report_02/FULL_REPORT.pdf'"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 4 — consolidate output and data" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 5: Move docs"
echo "=========================================="

echo "--- Report 03 docs → docs/report_03/ ---"
for f in "$R03/docs/"*.md; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/docs/report_03/$fname'"
done

echo "--- Report 03 literature → docs/report_03/literature/ ---"
for f in "$R03/docs/literature/"*; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    run "git mv '$f' '$REPO_ROOT/docs/report_03/literature/$fname'"
done
run "rm -rf '$R03/docs'"

echo "--- Top-level docs → docs/project/ ---"
for f in "$REPO_ROOT/docs/"*.md; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    # Skip if it's already in a subdirectory
    run "git mv '$f' '$REPO_ROOT/docs/project/$fname'"
done

echo "--- Report 03 config → config/ ---"
[ -f "$R03/config.yaml" ] && run "git mv '$R03/config.yaml' '$REPO_ROOT/config/report_03.yaml'"

echo "--- Report 03 README → docs/report_03/ ---"
[ -f "$R03/README.md" ] && run "git mv '$R03/README.md' '$REPO_ROOT/docs/report_03/README.md'"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 5 — organize documentation" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 6: Clean reports/ to publishable only"
echo "=========================================="

echo "--- Create figure symlinks ---"
# Report 03 report needs figures from output
run "ln -sf '../../../output/report_03/visuals' '$R03/report/figures'"
# Report 03 presentation needs images from output  
run "ln -sf '../../../output/report_03/visuals' '$R03/presentation/images'"
# Report 02 needs figures
run "ln -sf '../../output/report_02/figures' '$R02/figures'"
# Report 01 needs figures
run "mkdir -p '$R01/figures'"
run "ln -sf '../../output/report_01' '$R01/figures'"

echo "--- Move Report 02 working docs → docs/report_02/ ---"
run "mkdir -p '$REPO_ROOT/docs/report_02'"
for f in acs_linked_supplements_background.md case_studies_cps.md case_studies_foodaps.md \
         methodology_classification_workflow.md question_level_matching_design.md \
         synthesis_and_conclusions.md; do
    [ -f "$R02/$f" ] && run "git mv '$R02/$f' '$REPO_ROOT/docs/report_02/$f'"
done

echo "--- Move Report 01 working docs → docs/report_01/ ---"
run "mkdir -p '$REPO_ROOT/docs/report_01'"
for f in REPORT_PLAN.md STATUS_CHECKLIST.md QUICK_REFERENCE.md; do
    [ -f "$R01/$f" ] && run "git mv '$R01/$f' '$REPO_ROOT/docs/report_01/$f'"
done

echo "--- Remove empty tables dir ---"
run "rm -rf '$R01/tables'"

echo "--- Clean presentation .gitignore (no longer needed) ---"
run "rm -f '$R03/presentation/.gitignore'"
run "rm -f '$R03/report/.gitignore'"
run "rm -f '$R02/.gitignore'"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 6 — clean reports to publishable content only" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 7: Update .gitignore"
echo "=========================================="

if ! $DRY_RUN; then
cat > "$REPO_ROOT/.gitignore" << 'GITIGNORE_EOF'
# =============================================================================
# Build artifacts — NEVER commit these
# =============================================================================

# Quarto
_output/
.quarto/
*_files/

# LaTeX
*.aux
*.log
*.toc
*.tex
*.out
*.fls
*.fdb_latexmk
*.synctex.gz

# =============================================================================
# Python
# =============================================================================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
*.egg-info/
.installed.cfg
*.egg

# Jupyter
.ipynb_checkpoints/

# =============================================================================
# IDE / OS
# =============================================================================
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# =============================================================================
# Secrets
# =============================================================================
.env
*.key
config/api_keys.yaml

# =============================================================================
# Large files
# =============================================================================
models/roberta-large/
output/embeddings/*.npy
output/embeddings/*.pkl

# =============================================================================
# Archive (tracked but don't clutter)
# =============================================================================
archive/
handoffs/
cc_tasks/
GITIGNORE_EOF

    git add .gitignore && git commit -m "restructure: phase 7 — comprehensive .gitignore" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 8: Final cleanup"
echo "=========================================="

echo "--- Remove empty directories ---"
run "find '$REPO_ROOT/reports' -type d -empty -delete 2>/dev/null || true"
run "find '$REPO_ROOT/src' -type d -empty -delete 2>/dev/null || true"

echo "--- Remove src/__pycache__ ---"
run "find '$REPO_ROOT/src' -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 8 — final cleanup" || true
    echo ""
    echo "=========================================="
    echo "✅ MIGRATION COMPLETE"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Run: git log --oneline -10  (verify commits)"
    echo "  2. Run: git diff pre-restructure --stat  (see full changeset)"
    echo "  3. Test Quarto renders still work"
    echo "  4. Update CLAUDE.md with new paths"
    echo "  5. Push when satisfied"
    echo ""
    echo "To rollback: git reset --hard pre-restructure"
fi

echo ""
echo "Done."
