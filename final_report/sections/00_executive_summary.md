# Executive Summary

## The Challenge

Federal household surveys face mounting pressure. Response rates continue to decline, raising the cost per completed interview. Each survey question represents an investment—yet developing the capabilities to systematically assess whether the federal survey ecosystem is structured efficiently requires substantial labor. Manual analysis of questionnaire overlap across dozens of surveys would require weeks of expert time and rarely happens at ecosystem scale.

## What This Study Did

This proof-of-concept applied AI-based text categorization to map 6,987 questions from 46 federal demographic surveys to the Census Bureau's Survey Explorer taxonomy. Two independent language models (GPT-5-mini and Claude Haiku 4.5) categorized each question; a higher-capability model (Claude Sonnet 4.5) attempted to resolve disagreements and provide more nuanced assessments where the primary models diverged.

**Key metrics:**
- **Processing time**: ~2 hours (vs. estimated ~70 hours manual review)
- **Cost**: ~$15 in API fees
- **Success rate**: 99.5% of questions categorized
- **Inter-rater reliability**: Cohen's κ = 0.842 ("almost perfect agreement")

**A key benefit**: This approach enables automated tagging and data enrichment at scale. Building richer semantic knowledge about surveys and their questions creates a foundation for deeper understanding of topical coverage, measurement approaches, and relationships across the survey ecosystem.

## What We Found

The analysis surfaced three patterns warranting expert attention:

**1. Measurement Concentration**: A small fraction of taxonomy concepts dominate federal surveys. Ten concepts (6.6% of the taxonomy) account for 39.4% of all questions. Income, health insurance, and employment status are measured extensively across multiple surveys.

**2. Expected Overlap in Demographic Measurement**: Many demographic surveys ask similar questions about respondents—age, income, household composition, employment. This duplication is by design: it establishes which universe different populations belong to and enables cross-survey comparisons. The more interesting analytical question concerns under-represented and hard-to-count populations: what additional data or enrichment is needed to better understand these groups? Large, stable populations that change slowly yield less new information than targeted measurement of populations where we need to understand impacts, outcomes, and effects for evidence-based policy.

**3. Coverage Reflects Study Scope**: Approximately 30% of Census taxonomy concepts have limited or no coverage in the surveys analyzed. This is expected—we examined household demographic surveys, not the full federal statistical portfolio. The value of this methodology lies in demonstrating that systematic mapping is feasible. Extending this approach to additional survey domains would build progressively more complete coverage maps, using this analysis as a springboard.

## What This Means

This analysis demonstrates **technical feasibility**, not policy prescription. The methodology can surface patterns at scale that would be prohibitively expensive to identify manually. But interpreting those patterns—determining which overlaps represent problems, which gaps matter, and what actions are warranted—requires domain expertise.

**This approach becomes valuable if declining response rates demand better ROI per question asked.** When every survey question costs more to field, systematic analysis of what's already being measured across the survey ecosystem enables more informed questionnaire design decisions.

## Recommended Next Steps

1. **Expert validation**: Have subject matter experts review a sample of 100-200 categorizations to assess accuracy before relying on results.

2. **Pattern interpretation**: Convene survey methodologists to evaluate whether identified overlaps and gaps align with operational knowledge.

3. **Pilot application**: If validation is positive, apply the methodology to support a specific questionnaire redesign or burden reduction effort.

## What This Is Not

This is exploratory research, not an operational system. It does not recommend merging specific surveys, does not claim AI should replace expert judgment, and does not assert that all identified patterns represent problems. The value is in enabling structured analysis that experts can then interpret.

---

**Bottom line**: AI can now do in 2 hours what would take weeks manually—systematically mapping survey questions to standardized concepts across the federal survey ecosystem. Whether the patterns surfaced are actionable depends on expert review. The methodology is ready for that conversation.
