#!/usr/bin/env bash
# migrate.sh v3 — Federal Survey Concept Mapper repo restructure
# Usage: ./migrate.sh          (dry run, prints what would happen)
#        ./migrate.sh --execute (actually does it)
#
# Safety: pre-restructure tag must exist. Each phase commits separately.
# Rollback: git reset --hard pre-restructure

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

DRY_RUN=true
[[ "${1:-}" == "--execute" ]] && DRY_RUN=false

log()  { echo "[migrate] $*"; }
warn() { echo "[migrate] ⚠️  $*" >&2; }
die()  { echo "[migrate] ❌ $*" >&2; exit 1; }

# ── Preflight ────────────────────────────────────────────────────────────────
git rev-parse --verify pre-restructure >/dev/null 2>&1 \
  || die "Tag 'pre-restructure' not found. Create it first: git tag pre-restructure"

[[ -z "$(git status --porcelain)" ]] \
  || die "Working tree dirty. Commit or stash first."

if $DRY_RUN; then
  log "🔍 DRY RUN — no changes will be made. Use --execute to apply."
fi

# ── Helpers ──────────────────────────────────────────────────────────────────
safe_mv() {
  local src="$1" dest="$2"
  if $DRY_RUN; then
    echo "  MOVE: $src → $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  if git ls-files --error-unmatch "$src" >/dev/null 2>&1; then
    git mv "$src" "$dest"
  else
    mv "$src" "$dest"
  fi
}

safe_rm() {
  local target="$1"
  if $DRY_RUN; then
    echo "  DELETE: $target"
    return
  fi
  if git ls-files --error-unmatch "$target" >/dev/null 2>&1; then
    git rm -rf "$target"
  else
    rm -rf "$target"
  fi
}

safe_mkdir() {
  local dir="$1"
  if $DRY_RUN; then
    echo "  MKDIR: $dir"
    return
  fi
  mkdir -p "$dir"
}

phase_commit() {
  local msg="$1"
  if $DRY_RUN; then
    log "  COMMIT: $msg"
    return
  fi
  git add -A
  git commit -m "$msg" || log "Nothing to commit for: $msg"
}

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: Remove duplicate " 2" files (macOS copy artifacts)
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 1: Remove duplicate ' 2' files ═══"

# Find all " 2" files/dirs across the repo
while IFS= read -r -d '' dup; do
  safe_rm "$dup"
done < <(find "$REPO_ROOT" -name "* 2*" -not -path "*/.git/*" -print0 2>/dev/null)

# Also clean up any " 3" through " 10" copies (RevealJS libs etc)
for i in $(seq 3 10); do
  while IFS= read -r -d '' dup; do
    safe_rm "$dup"
  done < <(find "$REPO_ROOT" -name "* ${i}*" -not -path "*/.git/*" -print0 2>/dev/null)
done

phase_commit "chore: remove duplicate ' 2..10' files (macOS copy artifacts)"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: Remove committed build artifacts
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 2: Remove build artifacts ═══"

# Quarto _output directories
while IFS= read -r -d '' outdir; do
  safe_rm "$outdir"
done < <(find "$REPO_ROOT" -type d -name "_output" -not -path "*/.git/*" -print0 2>/dev/null)

# .quarto directories
while IFS= read -r -d '' qdir; do
  safe_rm "$qdir"
done < <(find "$REPO_ROOT" -type d -name ".quarto" -not -path "*/.git/*" -print0 2>/dev/null)

# LaTeX artifacts
while IFS= read -r -d '' texfile; do
  safe_rm "$texfile"
done < <(find "$REPO_ROOT" \( -name "*.aux" -o -name "*.log" -o -name "*.toc" \
  -o -name "*.tex" -o -name "*.out" -o -name "*.fls" \
  -o -name "*.fdb_latexmk" -o -name "*.synctex.gz" \) \
  -not -path "*/.git/*" -print0 2>/dev/null)

# __pycache__
while IFS= read -r -d '' cache; do
  safe_rm "$cache"
done < <(find "$REPO_ROOT" -type d -name "__pycache__" -not -path "*/.git/*" -print0 2>/dev/null)

# .bak files
while IFS= read -r -d '' bak; do
  safe_rm "$bak"
done < <(find "$REPO_ROOT" -name "*.bak" -not -path "*/.git/*" -print0 2>/dev/null)

phase_commit "chore: remove build artifacts (Quarto _output, LaTeX, __pycache__, .bak)"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: Consolidate source code under src/
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 3: Consolidate source code ═══"

# Target layout:
#   src/pipelines/     — report_03 pipelines (the main pipeline code)
#   src/scripts/       — report_03 one-off scripts
#   src/lib/           — shared utilities (from scripts/lib/)
#   src/core/          — report 01/02 era scripts (keep as-is)
#   src/notebooks/     — already fine
#   src/report_02/     — report 02 build scripts (keep as-is)

