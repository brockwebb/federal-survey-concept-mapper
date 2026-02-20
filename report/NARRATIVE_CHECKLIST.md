# Master Report — Narrative Checklist

**Purpose:** At-a-glance V&V for the master report. Each section lists the claim, the numbers that support it, and their source. If a number in the report doesn't appear here, it shouldn't be in the report. If a number here doesn't match the report, something is wrong.

**Canonical reference:** `docs/NUMBERS_MAP.md` has full provenance. This doc is the quick-check version.

---

## Ch 1: Introduction — The Landscape

| Claim | Number | Source |
|-------|--------|--------|
| Census Bureau fields many demographic surveys | 47 instruments | `PublicSurveyQuestionsMap.csv` column count minus 2 |
| Thousands of questions across them | ~7,000 (6,987 deduped) | `PublicSurveyQuestionsMap.csv` row count |
| ~30 distinct survey programs | ~30 | Manual count (some programs have multiple questionnaires) |
| AI did this in weeks, not months | API cost ~$100 | Cumulative across all stages |

**Narrative goal:** Establish scope and motivation. In-source before out-source.

---

## Ch 2: Classification — Mapping the Terrain

| Claim | Number | Source |
|-------|--------|--------|
| Dual-model classification | 2 models | OpenAI GPT-5-mini, Anthropic Claude Haiku 4.5 |
| Questions classified | 6,954 | `output/report_01/final/master_dataset.csv` |
| Topic-level agreement | 89.2% (κ=0.839) | `output/report_01/comparison/agreement_summary.csv` |
| Subtopic-level agreement | 69.7% (κ=0.687) | same |
| Economic questions dominate | ~42.8% | `output/report_01/comparison/topic_distribution.csv` |
| Classification cost | ~$15 | Manual estimate |

**Narrative goal:** Show the classification works, establish the topic taxonomy.

---

## Ch 3: Survey Overlap — Finding the Connections

| Claim | Number | Source |
|-------|--------|--------|
| ACS selected as anchor | Qualitative | Breadth + prominence justification |
| "Family 2" surveys identified | 5 surveys | SIPP, AHS, CE, CPS, FoodAPS |
| SIPP highest overlap | 577 shared subtopic-question intersections | `output/report_02/data/acs_family2_summary.csv` |
| CPS and FoodAPS selected for deep-dive | 2 surveys | Feasibility + diversity of purpose |

**Narrative goal:** Justify the ACS anchor and survey pair selection. Set up the pairwise analysis.

---

## Ch 4: Pairwise Harmonization — The Core Analysis

| Claim | Number | Source |
|-------|--------|--------|
| Total pairs evaluated | 1,598 | `stage4_survey_summary.json` |
| CPS–ACS pairs | 1,030 | same |
| FoodAPS–ACS pairs | 568 | same |
| Unique source questions | 380 (240 CPS + 140 FoodAPS) | same |
| 3 rater models | GPT-5-mini, Claude Haiku 4.5, Gemini 3 Flash | `config/report_03.yaml` raters |
| 3 arbitrator models | GPT-5.2, Claude Opus 4.5, Gemini 3 Pro | `config/report_03.yaml` arbitrators |
| Rater-stage agreement (Fleiss' κ) | 0.611 | `stage2_agreement_metrics.json` |
| Post-arbitration agreement (Cohen's κ, feasibility) | 0.843 | `stage3_arbitration_metrics.json` |
| Post-arbitration binary κ | 0.896 | same |
| Quality gates passed | Yes (both feasibility and binary) | same |

**Narrative goal:** Multi-model methodology produces reliable, reproducible judgments. Arbitration resolves disagreement effectively.

---

## Ch 5: Results — What We Found

| Claim | Number | Source |
|-------|--------|--------|
| CPS question-level harmonization rate | 42.5% (102/240) | `stage4_survey_summary.json` |
| FoodAPS question-level harmonization rate | 48.6% (68/140) | same |
| Combined ~45% | 170/380 | same — confirmed 2026-02-14 |
| F1 (direct recode) | ~16% | same |
| F2 (statistical adjustment) | ~29% | same |
| F3 (not feasible) | ~55% | same |
| CC dominates barriers | ~87% | `barrier_summary_by_survey.csv` |
| TC (temporal) | ~7% | same |
| RS (response scale) | ~4% | same |

**✅ RECONCILED 2026-02-14:** `stage4_survey_summary.json` confirms CPS=102 (42.5%), FoodAPS=68 (48.6%), combined=170. Report 03 exec summary values (100/41.7%, 168 combined) were stale.

**Narrative goal:** ~45% have paths. The barrier taxonomy explains WHY the other ~55% don't, and that's fine — different purposes are a feature, not a bug.

---

## Ch 6: Implications — So What?

| Claim | Number | Source |
|-------|--------|--------|
| Bridge variables identified | ~170 questions | Ch 5 results |
| Expert review load reduced | ~76% auto-processed | `stage4_survey_summary.json` triage data |
| 93 questions flagged for expert review | 93 | same |

**Narrative goal:** Cross-survey enrichment > consolidation. In-sourcing value. AI handles breadth, humans judge edges.

---

## Ch 7: Limitations & Next Steps

No new numbers. References Report 04 scope (multi-hop enrichment across all 47 surveys).

**Narrative goal:** Honest about scope (2 survey pairs so far), clear about extension path.

---

## Appendix A: Architecture & Data Flow

Diagrams only. No new numbers. One diagram per pipeline stage.

## Appendix B: Harmonization Taxonomy

Barrier codes (CC, TC, RS, PC, MC, PM) with definitions and examples.
Feasibility codes (F1, F2, F3) with definitions.

---

## Known Reconciliation Issues

1. ~~**CPS consolidable count:**~~ ✅ Resolved — 102 (42.5%) per `stage4_survey_summary.json`. Stale exec summary said 100.
2. ~~**Combined count:**~~ ✅ Resolved — 170 per source of truth. Stale exec summary said 168.
3. ~~**Pair-level barrier %s:**~~ ✅ Resolved — `barrier_summary_by_survey.csv` uses **all pairs per survey** as denominator (CPS=1,030, FoodAPS=568), giving CC=85.1%/88.9%. Report 03 exec summary used F3-only denominator (giving 96.5%). Master report Ch 5 uses the per-survey all-pairs framing from the CSV. Both are correct; different denominators.
4. **Report 01 classification models** (GPT-5-mini, Claude Haiku 4.5) vs **Report 03 rater models** (gpt-5-mini, claude-haiku-4-5-20251001, gemini-3-flash-preview). These are different stages with different model versions — don't conflate. Master report handles this correctly (Ch 2 vs Ch 4).
