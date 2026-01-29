#!/bin/bash
# Refactor directory structure for multi-report organization
# Run from repo root: ./refactor_structure.sh
# 
# DRY RUN FIRST: Review the commands before executing
# To execute: chmod +x refactor_structure.sh && ./refactor_structure.sh

set -e  # Exit on error

echo "=== Directory Refactor: Federal Survey Concept Mapper ==="
echo ""

# Create new structure
echo "Creating reports/ structure..."
mkdir -p reports/01_llm_concept_mapping
mkdir -p reports/02_question_consolidation
mkdir -p reports/03_harmonization_constraints

# Create new output subdirectory
echo "Creating output/harmonization_constraints/..."
mkdir -p output/harmonization_constraints

# Move final_report -> reports/01_llm_concept_mapping
echo "Moving final_report/ -> reports/01_llm_concept_mapping/..."
mv final_report/* reports/01_llm_concept_mapping/
rmdir final_report

# Move future_study -> reports/02_question_consolidation
echo "Moving future_study/ -> reports/02_question_consolidation/..."
mv future_study/* reports/02_question_consolidation/
rmdir future_study

# Rename output subdirectories for clarity (optional - comment out if unwanted)
# echo "Renaming output subdirectories..."
# mv output/final output/concept_mapping_final

echo ""
echo "=== Refactor Complete ==="
echo ""
echo "New structure:"
echo "  reports/"
echo "    01_llm_concept_mapping/      (was final_report)"
echo "    02_question_consolidation/   (was future_study)"
echo "    03_harmonization_constraints/ (NEW)"
echo ""
echo "  output/"
echo "    harmonization_constraints/   (NEW)"
echo ""
echo "Next steps:"
echo "  1. Update any hardcoded paths in scripts"
echo "  2. Update CLAUDE.md if it references old paths"
echo "  3. git add -A && git commit -m 'Refactor: reorganize reports structure'"