# Move report_03 pipelines → src/pipelines/
safe_mkdir "src/pipelines"
if [ -d "src/report_03/pipelines" ]; then
  for f in src/report_03/pipelines/*.py; do
    [ -f "$f" ] || continue
    fname="$(basename "$f")"
    safe_mv "$f" "src/pipelines/$fname"
  done
fi

# Move report_03 scripts → src/scripts/
safe_mkdir "src/scripts"
if [ -d "src/report_03/scripts" ]; then
  for f in src/report_03/scripts/*.py; do
    [ -f "$f" ] || continue
    fname="$(basename "$f")"
    safe_mv "$f" "src/scripts/$fname"
  done
fi

# Move lib/ up to src/lib/
safe_mkdir "src/lib"
if [ -d "src/report_03/scripts/lib" ]; then
  for f in src/report_03/scripts/lib/*; do
    [ -f "$f" ] || continue
    fname="$(basename "$f")"
    safe_mv "$f" "src/lib/$fname"
  done
fi

# Move CLAUDE.md from src/report_03/ to docs/ if it exists
if [ -f "src/report_03/CLAUDE.md" ]; then
  safe_mv "src/report_03/CLAUDE.md" "docs/report_03_CLAUDE.md"
fi

# Clean up empty src/report_03/ tree
if ! $DRY_RUN; then
  find src/report_03 -type d -empty -delete 2>/dev/null || true
fi

phase_commit "refactor: consolidate source code (pipelines, scripts, lib under src/)"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: Consolidate output artifacts
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 4: Consolidate output artifacts ═══"

# Move stale archive inside output/ to top-level archive/
if [ -d "output/archive" ]; then
  safe_mkdir "archive/output_archive"
  for item in output/archive/*; do
    [ -e "$item" ] || continue
    bname="$(basename "$item")"
    safe_mv "$item" "archive/output_archive/$bname"
  done
  if ! $DRY_RUN; then
    rmdir output/archive 2>/dev/null || true
  fi
fi

# Move early report artifacts into output/report_01/
for item in output/analysis output/comparison output/results \
            output/visualizations output/final output/arbitration_final; do
  if [ -d "$item" ]; then
    bname="$(basename "$item")"
    safe_mv "$item" "output/report_01/$bname"
  fi
done

# output/question_matching → output/report_02/question_matching
if [ -d "output/question_matching" ]; then
  safe_mv "output/question_matching" "output/report_02/question_matching"
fi

# Remove empty harmonization_constraints placeholder if empty
if [ -d "output/harmonization_constraints" ]; then
  if ! $DRY_RUN; then
    rmdir output/harmonization_constraints 2>/dev/null || true
  fi
fi

phase_commit "refactor: consolidate output artifacts under report-specific directories"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: Clean up reports/ (publishable content only)
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 5: Clean up reports/ ═══"

# If images/figures are files (not dirs), remove them — they're placeholders
for maybe_broken in "reports/03_harmonization_constraints/presentation/images" \
                     "reports/03_harmonization_constraints/report/figures"; do
  if [ -e "$maybe_broken" ] && [ ! -d "$maybe_broken" ]; then
    safe_rm "$maybe_broken"
  fi
done

# Create proper symlinks for figures → output visuals
if ! $DRY_RUN; then
  if [ -d "output/report_03/visuals" ]; then
    ln -sfn "../../../output/report_03/visuals" \
      "reports/03_harmonization_constraints/presentation/images"
    ln -sfn "../../../output/report_03/visuals" \
      "reports/03_harmonization_constraints/report/figures"
  fi
fi

phase_commit "refactor: clean reports/ dir, add figure symlinks to output/"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: Create report_04 skeleton
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 6: Create report_04 skeleton ═══"

safe_mkdir "reports/04_empirical_validation/sections"
safe_mkdir "output/report_04/analysis"
safe_mkdir "output/report_04/data"
safe_mkdir "output/report_04/figures"

if ! $DRY_RUN; then
  cat > reports/04_empirical_validation/README.md << 'EOF'
# Report 04: Empirical Validation of AI Consolidation Judgments

Validates AI classifications using public microdata from CPS and ACS (IPUMS).
Tests whether "consolidable" question pairs show statistically comparable
response distributions while "non-consolidable" pairs diverge.

## Data Sources
- IPUMS-CPS (2021-2023)
- IPUMS-USA / ACS (2021-2023)

## Key Variables
- Earnings: hourly wages, weekly earnings, overtime/tips/commissions
EOF
fi

phase_commit "chore: create report_04 skeleton directories"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: Update .gitignore
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 7: Update .gitignore ═══"

if ! $DRY_RUN; then
  cat > .gitignore << 'GITIGNORE'
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
# Large files / models
# =============================================================================
models/roberta-large/
output/embeddings/*.npy
output/embeddings/*.pkl

# =============================================================================
# macOS duplicate artifacts (never commit)
# =============================================================================
*\ 2*
*\ 3*
*\ 4*
*\ 5*
*\ 6*
*\ 7*
*\ 8*
*\ 9*
*\ 10*

# =============================================================================
# Archive / scratch
# =============================================================================
archive/
handoffs/
cc_tasks/

# =============================================================================
# Backup files
# =============================================================================
*.bak
*.orig
GITIGNORE
fi

phase_commit "chore: update .gitignore with duplicate and build artifact patterns"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: Update CLAUDE.md with new paths
# ═══════════════════════════════════════════════════════════════════════════════
log "═══ Phase 8: Update CLAUDE.md ═══"

if ! $DRY_RUN; then
  cat > CLAUDE.md << 'CLAUDEMD'
# Federal Survey Concept Mapper — Project Guide

## Repository Layout (post-restructure)

```
├── data/
│   ├── raw/                    # Input data (untouched)
│   ├── processed/              # Pipeline outputs (CSV, JSONL)
│   └── reference/              # Lookup tables, taxonomies
├── src/
│   ├── core/                   # Report 01/02 era scripts
│   ├── pipelines/              # Report 03+ pipeline stages (01-05)
│   ├── scripts/                # One-off analysis scripts
│   ├── lib/                    # Shared utilities (io_utils, stats, taxonomy)
│   ├── notebooks/              # Jupyter exploration notebooks
│   └── report_02/              # Report 02 build scripts
├── output/
│   ├── report_01/              # Report 01 analysis artifacts
│   ├── report_02/              # Report 02 analysis artifacts
│   ├── report_03/              # Report 03 analysis artifacts
│   │   ├── analysis/           # JSON, CSV analysis files
│   │   ├── checkpoints/        # API call checkpoints
│   │   ├── results/            # Raw API results
│   │   ├── visuals/            # Generated figures
│   │   └── pdf/                # Rendered slide PDFs
│   └── report_04/              # Report 04 (empirical validation)
├── reports/                    # ONLY publishable Quarto content
│   ├── 01_llm_concept_mapping/
│   ├── 02_question_consolidation/
│   ├── 03_harmonization_constraints/
│   │   ├── report/             # Quarto report
│   │   └── presentation/       # Quarto slides
│   └── 04_empirical_validation/
├── docs/                       # Project-level docs, methodology logs
├── config/                     # Configuration files
└── archive/                    # Old/superseded artifacts
```

## Key Principles
- **Source vs Generated**: `src/` has code, `output/` has generated artifacts
- **One canonical location**: Each file type lives in exactly one place
- **reports/ = publishable only**: No pipeline code, data, or scripts
- **Figures via symlinks**: reports/ reference output/ figures via relative symlinks

## Pipeline Stages (Report 03)
1. `src/pipelines/01_barrier_pipeline.py` — Barrier classification (3 LLM raters)
2. `src/pipelines/02_arbitration_pipeline.py` — Disagreement arbitration (3 LLM arbitrators)
3. `src/pipelines/03_analysis_pipeline.py` — Agreement analysis & metrics
4. `src/pipelines/04_findings_pipeline.py` — Question-level findings & rollup
5. `src/pipelines/05_deliverables_pipeline.py` — Report generation

## Shared Library
- `src/lib/io_utils.py` — File I/O helpers
- `src/lib/stats.py` — Statistical functions (kappa, agreement)
- `src/lib/taxonomy.py` — Barrier taxonomy definitions

## Import Convention
After restructure, imports use:
```python
from src.lib.stats import compute_kappa
from src.lib.io_utils import load_jsonl
```

## Rollback
```bash
git reset --hard pre-restructure
```
CLAUDEMD
fi

phase_commit "docs: update CLAUDE.md with post-restructure layout"

# ═══════════════════════════════════════════════════════════════════════════════
# Done
# ═══════════════════════════════════════════════════════════════════════════════
if $DRY_RUN; then
  log "✅ Dry run complete. Review above, then run: ./migrate.sh --execute"
else
  log "✅ Migration complete! 8 phases committed separately."
  log "   Rollback: git reset --hard pre-restructure"
  log ""
  log "   Post-migration TODO:"
  log "   1. Fix Python imports (scripts.lib.* → src.lib.*)"
  log "   2. Test Quarto renders with symlinked figures"
  log "   3. Verify presentation builds"
  log "   4. Run: git diff pre-restructure --stat"
fi
