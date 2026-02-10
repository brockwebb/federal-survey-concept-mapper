# Federal Survey Harmonization Research — Fact Sheet

> **One sentence:** The federal government already collects a massive mosaic of survey data — AI can map how those pieces fit together, unlocking new analytical power without collecting a single additional data point.

---

## What's the problem?

The federal statistical system operates **48+ household and establishment surveys** containing over **7,000 overlapping questions**. These surveys were designed independently, by different agencies, for different purposes. Nobody has a complete map of where they overlap, where they're compatible, and where the differences actually matter. Building that map by hand would take a PhD student a full semester — per survey pair. There are hundreds of pairs.

## Why should leadership care?

**Response rates are declining across federal surveys.** Every year, it gets harder and more expensive to collect new data. Meanwhile, the government already *has* enormous amounts of data that could answer questions no single survey can — if the connections between surveys were mapped and quality-scored. This research builds that map.

The primary value is **data enrichment**: using overlapping questions as "bridge variables" to link surveys and assemble richer analytical datasets. A secondary value is identifying where **instrument consolidation** could reduce respondent burden. Enrichment gives every agency *more* capability. Nobody loses anything.

## How is this different from prior work?

Traditional survey harmonization is manual, slow, and limited to 2–3 surveys at a time. This research uses **AI-assisted classification at scale** — multiple large language models independently rating question pairs, with ensemble methods and multi-model arbitration to ensure reliability. The approach holds the *entire federal survey topology* in view simultaneously, finding connections that no individual expert could surface because no human holds 7,000 questions in working memory at once.

## What does the evidence show?

| Validation Check | Result | What It Means |
|:---|:---|:---|
| **Do AI raters agree with each other?** | 3 independent AI models reached substantial agreement on barrier classification | The task is well-defined; results reflect real question properties, not model quirks |
| **Do AI arbitrators converge?** | Near-perfect agreement on consolidability verdicts (κ = 0.84–0.90) | High confidence in final harmonization judgments |
| **Are the rates consistent across surveys?** | CPS→ACS: 42.5% harmonizable; FoodAPS→ACS: 48.6% harmonizable | Stable rates suggest a general property of federal surveys, not an artifact of specific survey pairs |
| **Do demographics behave as expected?** | Race, age, relationship questions show near-100% consolidability | Known-easy questions score easy — the framework has face validity |
| **Do specialized questions behave as expected?** | Construct mismatch is the dominant barrier (~96% of failures) | The framework correctly identifies *why* questions can't be linked, not just that they can't |
| **Is the methodology reproducible?** | Full pipeline, all data, and all code are public and scripted | Any researcher can rerun the analysis and verify results |
| **Is it cost-effective?** | Total API costs under $100 for comprehensive 3-model analysis of 1,598 pairs | Orders of magnitude cheaper than equivalent manual expert review |

## What are the key findings so far?

**~45% of questions** examined across two major survey pairs (CPS and FoodAPS vs. ACS) have at least one viable harmonization path. These break down into quality tiers:

- **Tier 1 — Direct recode** (~16%): Questions are close enough to link with simple recoding. High-confidence bridge variables.
- **Tier 2 — Statistical adjustment** (~29%): Linkable with known transformations (reference period alignment, response scale mapping). Usable bridges with documented limitations.
- **Tier 3 — Not linkable** (~55%): Different constructs entirely. The framework correctly identifies these and explains *why*.

Where harmonization fails, the barriers are informative: construct mismatch dominates (96%), meaning most failures are because surveys genuinely ask about different things — not because of fixable methodological differences.

## What's the risk if this work isn't pursued?

The federal survey ecosystem continues operating as isolated silos. Declining response rates erode data quality with no compensating strategy. Cross-survey analytical opportunities — connections that could inform policy without additional collection costs — remain invisible. Other national statistical offices and the private sector are already investing in these capabilities.

## What's next?

**Report 04** extends the analysis from pairwise comparisons to the full multi-survey network, using AI to discover multi-hop enrichment paths (Survey A → B → C) across all 48 surveys. This is where the approach delivers its highest value: finding non-obvious connections across the entire federal survey topology that exceed any individual expert's working memory.

---

*This research was conducted under the Census Bureau's survey harmonization initiative. Four technical reports document the methodology and findings in detail. The full codebase, data, and analysis pipeline are available in the project repository.*
