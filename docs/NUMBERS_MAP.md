# Federal Survey Harmonization Research — Master Numbers Map

**Purpose:** Single source of truth for every key number cited across reports and deliverables.  
**Scope:** 47 Census Bureau demographic surveys, ~7,000 questions. NOT cross-agency.  
**Last audited:** 2026-02-28 (ACS-side numbers corrected from 50→51 via q_id join methodology)  

---

## The Narrative Arc (with numbers)

### Step 1: Surveys and Questions

| Metric | Value | Source File | Notes |
|--------|-------|-------------|-------|
| Total surveys (instruments) | 47 | `data/raw/PublicSurveyQuestionsMap.csv` column headers minus "Question" and "Unnamed: 48" | One instrument was dropped during ingest |
| Total questions (raw) | 7,419 | `data/raw/PublicSurveyQuestions.csv` row count | Before deduplication |
| Total questions (deduplicated) | 6,987 | `data/raw/PublicSurveyQuestionsMap.csv` row count | After deduplication; this is the working dataset |
| Unique survey programs | ~30 | Manual count | Some programs have multiple questionnaire variants (e.g., NTPS × 6, FoodAPS × 4) |

**CANONICAL USAGE:** "~7,000 questions across 47 Census Bureau demographic survey instruments"

### Step 2: Topic/Subtopic Classification (Report 01)

| Metric | Value | Source File | Path/Field |
|--------|-------|-------------|------------|
| Questions classified | 6,954 | `output/report_01/final/master_dataset.csv` row count | Rows with valid classifications |
| Topic agreement (%) | 89.2% | `output/report_01/comparison/agreement_summary.csv` | `Topic Agreement %` = 89.24 |
| Subtopic agreement (%) | 69.7% | `output/report_01/comparison/agreement_summary.csv` | `Subtopic Agreement %` = 69.69 |
| Cohen's κ (topics) | 0.839 | `output/report_01/comparison/agreement_summary.csv` | `Cohen's Kappa (Topics)` = 0.8389 |
| Cohen's κ (subtopics) | 0.687 | `output/report_01/comparison/agreement_summary.csv` | `Cohen's Kappa (Subtopics)` = 0.6869 |
| Classification models | 2 | — | OpenAI GPT-5-mini, Anthropic Claude Haiku 4.5 |
| API cost (approx) | ~$15 | Manual estimate | For dual-model classification of all questions |
| Processing time | ~2 hours | Manual estimate | Wall clock for full pipeline |

**Topic distribution (consensus):**

| Topic | Count | % | Source |
|-------|------:|--:|--------|
| Economic | ~2,980 | 42.8% | `output/report_01/comparison/topic_distribution.csv` (avg of two models) |
| Social | ~2,467 | 35.5% | same |
| Housing | ~967 | 13.9% | same |
| Demographic | ~369 | 5.3% | same |
| Government | ~167 | 2.4% | same |

### Step 3: Concept Overlap Identification (Report 02)

ACS selected as anchor survey due to its breadth and prominence.

**"Family 2" surveys** — those with highest concept overlap with ACS:

| Survey | Total shared subtopics | Subtopics covered | Source |
|--------|----------------------:|-----------:|--------|
| SIPP | 577 | 38 | `output/report_02/data/acs_family2_summary.csv` |
| AHS | 460 | 34 | same |
| CE | 283 | 30 | same |
| CPS | 181 | 25 | same |
| FoodAPS | 123 | 23 | same |

**NOTE:** "Total shared" here counts question-subtopic intersections, not unique questions.

### Step 4: Question Pair Generation (Report 02 → Report 03 input)

Questions sharing the same subtopic classification between a source survey and ACS are paired for evaluation.

| Survey pair | Total pairs evaluated | Unique source questions | Raw survey questions | Source |
|-------------|---------------------:|------------------------:|---------------------:|--------|
| CPS–ACS | 1,030 | **157** | 211 | `docs/validation/question_counts.json`, validated from raw data |
| FoodAPS–ACS | 568 | **118** | 462 | same |
| **Total** | **1,598** | **275** | — | same |

**WHY UNIQUE < RAW:** Not all survey questions fall in subtopics where ACS also has questions. 54 CPS questions and 344 FoodAPS questions are in subtopics with no ACS coverage, so no pairs are possible and they are excluded.

**WHY THE PAIR COUNT IS LARGE:** Each source question is paired with every ACS question sharing its subtopic. Most pairs are unrelated — this is the naive combinatorial approach. The pair-level rates will be low; the question-level rates (Step 7) are the meaningful metric.

**⚠️ KNOWN INFLATION (corrected 2026-02-27):** `stage4_question_level.csv` assigns separate IDs per question-subtopic-pairing context. A question classified into multiple subtopics gets multiple IDs (worst case: one CPS disability question appears 25 times). The file contains 380 rows (240 CPS + 140 FoodAPS), but only 275 unique question texts (157 + 118). All counts in this document use the **deduplicated** values. See `docs/validation/number_flow.md` for complete trace.

