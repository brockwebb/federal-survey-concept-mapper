# Stage 4 Research Framing: Consolidability Analysis

**Created:** 2026-01-31  
**Status:** Draft - pending resolution of open questions

---

## The Combinatorial Math Problem

We have:
- ~240 CPS questions paired with ACS questions within topic buckets → 1,030 pairs
- ~140 FoodAPS questions paired with ACS questions within topic buckets → 568 pairs
- Average ~4-5 ACS comparisons per source question

Most pairs are apples-to-oranges **by design**. We were deliberately naive/exhaustive — comparing every question to every question within topic areas. 

Example: "What's your race?" paired with "What's your income?" because they're both tagged "Demographics."

**CC (Construct/Concept) failures at 96-97% aren't a failure of the method — they're expected.** The signal is in what *passes*, not what fails.

---

## Why This Approach?

An expert or smarter pre-filtering system could quickly exclude obviously mismatched pairs. We didn't do that because:

1. **Naive baseline:** Establishes what's consolidable without human judgment
2. **Exhaustive coverage:** No consolidable pair gets missed due to filtering assumptions
3. **Reproducibility:** No subjective "these obviously don't match" decisions

One potential experiment would have been to only analyze pairs above a certain similarity threshold. We chose exhaustive comparison instead.

---

## What Stakeholders Actually Need

### 1. For Consolidable Questions
Not just "100 questions are consolidable" but specific actionable mappings:

> "CPS Q6 → ACS Q19 (F1, direct recode)"

Which specific ACS question(s) can each source question consolidate with?

### 2. For Non-Consolidable Questions  
What's the *best available* match, even if it fails?

> "CPS Q42 has no consolidable path — closest match is ACS Q87 but fails on temporal mismatch (TC.2, F3)"

This tells stakeholders: if you really need this question, here's why it can't be consolidated and what would need to change.

### 3. The "Why" Framing
- CC dominates failures because we compared everything to everything
- Experts would pre-filter obvious mismatches
- The meaningful analysis is what passes, not what fails
- Combinatorial pair counts (1,030 / 568) will confuse laypeople — focus on question counts (240 / 140)

---

## Methodological Framework

See `docs/stage4_ensemble_methodology.md` for full theoretical treatment.

**Summary:** We implement four scoring methods (composite, entropy, Bayesian, Borda) to rank pairs by consolidability confidence. The ensemble approach:
- Captures different aspects of classification quality
- Identifies edge cases where methods diverge
- Trades precision for accuracy (robust to methodological assumptions)

**Key theoretical contribution:** The entropy-based approach frames LLM classifiers as stochastic samplers in an energy landscape. High classifier agreement = stable attractor = robust classification. This connects to statistical mechanics, ensemble methods, and "wisdom of crowds."

See methodology log Decision 016 for rationale and alternatives considered.

---

## Resolved Questions

### Ranking Criteria (resolved 2026-01-31)
- **Best match per question:** One best ACS match per source question, ranked by feasibility (F1 > F2 > F3) then Borda score as tiebreaker
- **Non-consolidable:** Best-available "nearest miss" is surfaced (highest Borda among F3 pairs), giving stakeholders visibility into what almost worked
- **Presentation:** Question-centric table with one row per source question, best match identified

### Triage Quadrant Assignment (resolved 2026-01-31)
Two-axis framework using Borda (direction) × Entropy (stability):
- **Q1:** High Borda + High Entropy → Confident consolidable (auto-process)
- **Q2:** Low Borda + High Entropy → Confident non-consolidable (low priority)
- **Q3:** High Borda + Low Entropy → Edge case, leaning yes but contested (human review priority)
- **Q4:** Low Borda + Low Entropy → Ambiguous (human review secondary)

Thresholds: median of best-match scores (not pair-level, where the degenerate F3 majority makes Borda median = 0).

### Open Questions Remaining
- **Layperson framing:** Emphasis on question counts for stakeholder communication (Stage 5)
- **Multiple matches:** Currently surfacing only the best match; full ranked list available in pair-level data if needed

---

## Current Stage 4 Outputs

- `stage4_question_level.csv` — 380 rows, binary consolidable flag per question
- `stage4_survey_summary.json` — Aggregate rates (41.7% CPS, 48.6% FoodAPS)
- `stage4_findings_report.md` — Narrative with topic breakdown
- `stage4_f2_transformations.csv` — 241 F2 pairs needing adjustment
- `stage4_barrier_patterns.csv` — F3 barrier distribution
- `stage4_bakeoff_scores.csv` — Pair-level scores from 4 methods + ensemble
- `stage4_bakeoff_report.md` — Scoring method comparison and correlations
- `stage4_question_best_matches.csv` — One row per question with best ACS match + triage quadrant

---

## Next Steps

1. ~~Resolve open questions (ranking criteria, thresholds, presentation)~~ ✅
2. ~~Generate consolidable pairs mapping~~ ✅
3. ~~Generate "nearest miss" for non-consolidable~~ ✅ (included in best-match rollup)
4. Reframe outputs for stakeholder communication (Stage 5)
