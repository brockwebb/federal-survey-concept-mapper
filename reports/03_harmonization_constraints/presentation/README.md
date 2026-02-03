# Capstone Slide Deck

**Created:** 2026-02-02
**Format:** Quarto Revealjs

---

## Files

- `_quarto.yml` — Quarto project configuration
- `slides.qmd` — Main presentation content (Quarto markdown)
- `images/` — Local copy of all visuals (5 PNG files)
- `README.md` — This file
- `QUICK_START.md` — Quick reference guide
- `SCAFFOLD_VERIFICATION.md` — Creation verification report

---

## Rendering

### Render to HTML (Revealjs)

```bash
quarto render slides.qmd
```

Output: `_output/slides.html`

### Preview with live reload

```bash
quarto preview slides.qmd
```

Opens browser with live preview.

### Export to PDF

```bash
quarto render slides.qmd --to pdf
```

Requires Chrome/Chromium installed.

### Export to PowerPoint

```bash
quarto render slides.qmd --to pptx
```

---

## Slide Structure (5 Acts)

### Act 1: Setup (Slides 1-4)
- The Problem
- Why It Matters
- The Challenge
- Starting Point

### Act 2: Methodology (Slides 5-10)
- Concept Classification
- Key Insight
- Harmonization Framework
- Pairwise Comparison
- Multi-Model Ensemble
- Agreement & Arbitration

### Act 3: Results (Slides 11-14)
- Question-Level Rollup
- Headline Results
- Why Questions Can't Consolidate
- Expert Review Load

### Act 4: Examples (Slides 15-17)
- High Consolidability (F1)
- Medium Consolidability (F2)
- Not Consolidable (F3)

### Act 5: Takeaways (Slides 18-21)
- Deliverables
- What This Proves
- What's Next
- Summary
- Questions

---

## Assets

All visuals are stored locally in `images/`:
- `process_flow.png` — Pipeline diagram (33KB)
- `triage_quadrant.png` — 2D triage framework (96KB)
- `consolidation_rates.png` — Bar chart of consolidability rates (44KB)
- `barrier_distribution.png` — Pie chart of F3 barriers (47KB)
- `expert_review_load.png` — Stacked bar of triage quadrants (60KB)

**Note:** Images are copied from `../output/visuals/` and maintained locally for presentation portability.

Example pairs referenced from `../output/analysis/example_pairs_for_presentation.md`

---

## Customization

### Theme

Change in `_quarto.yml`:
```yaml
format:
  revealjs:
    theme: [simple, dark, league, beige, sky, night, serif, solarized]
```

### Slide Size

Adjust in `_quarto.yml`:
```yaml
format:
  revealjs:
    width: 1600   # Default: 1600
    height: 900   # Default: 900
```

### Transitions

```yaml
format:
  revealjs:
    transition: [none, fade, slide, convex, concave, zoom]
```

---

## Notes

- **Speaker notes** included in slides (press 's' during presentation)
- **Incremental reveals** on some slides (click to advance)
- **Callout boxes** for emphasis (.callout-important, .callout-note)
- Placeholders for contact info and links (fill in before delivery)

---

## Version History

| Date | Version | Notes |
|------|---------|-------|
| 2026-02-02 | v1.0 | Initial scaffold from task spec |

---

## TODO (Refinement)

- [ ] Fill in contact information (Questions slide)
- [ ] Add repository link
- [ ] Add link to expert review tables output
- [ ] Cherry-pick final example pairs (currently using task spec examples)
- [ ] Adjust slide timing/speaker notes
- [ ] Test render to PDF/PPTX formats
- [ ] Add any additional backup/appendix slides
