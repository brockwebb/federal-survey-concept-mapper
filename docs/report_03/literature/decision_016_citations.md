# Decision 016: Literature Citations

> **Note (2026-01-31):** This document was created during initial literature review before external critical review. The "novel contribution" framing below has been tempered. See `docs/stage4_ensemble_methodology.md` "Honest Assessment" section for the sober framing: useful operational instrumentation, not theoretical discovery.

---

**Source:** Perplexity research review (2026-01-31)
**Full review:** `docs/literature/perplexity_entropy_methodology_review.md`

---

## Novelty Assessment

**Verdict:** The methodology is grounded in established theory, but the specific combination is defensibly novel.

| Component | Status | Prior Art |
|-----------|--------|-----------|
| Shannon entropy as agreement measure | Established (but different use) | Ensemble diversity, info-theoretic IRR |
| Energy landscape metaphor | Well-established | Hopfield, Boltzmann machines |
| Multi-LLM ensemble uncertainty | Emerging field | MUSE, DiverseAgentEntropy |
| **Our combination** | **Novel** | No direct prior art |

**What's novel:**
- Per-item entropy over heterogeneous LLM ensemble (6 models: 3 raters + 3 arbitrators)
- On subjective classification task without ground truth
- Empirical demonstration that entropy is orthogonal to vote-count methods (ρ=0.07-0.08)
- Energy-landscape interpretation: low entropy = deep attractor basin

---

## Thread 1: Entropy as Classifier Agreement

### Key Citations

1. **Khairalla et al. (2021)** - "Creating Ensemble Classifiers with Information Entropy Diversity"  
   *Wiley Complexity*  
   Uses entropy to measure diversity among classifiers for ensemble selection. Close in spirit but focuses on ensemble composition, not per-item agreement.  
   [^3]: https://onlinelibrary.wiley.com/doi/10.1155/2021/9953509

2. **Martins et al. (2020)** - Information-theoretic inter-rater agreement  
   *PMC Medical Research*  
   Proposes "informational agreement" indices using mutual information as alternative to kappa. Supports entropy for categorical rating but assumes human raters + latent truth.  
   [^4]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7679268/

3. **Cunningham (2008)** - "The use of entropy to measure structural diversity"  
   *IEEE Ensemble Methods*  
   Uses entropy to quantify structural diversity across classifiers at ensemble level.  
   [^8]: https://ieeexplore.ieee.org/document/4721376/

### Gap Identified
No prior work uses per-item Shannon entropy over LLM ensemble votes as an operational confidence score separate from vote direction.

---

## Thread 2: Energy Landscape and Attractor Dynamics

### Key Citations

4. **Hopfield (1982)** - Original Hopfield network formulation  
   *Wikipedia overview*  
   Introduces energy function with gradient descent dynamics converging to fixed-point attractors. Deep basins = stable memories.  
   [^5]: https://en.wikipedia.org/wiki/Hopfield_network

5. **Krotov (2024)** - Hopfield networks historical overview  
   *Nature Neuroscience/PMC*  
   "Hopfield introduced an energy landscape into neural network theory" - explicit framing of basin depth as stability.  
   [^6]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11573896/
   [^12]: https://www.sciencedirect.com/science/article/pii/S089662732400802X

6. **Imperial College tutorial** - Boltzmann machines and RBMs  
   *IC Technical Report*  
   Energy landscape as valleys/basins, Gibbs distributions p(s) ∝ exp(-E(s)).  
   [^7]: https://www.doc.ic.ac.uk/~ae/papers/julian.pdf

7. **Imperial College** - "Strong attractors" in Hopfield models  
   *IC Technical Report*  
   Quantifies how stronger patterns correspond to lower energy and larger basins.  
   [^13]: https://www.doc.ic.ac.uk/~ae/papers/hopfield-networks.pdf

### Assessment
Energy-landscape metaphor is standard and well-cited. Applying it to multi-LLM agreement and operationalizing "basin depth" via empirical entropy is our innovation.

---

## Thread 3: LLM Ensemble Confidence

### Key Citations

8. **MUSE (2025)** - "Multi-LLM Uncertainty via Subset Ensembles"  
   *arXiv/PMC*  
   Uses Jensen-Shannon divergence across LLM predictive distributions to quantify disagreement. Closest mathematical cousin but focuses on calibrated uncertainty, not structural agreement.  
   [^1]: https://arxiv.org/abs/2507.07236
   [^11]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12702469/

9. **DiverseAgentEntropy (2024)** - "Multi-Agent Approach to Estimating Black-Box Model Uncertainty"  
   *arXiv*  
   Uses weighted entropy over multiple agents' answers as uncertainty. Very close mathematically but: (a) single-model multi-sample, (b) treats entropy as uncertainty about correctness, not orthogonal agreement signal.  
   [^2]: https://arxiv.org/html/2412.09572v2

10. **Inter-Model Consensus (2024)** - "Enhancing Answer Reliability Through Inter-Model Consensus of LLMs"  
    *arXiv*  
    Studies LLM consensus with chi-square, Fleiss' kappa, bootstrap CIs. Close to our intuition but uses traditional metrics, not entropy-based stability.  
    [^16]: https://arxiv.org/html/2411.16797v1

### Gap Identified
No prior work combines:
- Heterogeneous multi-LLM ensemble (different model families)
- Subjective classification task without ground truth
- Per-item entropy as orthogonal signal to vote-count methods
- Energy-landscape interpretation

---

## Recommended Positioning

**For the paper/report:**

1. **Cite** information-theoretic IRR and ensemble-diversity work to justify entropy as principled agreement measure [^3][^4][^8]

2. **Cite** Hopfield/Boltzmann/attractor literature as conceptual lineage for energy-landscape framing [^5][^6][^12][^13][^7]

3. **Cite** MUSE and DiverseAgentEntropy as closest existing work on multi-LLM uncertainty [^1][^2][^11]

4. **Distinguish** our contribution:
   - Subjective tasks without ground truth
   - Heterogeneous LLM ensemble (not single-model multi-sample)
   - Empirical demonstration of orthogonality (ρ=0.07-0.08)
   - Explicit "what" vs "how strongly" separation

**Claim:** Using Shannon entropy over multi-LLM ensemble votes as a separate, attractor-style agreement signal—empirically orthogonal to vote-count confidence—is a novel methodological contribution grounded in established theory.

---

## BibTeX (to be formatted)

```
@article{khairalla2021entropy,
  title={Creating Ensemble Classifiers with Information Entropy Diversity},
  journal={Complexity},
  year={2021},
  doi={10.1155/2021/9953509}
}

@article{hopfield1982neural,
  title={Neural networks and physical systems with emergent collective computational abilities},
  author={Hopfield, John J},
  journal={Proceedings of the National Academy of Sciences},
  year={1982}
}

@article{muse2025,
  title={MUSE: Multi-LLM Uncertainty via Subset Ensembles},
  journal={arXiv},
  year={2025},
  url={https://arxiv.org/abs/2507.07236}
}

@article{diverseagententropy2024,
  title={Multi-Agent Approach to Estimating Black-Box Model Uncertainty},
  journal={arXiv},
  year={2024},
  url={https://arxiv.org/html/2412.09572v2}
}
```
