# Quick Start: Capstone Slide Deck

**Status:** ✅ Ready for content refinement

---

## View Slides

### Open in Browser
```bash
open _output/slides.html
```

Or navigate to:
```
reports/03_harmonization_constraints/presentation/_output/slides.html
```

### Live Preview (with auto-reload)
```bash
quarto preview slides.qmd
```

---

## Make Changes

1. **Edit content:** `slides.qmd`
2. **Render:** `quarto render slides.qmd`
3. **Refresh browser** to see changes

---

## File Structure

```
presentation/
├── _quarto.yml              # Configuration
├── slides.qmd               # Main content ← EDIT THIS
├── images/                  # Local visuals (5 PNG files)
├── README.md                # Full documentation
├── QUICK_START.md           # This file
├── SCAFFOLD_VERIFICATION.md # What was created
└── _output/
    └── slides.html          # Rendered presentation
```

---

## Key Shortcuts (During Presentation)

- **Space/Arrow keys:** Navigate slides
- **F:** Full screen
- **S:** Speaker notes view
- **O:** Overview mode (see all slides)
- **ESC:** Exit special modes

---

## Next Steps

### 1. Content Refinement
- [ ] Review narrative flow
- [ ] Adjust wording for clarity
- [ ] Add speaker notes if needed

### 2. Example Selection
Current examples are from task spec. To use examples from `example_pairs_for_presentation.md`:

```bash
# View available examples
cat ../output/analysis/example_pairs_for_presentation.md
```

Pick compelling examples and update slides 15-17.

### 3. Fill Placeholders
- [ ] Contact info (slide 22)
- [ ] Repository link (slide 22)
- [ ] Expert review tables link (slide 22)

### 4. Test Export Formats

**PDF:**
```bash
quarto render slides.qmd --to pdf
```

**PowerPoint:**
```bash
quarto render slides.qmd --to pptx
```

---

## Current Slide Count

**22 slides** = ~15-20 minute presentation

- Act 1 (Setup): 4 slides
- Act 2 (Methodology): 6 slides
- Act 3 (Results): 4 slides
- Act 4 (Examples): 3 slides
- Act 5 (Takeaways): 4 slides + Q&A

---

## Troubleshooting

**Visuals not appearing?**
```bash
# Check visuals exist locally
ls -la images/*.png
```

All 5 visuals should exist in `images/`:
- process_flow.png (33KB)
- triage_quadrant.png (96KB)
- consolidation_rates.png (44KB)
- barrier_distribution.png (47KB)
- expert_review_load.png (60KB)

Images are maintained locally for presentation portability.

**Render errors?**
```bash
# Check Quarto version
quarto --version

# Should be 1.4+ for revealjs features
```

---

## Quick Edits

### Change theme
Edit `_quarto.yml`:
```yaml
format:
  revealjs:
    theme: [simple, dark, league, sky]
```

### Adjust slide size
Edit `_quarto.yml`:
```yaml
format:
  revealjs:
    width: 1920   # Larger screens
    height: 1080
```

### Change transitions
Edit `_quarto.yml`:
```yaml
format:
  revealjs:
    transition: [none, fade, slide, convex]
```

---

## Resources

- [Quarto Revealjs Guide](https://quarto.org/docs/presentations/revealjs/)
- [Full README](README.md) — Detailed documentation
- [Verification Report](SCAFFOLD_VERIFICATION.md) — What was created
