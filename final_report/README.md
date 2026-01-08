# Federal Survey Concept Mapping - Report Assets

This directory contains all assets for the scientific report.

## Directory Structure

```
/final_report/
├── REPORT_PLAN.md           # Master writing plan
├── sections/                # 14 markdown sections (to be written)
├── figures/                 # Visualizations for report
├── tables/                  # Summary tables  
└── data/                    # Master datasets
```

## Assets Inventory

### Figures (figures/)
**Ready**:
- ❌ `figure_01_methodology_flow.png` - Pipeline diagram (needs creation)
- ❌ `figure_02_model_agreement.png` - Agreement visualization (needs creation)
- ⏳ `figure_03_beeswarm_distribution.png` - Coverage distribution (run generate_coverage_analysis.py)
- ⏳ `figure_04_horizontal_bars_topics.png` - Subtopic coverage by topic (run generate_coverage_analysis.py)
- ⏳ `figure_05_clustered_heatmap.png` - Survey similarity (run generate_visualizations_1_2_3.py)
- ⏳ `figure_06_unique_orphan_tables.png` - Coverage gaps (run generate_coverage_analysis.py)

### Tables (tables/)
**Ready**:
- ✅ `table_01_survey_summary.csv` - Survey statistics
- ✅ `table_02_agreement_stats.csv` - Model agreement metrics
- ⏳ `table_03_survey_profiles.csv` - Survey profiles (run generate_survey_tables.py)
- ⏳ `table_04_consolidation_candidates.csv` - High-overlap pairs (run generate_survey_tables.py)
- ⏳ `table_05_coverage_gaps.csv` - Orphan/unique concepts (run generate_coverage_analysis.py)
- ⏳ `table_06_similarity_matrix.csv` - Pairwise similarity (run generate_survey_tables.py)

### Data (data/)
**Ready**:
- ✅ `master_dataset.csv` - Complete categorizations (6,987 questions)
- ✅ `survey_concept_matrix.csv` - Survey × concept counts

## Generate Missing Assets

### Step 1: Generate Coverage Analysis
```bash
cd src
python generate_coverage_analysis.py
```
**Produces**:
- figure_03_beeswarm_distribution.png
- figure_04_horizontal_bars_topics.png
- figure_06_unique_orphan_tables.png
- table_05_coverage_gaps.csv

### Step 2: Generate Survey Tables
```bash
cd src
python generate_survey_tables.py
```
**Produces**:
- table_03_survey_profiles.csv
- table_04_consolidation_candidates.csv
- table_06_similarity_matrix.csv

### Step 3: Generate Initial Visualizations
```bash
cd src
python generate_visualizations_1_2_3.py
```
**Produces**:
- figure_05_clustered_heatmap.png
- Coverage treemap (HTML, not used in report)
- Sankey diagram (HTML, not used in report)

### Step 4: Create Pipeline Diagrams (Manual)
- Extract diagrams from `docs/pipeline_documentation.md`
- Or create simplified versions in diagrams.net / PowerPoint
- Save as:
  - `figure_01_methodology_flow.png`
  - `figure_02_model_agreement.png`

## Copy Assets to Report

After generating, copy to report directory:

```bash
# From output/visualizations to report/figures
cp ../output/visualizations/beeswarm_coverage_distribution.png figures/figure_03_beeswarm_distribution.png
cp ../output/visualizations/horizontal_bars_all_subtopics.png figures/figure_04_horizontal_bars_topics.png
cp ../output/visualizations/2_clustered_heatmap.png figures/figure_05_clustered_heatmap.png
cp ../output/visualizations/unique_orphan_tables.png figures/figure_06_unique_orphan_tables.png

# From output/visualizations to report/tables
cp ../output/visualizations/survey_profiles.csv tables/table_03_survey_profiles.csv
cp ../output/visualizations/consolidation_candidates.csv tables/table_04_consolidation_candidates.csv
cp ../output/visualizations/unique_and_orphan_concepts.csv tables/table_05_coverage_gaps.csv
cp ../output/visualizations/survey_similarity_matrix.csv tables/table_06_similarity_matrix.csv
```

## Report Status

**Current State**: Directory structure complete, 2 tables ready, data files in place

**Next Steps**:
1. Generate remaining visualizations (Steps 1-3 above)
2. Create methodology diagrams (Step 4)
3. Begin drafting sections (start with Section 4 - Methodology)

## Writing Sections

Sections should be written in order of the writing strategy:

**Phase 1** (Core Content):
1. Section 04 - Methodology
2. Section 05 - Data Collection
3. Section 06 - Categorization Approach
4. Section 07 - Results
5. Section 08 - Coverage Analysis
6. Section 09 - Consolidation Opportunities

**Phase 2** (Framing):
7. Section 02 - Introduction
8. Section 03 - Background
9. Section 10 - Discussion
10. Section 11 - Limitations
11. Section 12 - Recommendations

**Phase 3** (Bookends):
12. Section 01 - Abstract (write last)
13. Section 13 - Conclusion
14. Section 14 - Appendices

See REPORT_PLAN.md for detailed content guidance for each section.
