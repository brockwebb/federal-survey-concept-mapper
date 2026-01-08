# From Weeks to Hours
## AI-Assisted Concept Mapping for Federal Survey Analysis

---

### THE CHALLENGE

| Problem | Impact |
|---------|--------|
| Response rates declining | Cost per response rising |
| 46+ federal demographic surveys | No systematic overlap analysis |
| Manual review: ~70 hours | Rarely attempted at scale |

**Question**: How efficiently is the federal survey ecosystem structured?

---

### THE APPROACH

```
┌─────────────────┐     ┌─────────────────┐
│  Claude Haiku   │     │   GPT-5-mini    │
│     4.5         │     │                 │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
              ┌─────────────┐
              │   AGREE?    │
              └──────┬──────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    ┌─────────┐           ┌─────────────┐
    │   YES   │           │     NO      │
    │  (67%)  │           │   (33%)     │
    └─────────┘           └──────┬──────┘
                                 ▼
                         ┌─────────────┐
                         │ ARBITRATION │
                         │  (Sonnet)   │
                         └─────────────┘
```

**Dual-model cross-validation** → High agreement = confident categorization  
**Confidence-based arbitration** → Disagreements resolved systematically

---

### PERFORMANCE

| Metric | Result |
|--------|--------|
| Questions processed | 6,987 |
| Surveys covered | 46 |
| Success rate | 99.5% |
| Inter-rater reliability | κ = 0.842 ("almost perfect") |
| Processing time | ~2 hours |
| Total cost | ~$15 |
| vs. Manual estimate | **35× faster** |

---

### KEY FINDINGS (Require Expert Validation)

**📊 CONCENTRATION**
- 10 concepts (6.6% of taxonomy) → 39.4% of all questions
- Income, Health Insurance, Employment dominate measurement

**🔄 OVERLAP PATTERNS**
- NSCH age variants: ~100% conceptual overlap
- NTPS public/private teacher: ~82% overlap
- SIPP ↔ CE: ~55% shared concepts

**⚠️ COVERAGE GAPS**
- ~30% of taxonomy concepts: no household survey coverage
- 47 concepts measured by only one survey (single points of failure)

---

### WHAT THIS IS — AND ISN'T

| ✅ This Analysis Provides | ❌ This Analysis Does Not Provide |
|---------------------------|-----------------------------------|
| Structured data on survey content | Validation of categorization accuracy |
| Patterns for expert review | Interpretation of whether patterns matter |
| Reproducible methodology | Policy recommendations |
| Empirical coverage maps | Decisions about consolidation |

**AI surfaces patterns. Experts interpret them.**

---

### RECOMMENDED NEXT STEPS

1. **VALIDATE** → Expert review of 200-300 question sample
2. **INTERPRET** → Survey methodologists evaluate identified patterns  
3. **PILOT** → Apply methodology to support a specific redesign effort

---

**Full Report**: Available upon request

*This is exploratory research. Views expressed are the author's own.*