### Step 5: Barrier Taxonomy (Report 03)

Six barrier categories applied to each pair:

| Code | Name | Description |
|------|------|-------------|
| CC | Construct/Concept | Questions measure fundamentally different things |
| TC | Temporal/Chronological | Reference period mismatch |
| RS | Response Scale | Different answer formats |
| PC | Population/Coverage | Different target populations |
| MC | Mode/Context | Different collection methods |
| PM | Precision/Measurement | Different levels of detail |

Plus feasibility codes: F1 (direct recode), F2 (statistical adjustment needed), F3 (not feasible).

### Step 6: Multi-Model Rating & Arbitration (Report 03)

**Stage 2 — Rater agreement (3 models independently rate all 1,598 pairs):**

| Metric | Value | Source File | Path |
|--------|-------|-------------|------|
| Rater models | 3 | — | OpenAI gpt-5-mini, Anthropic claude-haiku-4-5-20251001, Google gemini-3-flash-preview |
| Total pairs rated | 1,598 | `output/report_03/analysis/stage2_agreement_metrics.json` | `metadata.total_pairs` |
| CPS pairs | 1,030 | same | `L1_agreement.stratified.by_survey.CPS.n_pairs` |
| FoodAPS pairs | 568 | same | `L1_agreement.stratified.by_survey.FOODAPS.n_pairs` |
| L1 barrier agreement (Fleiss' κ) | 0.611 | same | `L1_agreement.overall.three_way.fleiss_kappa` |
| Feasibility agreement (Fleiss' κ) | 0.537 | same | `feasibility_agreement.overall.three_way.fleiss_kappa` |

**Stage 3 — Arbitration (independent models arbitrate disagreements):**

| Metric | Value | Source File | Path |
|--------|-------|-------------|------|
| Arbitrator models | 3 | — | Same models in arbitrator role |
| Two-way coverage | 1,598 pairs | `output/report_03/analysis/stage3_arbitration_metrics.json` | `metadata.two_way_n` |
| Three-way coverage | 751 pairs | same | `metadata.three_way_n` (Google: CPS only, rate-limited) |
| Post-arbitration κ (feasibility, 2-way) | **0.843** | same | `two_way_agreement.feasibility.cohens_kappa` |
| Post-arbitration κ (L1, 2-way) | 0.796 | same | `two_way_agreement.L1.cohens_kappa` |
| Post-arbitration κ (binary, 2-way) | **0.896** | same | `two_way_agreement.binary_consolidability.cohens_kappa` |
| Quality gate passed (feasibility) | ✅ Yes | same | `two_way_agreement.feasibility.quality_gate_passed` = true |
| Quality gate passed (binary) | ✅ Yes | same | `two_way_agreement.binary_consolidability.quality_gate_passed` = true |

**Key narrative point:** Rater-stage agreement was moderate (κ = 0.611); arbitration improved it to almost perfect (κ = 0.843). This validates the multi-model approach.

### Step 7: Question-Level Results (Report 03, Stage 4)

Collapsing from pair-level to question-level: a question is "consolidable" if it has **at least one** ACS pair rated F1 or F2. Counts are **deduplicated by unique question text** (corrected 2026-02-27; see `docs/validation/number_flow.md`).

| Survey | Unique Qs | Consolidable | Rate | F1 (direct) | F2 (stat. adjustment) | F3 (not feasible) | Source |
|--------|--------:|---:|---:|---:|---:|---:|--------|
| CPS | **157** | **86** | **54.8%** | **32** (20.4%) | **54** (34.4%) | **71** (45.2%) | `docs/validation/question_counts.json`, deduplicated from `stage4_question_level.csv` |
| FoodAPS | **118** | **56** | **47.5%** | **19** (16.1%) | **37** (31.4%) | **62** (52.5%) | same |

**Why the CPS rate is HIGHER after correction:** The inflated duplicates were disproportionately disability-related questions (up to 25 copies of the same text) that mostly scored F3. Removing duplicates removes more F3s than F1/F2s, raising the consolidation rate from the pre-correction 42.5% to 54.8%.

**Pair-level vs question-level rates (critical context):**

| Survey | Pair-level rate | Question-level rate | Why different |
|--------|:-:|:-:|---|
| CPS | 19.5% | 54.8% | Each question paired with many unrelated ACS questions |
| FoodAPS | 20.6% | 47.5% | Same — combinatorial pairing inflates denominator |

### Step 7b: ACS-Side Participation (NEW — added 2026-02-27)

ACS has 115 questions total, but how many actually serve as harmonization bridge targets?

| Metric | CPS | FoodAPS | Combined | Source |
|--------|----:|--------:|---------:|--------|
| Unique ACS targets (F1+F2 pairs) | 36 | 32 | **51** | `stage4_question_best_matches.csv` joined via q_id through `stage4_question_level.csv` (dedup by full question text, union all ACS targets per unique source question across subtopic contexts) |
| ACS questions serving BOTH surveys | — | — | **17** | same |
| ACS participation rate | — | — | **44.3%** (51/115) | same |
| Fan-in ratio (source Qs per ACS target) | — | — | **2.78** (142/51) | same |

**Methodology note (ACS-side counting):** `stage4_question_best_matches.csv` truncates source question text at ~100 characters. Two CPS questions that differ only after character 100 collide when matched by text alone. The correct method joins through `survey_q_id` via `stage4_question_level.csv` (which has full texts), then unions all F1/F2 ACS targets for each unique source question across all its subtopic contexts. Set arithmetic: 36 + 32 − 17 = 51. ✅

**Key findings:**
- 51 of 115 ACS questions (44.3%) serve as F1/F2 bridge targets for at least one source survey.
- 17 ACS questions serve BOTH CPS and FoodAPS — these are three-way bridge variables and the highest-value harmonization targets (e.g., employment status, hours worked, race, age, marital status, military service, household relationship).
- Fan-in of 2.78 means each ACS bridge question connects to nearly 3 source survey questions on average.
- Zero literal question sharing exists between ACS, CPS, and FoodAPS — all harmonization is concept-level.

### Step 8: Barrier Distribution (Report 03)

Among pairs rated not consolidable (F3), why not?

| Survey | CC (Construct) | TC (Temporal) | RS (Response) | PC (Population) | MC (Mode) | PM (Precision) | Source |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|--------|
| CPS | 85.1% | 7.9% | 4.1% | 0.7% | 1.0% | 0.2% | `output/report_03/analysis/barrier_summary_by_survey.csv` |
| FoodAPS | 88.9% | 5.5% | 3.3% | 0.9% | 0.7% | 0.2% | same |

**Key finding:** Construct/concept mismatch dominates (~86-89%). This is expected — most question pairs don't match because they ask about different things, not because of fixable methodological differences. The interesting cases are the 11-15% that fail for potentially addressable reasons (temporal, response format, population coverage).

### Step 9: Expert Review & Report 04 (TBD)

Not yet completed. This is where the harmonization candidates go to subject-matter experts for validation. Report 04 scope also includes multi-hop enrichment discovery across the full 47-survey topology.

---

## Numbers That Don't Exist Yet (Gaps)

| What's missing | Why it matters | How to get it |
|----------------|---------------|---------------|
| Questions per survey (all 47) | Foundational count for the full story | Count from `PublicSurveyQuestionsMap.csv` by column |
| Total shared concepts across all 47 surveys | Shows the harmonization landscape | Compute from `master_dataset.csv` |
| Cross-survey concept overlap matrix (all 47) | The full topology picture | Report 04 scope |
| Subtopic-level breakdown of corrected counts | Ch 5/6 tables need recalculation | Dedup `stage4_question_level.csv` by question text per subtopic |

---

## Common Errors to Avoid

| Error | Correct | Where it keeps appearing |
|-------|---------|------------------------|
| "48 surveys" | **47 surveys** | README, older reports — one was dropped |
| "federal surveys" (implying cross-agency) | **Census Bureau demographic surveys** | README title, fact sheet |
| "7,400 questions" or "7,000 questions" | **~7,000 questions** (6,987 deduplicated) | Various |
| Citing pair-level rates as consolidation rates | Must specify **question-level** rates | Report 03 findings |
| κ = 0.843 without context | That's **post-arbitration feasibility** (2-way); rater-stage was 0.611 | Reports conflating stages |
| "240 CPS questions" or "140 FoodAPS questions" | **157 CPS** / **118 FoodAPS** unique questions | Pre-correction inflation from `stage4_question_level.csv` counting question-subtopic assignments as unique questions |
| "380 unique source questions" | **275 unique source questions** (157 + 118) | Same inflation bug |
| "42.5% CPS consolidation rate" | **54.8%** (corrected) | Pre-correction inflated F3 duplicates dragged rate down |
| Missing ACS-side analysis | **51 of 115 ACS questions** serve as bridge targets (44.3%) | Was not reported before 2026-02-27; corrected from 50 to 51 on 2026-02-28 via q_id join methodology |

---

## Methodology Summary (Plain Language)

1. Two LLMs independently classified every question by Census topic and subtopic. They agreed 89% of the time (κ = 0.84).
2. Questions sharing the same subtopic across surveys were paired. For CPS and FoodAPS vs ACS, this produced 1,598 pairs.
3. Three LLMs independently evaluated each pair: can this pair be harmonized? What's the barrier if not?
4. Where models disagreed, three independent arbitrators broke the tie. Agreement improved from κ = 0.61 to κ = 0.84.
5. Results collapsed from pairs to individual questions: **47-55% of source questions** have at least one harmonization path to ACS.
6. On the ACS side, 50 of 115 questions (43.5%) serve as bridge targets, with 17 serving both CPS and FoodAPS simultaneously.
7. For the ~45-53% that can't harmonize, the dominant reason (~87%) is that the questions measure fundamentally different things.
