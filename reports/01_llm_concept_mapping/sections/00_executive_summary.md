# Executive Summary

## The Challenge

Federal household surveys face mounting pressure. Response rates continue to decline, raising the cost per completed interview. Each survey question represents an investment, yet developing the capabilities to systematically assess whether the federal survey ecosystem is structured efficiently requires substantial labor. Manual analysis of questionnaire overlap across dozens of surveys would require weeks of expert time and rarely happens at ecosystem scale.

## What This Study Did

This proof-of-concept applied AI-based text categorization to map 6,987 questions from 46 federal demographic surveys to the Census Bureau's Survey Explorer taxonomy. Two independent language models (GPT-5-mini and Claude Haiku 4.5) categorized each question; a higher-capability model (Claude Sonnet 4.5) attempted to resolve disagreements and provide more nuanced assessments where the primary models diverged.

**Key metrics:**
- **Processing time**: ~2 hours (vs. estimated ~70 hours manual review)
- **Cost**: ~$15 in API fees
- **Success rate**: 99.5% of questions categorized
- **Inter-rater reliability**: Cohen's κ = 0.842 ("almost perfect agreement")

**A key benefit**: This approach enables automated tagging and data enrichment at scale. Building richer semantic knowledge about surveys and their questions creates a foundation for deeper understanding of topical coverage, measurement approaches, and relationships across the survey ecosystem.

## What We Found

The analysis produced three key findings:

**1. Technical Feasibility Demonstrated**: This proof of concept successfully showed that AI-based LLM tools can reliably categorize survey questions at scale. Two independent models achieved Cohen's κ = 0.842 ("almost perfect agreement"), processing nearly 7,000 questions in approximately 2 hours. The methodology works.

**2. Topic Distribution Visible at a Glance**: The methodology produces visualizations (Figure 2) showing how questions distribute across taxonomy concepts. Within household demographic surveys, Economic and Social topics dominate, while coverage is thinner in some subtopics. Whether sparse coverage in particular areas warrants closer examination or appropriately reflects survey scope is a question for domain experts.

**3. Patterns Reflect Study Scope**: The concentration of questions in certain topics (Income, Health Insurance, Employment Status) and the approximately 30% of taxonomy concepts without coverage are expected given our focus on household demographic surveys. This is one segment of the federal statistical portfolio. The value of this methodology lies in demonstrating that systematic mapping is feasible; extending this approach to additional survey domains would build progressively more complete coverage maps.

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

**Bottom line**: AI can now do in 2 hours what would take weeks manually: systematically mapping survey questions to standardized concepts across the federal survey ecosystem. Whether the patterns surfaced are actionable depends on expert review. The methodology is ready for that conversation.
