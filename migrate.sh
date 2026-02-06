#!/bin/bash
# =============================================================================
# REPO RESTRUCTURE MIGRATION SCRIPT v3
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

# Run a shell command (for rm, mkdir, ln, find, etc.)
run() {
    if $DRY_RUN; then
        echo "  [DRY] $*"
    else
        echo "  [RUN] $*"
        eval "$@"
    fi
}

# Move a file: git mv if tracked, plain mv if not
safe_mv() {
    local src="$1" dst="$2"
    if $DRY_RUN; then
        echo "  [DRY] move '$src' → '$dst'"
    else
        if git ls-files --error-unmatch "$src" &>/dev/null 2>&1; then
            echo "  [RUN] git mv '$src' → '$dst'"
            git mv "$src" "$dst"
        else
            echo "  [RUN] mv '$src' → '$dst'  (untracked)"
            mv "$src" "$dst"
        fi
    fi
}

# Move a directory: git mv if has tracked files, plain mv otherwise
safe_mv_dir() {
    local src="$1" dst="$2"
    if $DRY_RUN; then
        echo "  [DRY] move dir '$src' → '$dst'"
    else
        if git ls-files "$src" 2>/dev/null | head -1 | grep -q .; then
            echo "  [RUN] git mv '$src' → '$dst'"
            git mv "$src" "$dst"
        else
            echo "  [RUN] mv '$src' → '$dst'  (untracked dir)"
            mv "$src" "$dst"
        fi
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

echo "--- Presentation tracking/summary docs (superseded) ---"
for f in BACKUP_SLIDES_SUMMARY.md CHANGES_COMPLETE.md HARMONIZATION_DISTRIBUTION_SUMMARY.md \
         IMAGE_UPDATE_SUMMARY.md MERMAID_TO_PNG_SUMMARY.md PIPELINE_INTEGRATION_SUMMARY.md \
         QUESTION_CONSOLIDATION_DISTRIBUTION_SUMMARY.md RESPONDENT_BURDEN_RESTORATION.md \
         SCAFFOLD_VERIFICATION.md THREE_LAYER_VALUE_VERIFICATION.md \
         VALUE_PROPOSITION_UPDATES_SUMMARY.md QUICK_START.md README.md; do
    run "rm -f '$R03/presentation/$f'"
done

echo "--- Pycache everywhere ---"
run "find '$REPO_ROOT' -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"

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

for d in \
    "$REPO_ROOT/src/core" \
    "$REPO_ROOT/src/report_02" \
    "$REPO_ROOT/src/report_03/pipelines" \
    "$REPO_ROOT/src/report_03/scripts/lib" \
    "$REPO_ROOT/src/notebooks" \
    "$REPO_ROOT/output/report_01" \
    "$REPO_ROOT/output/report_02/data" \
    "$REPO_ROOT/output/report_02/figures" \
    "$REPO_ROOT/output/report_03/pdf" \
    "$REPO_ROOT/output/archive" \
    "$REPO_ROOT/docs/project" \
    "$REPO_ROOT/docs/report_01" \
    "$REPO_ROOT/docs/report_02" \
    "$REPO_ROOT/docs/report_03/literature" \
    "$REPO_ROOT/data/processed"; do
    run "mkdir -p '$d'"
done

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 3: Move code → src/"
echo "=========================================="

echo "--- Original src/ scripts → src/core/ ---"
for f in "$REPO_ROOT/src/"*.py; do
    [ -f "$f" ] || continue
    safe_mv "$f" "$REPO_ROOT/src/core/$(basename "$f")"
done

echo "--- Notebooks → src/notebooks/ ---"
if [ -d "$REPO_ROOT/notebooks" ]; then
    for f in "$REPO_ROOT/notebooks/"*.ipynb; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/src/notebooks/$(basename "$f")"
    done
    run "rm -rf '$REPO_ROOT/notebooks'"
fi

echo "--- Report 03 pipeline scripts → src/report_03/pipelines/ ---"
for f in 01_barrier_pipeline.py 02_arbitration_pipeline.py 03_analysis_pipeline.py \
         03_stage2_agreement.py 03b_stage2_extended.py 04_findings_pipeline.py \
         05_deliverables_pipeline.py run_pipeline.py run_full_pipeline.py; do
    [ -f "$R03/$f" ] || continue
    safe_mv "$R03/$f" "$REPO_ROOT/src/report_03/pipelines/$f"
done

echo "--- Report 03 analysis scripts → src/report_03/scripts/ ---"
if [ -d "$R03/scripts" ]; then
    # Move lib contents first (before parent gets emptied)
    if [ -d "$R03/scripts/lib" ]; then
        echo "--- Report 03 scripts/lib → src/report_03/scripts/lib/ ---"
        for f in "$R03/scripts/lib/"*; do
            [ -f "$f" ] || continue
            safe_mv "$f" "$REPO_ROOT/src/report_03/scripts/lib/$(basename "$f")"
        done
        run "rm -rf '$R03/scripts/lib'"
    fi
    # Now move scripts
    for f in "$R03/scripts/"*.py; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/src/report_03/scripts/$(basename "$f")"
    done
    run "rm -rf '$R03/scripts'"
fi

echo "--- Report 03 CLAUDE.md → src/report_03/ ---"
[ -f "$R03/CLAUDE.md" ] && safe_mv "$R03/CLAUDE.md" "$REPO_ROOT/src/report_03/CLAUDE.md"

echo "--- Report 02 build scripts → src/report_02/ ---"
[ -f "$R02/build_report.py" ] && safe_mv "$R02/build_report.py" "$REPO_ROOT/src/report_02/build_report.py"
if [ -d "$R02/scripts" ]; then
    for f in "$R02/scripts/"*.py "$R02/scripts/"*.json "$R02/scripts/"*.css; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/src/report_02/$(basename "$f")"
    done
    run "rm -rf '$R02/scripts'"
fi

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 3 — move all code to src/" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 4: Move output/data → output/"
echo "=========================================="

echo "--- Report 03 output/ → output/report_03/ ---"
if [ -d "$R03/output" ]; then
    for d in analysis checkpoints results visuals; do
        [ -d "$R03/output/$d" ] || continue
        safe_mv_dir "$R03/output/$d" "$REPO_ROOT/output/report_03/$d"
    done
    # Loose files
    for f in "$R03/output/"*; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/output/report_03/$(basename "$f")"
    done
    run "rm -rf '$R03/output'"
fi

echo "--- Report 03 archive → output/archive/ ---"
[ -d "$R03/output_archive_gpt4omini_error" ] && \
    safe_mv_dir "$R03/output_archive_gpt4omini_error" "$REPO_ROOT/output/archive/gpt4omini_error"

echo "--- Report 03 data → data/processed/ ---"
if [ -d "$R03/data" ]; then
    for f in "$R03/data/"*; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/data/processed/$(basename "$f")"
    done
    run "rm -rf '$R03/data'"
fi

echo "--- Report 02 data → output/report_02/data/ ---"
if [ -d "$R02/data" ]; then
    for f in "$R02/data/"*; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/output/report_02/data/$(basename "$f")"
    done
    run "rm -rf '$R02/data'"
fi

echo "--- Report 01 data → output/report_01/ ---"
if [ -d "$R01/data" ]; then
    for f in "$R01/data/"*; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/output/report_01/$(basename "$f")"
    done
    run "rm -rf '$R01/data'"
fi

echo "--- Report 01 figures → output/report_01/ ---"
if [ -d "$R01/figures" ]; then
    for f in "$R01/figures/"*; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/output/report_01/$(basename "$f")"
    done
    run "rm -rf '$R01/figures'"
fi

echo "--- Report 01 FULL_REPORT → output/report_01/ ---"
[ -f "$R01/FULL_REPORT.md" ] && safe_mv "$R01/FULL_REPORT.md" "$REPO_ROOT/output/report_01/FULL_REPORT.md"

echo "--- Report 02 figures → output/report_02/figures/ ---"
if [ -d "$R02/figures" ]; then
    for f in "$R02/figures/"*; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/output/report_02/figures/$(basename "$f")"
    done
    run "rm -rf '$R02/figures'"
fi

echo "--- Report 03 report figures (duplicates) → remove ---"
run "rm -rf '$R03/report/figures'"

echo "--- Report 03 presentation images (duplicates) → remove ---"
run "rm -rf '$R03/presentation/images'"

echo "--- Report 03 presentation PDFs → output/report_03/pdf/ ---"
for f in "$R03/presentation/"*.pdf; do
    [ -f "$f" ] || continue
    safe_mv "$f" "$REPO_ROOT/output/report_03/pdf/$(basename "$f")"
done

echo "--- Report 02 FULL_REPORT files → output/report_02/ ---"
[ -f "$R02/FULL_REPORT.md" ] && safe_mv "$R02/FULL_REPORT.md" "$REPO_ROOT/output/report_02/FULL_REPORT.md"
[ -f "$R02/FULL_REPORT.pdf" ] && safe_mv "$R02/FULL_REPORT.pdf" "$REPO_ROOT/output/report_02/FULL_REPORT.pdf"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 4 — consolidate output and data" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 5: Move docs"
echo "=========================================="

echo "--- Report 03 docs → docs/report_03/ ---"
if [ -d "$R03/docs" ]; then
    if [ -d "$R03/docs/literature" ]; then
        for f in "$R03/docs/literature/"*; do
            [ -f "$f" ] || continue
            safe_mv "$f" "$REPO_ROOT/docs/report_03/literature/$(basename "$f")"
        done
    fi
    for f in "$R03/docs/"*.md; do
        [ -f "$f" ] || continue
        safe_mv "$f" "$REPO_ROOT/docs/report_03/$(basename "$f")"
    done
    run "rm -rf '$R03/docs'"
fi

echo "--- Top-level docs → docs/project/ ---"
for f in "$REPO_ROOT/docs/"*.md; do
    [ -f "$f" ] || continue
    safe_mv "$f" "$REPO_ROOT/docs/project/$(basename "$f")"
done

echo "--- Report 03 config → config/ ---"
[ -f "$R03/config.yaml" ] && safe_mv "$R03/config.yaml" "$REPO_ROOT/config/report_03.yaml"

echo "--- Report 03 README → docs/report_03/ ---"
[ -f "$R03/README.md" ] && safe_mv "$R03/README.md" "$REPO_ROOT/docs/report_03/README.md"

if ! $DRY_RUN; then
    git add -A && git commit -m "restructure: phase 5 — organize documentation" || true
fi

# =============================================================================
echo ""
echo "=========================================="
echo "PHASE 6: Clean reports/ to publishable only"
echo "=========================================="

echo "--- Create figure symlinks ---"
run "ln -sf '../../../output/report_03/visuals' '$R03/report/figures'"
run "ln -sf '../../../output/report_03/visuals' '$R03/presentation/images'"
[ -d "$R02" ] && run "ln -sf '../../output/report_02/figures' '$R02/figures'"

echo "--- Move Report 02 working docs → docs/report_02/ ---"
for f in acs_linked_supplements_background.md case_studies_cps.md case_studies_foodaps.md \
         methodology_classification_workflow.md question_level_matching_design.md \
         synthesis_and_conclusions.md; do
    [ -f "$R02/$f" ] && safe_mv "$R02/$f" "$REPO_ROOT/docs/report_02/$f"
done

echo "--- Move Report 01 working docs → docs/report_01/ ---"
for f in REPORT_PLAN.md STATUS_CHECKLIST.md QUICK_REFERENCE.md; do
    [ -f "$R01/$f" ] && safe_mv "$R01/$f" "$REPO_ROOT/docs/report_01/$f"
done

echo "--- Remove empty tables dir ---"
run "rm -rf '$R01/tables'"

echo "--- Clean stale .gitignore files ---"
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
# Archive / scratch (tracked but don't clutter)
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

echo "--- Remove pycache everywhere ---"
run "find '$REPO_ROOT' -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"

echo "--- Remove migration artifacts ---"
run "rm -f '$REPO_ROOT/migrate.sh'"
run "rm -f '$REPO_ROOT/MIGRATION_PLAN.md'"

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
