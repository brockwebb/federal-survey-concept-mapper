# Report 04 Vision: AI-Assisted Cross-Survey Enrichment Discovery

**Date**: 2026-02-05  
**Status**: PLANNING  
**Depends on**: Report 03 (bridge variable catalog with quality scores)

---

## Core Question

Given bridge variables identified and quality-scored in Report 03, can AI identify cross-survey enrichment relationships that domain experts haven't surfaced?

## The Human Limitation This Addresses

Not intelligence — **dimensionality**. No human holds the full topology of 7,000+ questions across 48 surveys in working memory simultaneously. A survey methodologist knows their instrument deeply and maybe 2-3 adjacent ones. The institutional structure of the federal statistical system mirrors this cognitive constraint: knowledge is siloed because attention is siloed.

The connections between NHIS health variables and ACS housing variables mediated through CPS economic indicators — nobody examines that triple because nobody's job spans all three.

## What AI Provides

**Simultaneous breadth** over a characterized topology. Not smarter analysis — the ability to hold the entire question-level landscape in context and surface structural opportunities that cognitive bandwidth constraints make invisible to any individual researcher.

## Approach (Preliminary)

### Phase 1: Build the topology
- Surveys as nodes, bridge variables as weighted edges
- Edge weights from Report 03 harmonization quality scores (F1 > F2 > F3)
- Barrier codes as edge metadata (linkage constraint characterization)

### Phase 2: Direct bridge analysis
- Identify bilateral enrichment opportunities (Survey A ↔ Survey B)
- Quality-rank by bridge variable strength
- Map coverage: what questions in Survey A gain enrichment from Survey B, and vice versa

### Phase 3: Multi-hop enrichment paths
- Find transitive linkage: A → B → C where no direct A → C bridge exists
- Identify enrichment paths that no pairwise examination reveals
- Characterize cumulative uncertainty through chains (bridge quality degrades multiplicatively)

### Phase 4: Latent structure discovery
- Community detection on survey topology graph
- Identify survey clusters that share enrichment potential
- Surface unexpected connections across survey domains

### Phase 5: Worked examples
- ACS + CPS: Demonstrate how bridge variables enable county-level monthly employment estimates for subpopulations currently only estimable annually
- ACS/CPS + FoodAPS: Show how bridge variables enable food acquisition pattern estimation for populations FoodAPS alone can't touch (5,000 households → demographic-level estimates)

## Concrete Deliverables

1. **Survey topology graph** with weighted edges (bridge variables) and annotated constraints
2. **Multi-hop enrichment catalog**: paths through the survey network enabling inference no single survey supports
3. **Enrichment opportunity ranking**: prioritized by bridge quality, coverage gain, and practical feasibility
4. **Worked examples**: 2-3 concrete demonstrations of enrichment value using Phase 3 survey pairs
5. **Visualization**: Interactive network graph showing the federal survey mosaic and its linkage structure

## Success Criteria

- Identify at least N enrichment paths not previously documented in survey methodology literature
- Demonstrate that multi-hop bridges exist with acceptable cumulative quality
- Produce actionable enrichment recommendations for at least one Phase 3 survey pair
- Validate that AI-surfaced connections are methodologically sound (expert review)

## Dependencies

- Report 03 completion (bridge variable catalog)
- Expansion of pipeline to additional surveys beyond CPS/FoodAPS-ACS (SIPP, NHIS, AHS)
- Neo4j graph infrastructure (already available via project MCP)

## Open Questions

- How does bridge quality degrade through multi-hop chains? Need multiplicative uncertainty model.
- What minimum bridge quality threshold makes linkage useful vs. introducing systematic bias?
- How do temporal mismatches (different reference periods) affect enrichment validity?
- Can we validate enrichment claims using surveys that DO have direct linkage (e.g., CPS-ACS linked records)?

## Connection to Broader Narrative

Report 03 builds the map. Report 04 uses the map. The value proposition is complete only with both: Report 03 shows that AI can systematically characterize the federal survey mosaic, Report 04 shows what becomes possible when you can see the whole mosaic at once.
