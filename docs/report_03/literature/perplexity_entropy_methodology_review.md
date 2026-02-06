<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Here's your response to Perplexity:

Primary objective: \#2 + \#5 combined
I've developed a methodology and need to establish whether it's novel (requiring gap analysis) or has prior art I should cite (requiring focused lit review).
The specific methodology:
We're using Shannon entropy to measure classifier agreement (not prediction uncertainty) across a 6-model ensemble (3 LLM raters + 3 LLM arbitrators) on a subjective classification task (survey question consolidability).
Key empirical finding: Entropy-based scores are nearly uncorrelated (Spearman ρ=0.07-0.08) with vote-counting methods (Bayesian posterior, Borda count), suggesting entropy captures a distinct signal — how much classifiers agreed — orthogonal to which direction they voted.
The theoretical framing I want to validate/cite:
I'm framing LLM ensemble agreement through an energy landscape metaphor: when diverse LLM classifiers converge on the same answer, that's evidence of a "stable attractor" — a deep basin in the solution space that multiple independent samplers fell into. Low entropy = deep basin = robust classification. High entropy = flat landscape = genuinely ambiguous.
What I need:
For entropy as classifier agreement measure: Seminal papers (3-5) establishing precedent. Is this standard practice I should cite, or novel?
For energy-landscape framing of neural network/LLM convergence: Key papers (3-5) connecting statistical mechanics concepts to ML. Boltzmann machines, Hopfield networks, energy-based models — the conceptual ancestors.
For LLM ensemble confidence specifically: Any existing work on using multiple LLMs as an ensemble and measuring their agreement as a confidence/reliability signal. This may not exist — if so, that's useful to know.
Scope: Restrict to these 3 threads. I don't need comprehensive coverage — just enough to either cite properly or establish novelty.
Output: Annotated bibliography organized by thread, with explicit assessment of whether my framing appears novel or has clear precedent.

This should get you targeted citations rather than a sprawling lit review. The key question for Perplexity: "Is entropy-for-classifier-agreement standard practice, or have I stumbled onto something?"

Your method sits very close to the frontier: entropy-based agreement is known in classical ML/IRT-style settings, but I am not finding anything that (a) uses Shannon entropy over discrete votes from an LLM ensemble to quantify agreement separately from correctness and (b) connects that to an explicit energy-landscape/attractor framing for multi‑LLM decision stability. That is, there is clear precedent for each ingredient, but your specific combination and interpretation look novel.[^1][^2][^3][^4][^5][^6][^7]

***

## Thread 1: Entropy as a classifier/rater agreement measure

Here entropy is used, but mostly either as (i) a per‑model uncertainty score or (ii) a diversity index during ensemble construction, not as a stand‑alone “agreement score” orthogonal to vote direction, especially not for LLM raters on subjective tasks.

1. **Entropy/diversity in classical ensembles**

- Recent work on “Creating Ensemble Classifiers with Information Entropy Diversity” explicitly uses information entropy to measure diversity among component classifiers and to select subsets, treating entropy over outputs as an indicator of how varied the classifiers are. This is close in spirit to “entropy of disagreement,” but the focus is on optimizing ensemble composition, not on interpreting a fixed ensemble’s per‑item agreement as a reliability/ambiguity signal.[^3]
- Earlier work such as “The use of entropy to measure structural diversity” uses entropy to quantify structural diversity (architectural differences) across many classifiers, again at the ensemble level rather than per‑item agreement.[^8]
- There are more recent “entropy-based dynamic ensemble classification” methods that use entropy of samples to drive sampling and weighting policies, again treating entropy as information content or difficulty, but not directly as a per‑item inter‑classifier agreement metric to be compared with Bayesian posteriors or Borda ranks.[^9]

2. **Information-theoretic inter‑rater agreement**

- In medical‑diagnostic agreement work, an “informational agreement” index explicitly “à la Shannon” has been proposed as an alternative/generalization to kappa for multiple raters on categorical data. They use mutual information between raters and true state, and also mutual information between rater pairs, as agreement indices that overcome some kappa paradoxes.[^10][^4]
- This strongly supports your use of Shannon information to think about agreement in categorical rating, but those papers typically assume human raters plus a latent “truth,” and they summarize overall agreement structures rather than turning per‑item entropy over ratings into an operational confidence score.

3. **Multi‑LLM / multi‑agent uncertainty via information theory**

- A recent line of work on multi‑LLM uncertainty (e.g., MUSE: Multi‑LLM Uncertainty via Subset Ensembles) uses Jensen–Shannon divergence across model predictive distributions to quantify disagreement and then chooses subsets of LLMs that are “diverse yet coherent.” Conceptually, JSD here is playing almost exactly the role you want for entropy: high divergence = disagreement, but they use it more for calibrated uncertainty and subset selection than for a per‑item, interpretable “agreement score” contrasted with vote-count posteriors.[^11][^1]
- Multi‑agent approaches such as DiverseAgentEntropy construct multiple “agents” (variants of a query to the same model) and use the weighted entropy of their final responses as an uncertainty estimate; low entropy indicates higher model confidence. That is very close in mathematical form to what you are doing, but: (a) it is single‑model, multi‑sample rather than multi‑model, and (b) they treat entropy as *uncertainty about correctness*, not as a distinct axis of “agreement structure” separable from the *direction* of the answer.[^2]

4. **Assessment for your question**

- Using Shannon entropy over categorical votes/predictions as a *numerical measure of agreement/disagreement* is not new; both ensemble‑diversity work and information‑theoretic inter‑rater indices implicitly rely on that idea.[^4][^3][^8]
- However, I do not see prior work that:
    - Takes a fixed ensemble (multiple LLM raters and arbitrators),
    - Computes per‑item entropy over their discrete labels as an *agreement score*,
    - And then empirically shows that this score is nearly uncorrelated with vote‑count posteriors/Borda scores, arguing it captures a **separate structural property** (“how strongly did the ensemble converge?”) rather than correctness or margin.
- That specific use — entropy as an **orthogonal axis** of ensemble behavior on subjective tasks (consolidability), distinguished from direction of prediction — appears to be a novel framing with no direct off‑the‑shelf citation.

You can safely position your entropy score as conceptually grounded in information‑theoretic agreement measures, but empirically distinct from standard voting/Bayesian aggregation in the LLM ensemble setting, and I’d recommend explicitly citing informational agreement/kappa‑alternatives plus multi‑LLM JSD work as the closest relatives.[^1][^4]

***

## Thread 2: Energy landscapes and attractor dynamics as a framing

Here your metaphor lines up quite cleanly with established theory in Hopfield networks, Boltzmann machines, and modern attractor‑based views of neural computation and associative memory.

1. **Hopfield networks and energy basins**

- Hopfield’s original formulation and many expositions view the network as having an energy function whose gradient descent dynamics cause convergence to fixed‑point attractors; each stored pattern corresponds to a basin of attraction in the energy landscape.[^5]
- Recent historical/overview pieces emphasize precisely this: Hopfield introduced “an energy landscape into neural network theory” to conceptualize network state flow, associate deep basins with stable memories, and make the dynamics analyzable in physics‑like terms.[^12][^6]
- Work on “strong attractors” in Hopfield models quantifies how “stronger” patterns (stored more often or with higher degree) correspond to lower energy and larger basins of attraction, with explicit results linking degree to basin size and energy distribution.[^13]

2. **Boltzmann machines and RBMs**

- Boltzmann machines and restricted Boltzmann machines explicitly define probabilities over states as Gibbs distributions $p(s) \propto \exp(-E(s))$; the energy landscape metaphor is standard.[^7]
- Expository work literally draws the energy landscape as valleys/basins corresponding to attractors, and discusses how sampling or gradient dynamics move the system into low‑energy basins that represent coherent configurations or memories.[^7]

3. **General attractor networks and changing landscapes**

- Work on “localist attractor networks” shows how attractor basins and their shapes change as the network learns or as input changes, and explicitly describes the network operation as gradient descent/ascent in an energy landscape whose basins correspond to stored patterns.[^14]
- More recent applications in neuroscience use connectome‑based Hopfield‑style networks, again assigning energy to brain activation patterns and interpreting stable patterns as attractors with associated basins in the state space.[^15]

4. **Assessment for your framing**

- The specific mapping “low entropy of ensemble votes ≈ deep basin, high entropy ≈ flat landscape/ambiguous region” is not something I see explicitly in the LLM/ensemble literature, but it is very natural to connect:
    - energy‑based models and attractor basins, where strong attractors have large basins and draw many initial conditions into the same state;[^13][^7]
    - with your observation that many independently sampled LLMs converge to the same label, producing low empirical entropy over their outputs.
- So: the **energy‑landscape metaphor itself** is absolutely standard and well‑cited; applying it to *multi‑LLM ensemble agreement on subjective tasks* and *operationalizing “basin depth” via empirical Shannon entropy over outputs* appears to be your conceptual innovation. I do not see direct prior art that makes that precise identification.[^6][^12][^5]

You can comfortably say your interpretation is “inspired by classic energy‑based and attractor‑network theories” and cite Hopfield/Boltzmann/attractor‑network work as the conceptual lineage.[^12][^5][^6][^13][^7]

***

## Thread 3: LLM ensembles and agreement as a confidence/reliability signal

Here the key question is: has anyone already done what you are doing, specifically with multiple LLMs (or multiple “agents” built from LLMs), using agreement/consensus as a confidence or reliability signal?

1. **Multi‑LLM ensembles and uncertainty**

- The MUSE approach (Multi‑LLM Uncertainty via Subset Ensembles) explicitly aggregates predictions from multiple LLMs and uses information‑theoretic disagreement (Jensen–Shannon divergence) to quantify uncertainty, arguing that combining multiple LLMs yields more reliable uncertainty estimates than any single model.[^11][^1]
- They treat multi‑LLM disagreement as an uncertainty signal and perform subset selection to optimize calibration and robustness, but their focus is predictive uncertainty and calibration rather than “agreement as convergence evidence” on subjective survey labels.

2. **Multi‑LLM consensus for reliability**

- A 2024–2025 line of work on “Enhancing Answer Reliability Through Inter‑Model Consensus of LLMs” studies several LLMs collaborating and forming consensus, then defines reliability metrics based on consensus rates, statistical tests (chi‑square, Fleiss’ kappa), and bootstrap confidence intervals to evaluate how consensus relates to reliability in the absence of ground truth.[^16]
- This is very close to your intuition that agreement across independent LLMs is evidence of reliability, but they remain in the space of traditional agreement metrics and frequency‑based consensus scores, not Shannon‑entropy‑based stability metrics or energy‑landscape metaphors.

3. **Confidence calibration and ensembles in LLMs**

- Recent work on “Effective Confidence Calibration and Ensembles in LLM‑Powered Classification” develops logit‑based confidence calibration, then uses calibrated scores to design cost‑aware cascading LLM ensembles. The focus is on single‑model calibration and cost‑efficient ensembling, not on consensus/entropy per se.[^17][^18]
- Industrial blogs and research on LLM reliability emphasize token‑probability‑based confidence and reflection methods but generally treat ensemble or multi‑agent methods as sources of extra evidence, not as an information‑theoretically framed agreement signal.[^19][^20][^21]

4. **Multi‑agent entropy / diversity**

- The “Multi‑Agent Approach to Estimating Black‑Box Model Uncertainty” with DiverseAgentEntropy does use weighted entropy over multiple agents’ answers as an uncertainty score and applies abstention when entropy is high. The agents are created from variations of a query to the same model; agreement among agents increases confidence.[^2]
- Conceptually, this is the closest mathematical cousin to your method, but it differs in several key ways:
    - It is single‑model, multi‑sample rather than a true multi‑LLM ensemble.
    - It still interprets entropy as an *uncertainty about correctness* proxy, not as a structural measure of “basin depth” that might be orthogonal to which answer is chosen and weakly correlated with voting‑based posteriors.

5. **Assessment of novelty for LLM ensemble confidence**

- There is clear precedent for:
    - Using multi‑LLM consensus rates and classical agreement metrics as reliability indicators.[^16]
    - Using information‑theoretic measures (JSD, entropy) over multiple models’ outputs or multiple samples as uncertainty signals.[^1][^2][^11]
- However, I do not see prior work with:
    - A **6‑model ensemble** of heterogeneous LLM “raters” and “arbitrators” on a subjective survey task,
    - An explicit **per‑item Shannon entropy** over their categorical votes used as an “agreement/convergence” score,
    - And an empirical demonstration that this entropy is nearly uncorrelated with vote‑count‑based Bayesian/Borda posteriors, supporting the claim that it captures a distinct structural attribute of the ensemble’s dynamics.
- Nor do I see previous work that explicitly links low entropy + strong agreement to “falling into a deep attractor basin” in an energy landscape for LLM‑generated classifications.

Within the constraints of current literature, that combination appears novel. Existing work can support your claims piecewise but not as a direct prior art for your full methodology.

***

## How I’d write this up (positioning)

For your paper/method description, I’d recommend:

- **Entropy as agreement**
    - Cite information‑theoretic inter‑rater agreement indices and ensemble‑diversity work to justify entropy/JSD as principled measures of agreement/disagreement among classifiers/raters.[^3][^8][^4]
    - Emphasize that, unlike most prior work, you:
        - apply entropy per item in a multi‑LLM ensemble,
        - on a subjective survey classification task,
        - and analyze its weak correlation with vote‑based aggregation scores, suggesting it captures a separate dimension of ensemble behavior.
- **Energy‑landscape framing**
    - Cite Hopfield, Boltzmann machines, and attractor‑network papers where energy landscapes and basins are formalized and associated with stable memories/decisions.[^5][^6][^12][^13][^7]
    - Then argue that observing multiple independently sampled LLMs converging to the same label is analogous to many trajectories falling into the same low‑energy basin; empirical entropy over ensemble votes acts as a proxy for basin depth or attractor stability.
- **LLM ensembles as confidence signals**
    - Cite multi‑LLM uncertainty (MUSE), multi‑agent entropy (DiverseAgentEntropy), and consensus‑based reliability work as showing that ensemble agreement and information‑theoretic disagreement can improve reliability and uncertainty estimation.[^16][^2][^11][^1]
    - Then distinguish your contribution as:
        - focusing on **subjective** tasks without clear ground truth,
        - using **heterogeneous** LLM raters + arbitrators,
        - and explicitly separating *what* the ensemble predicts from *how strongly* it converges, with entropy serving as this second axis.

Given what is currently visible in the literature, you can defensibly claim that using Shannon entropy over multi‑LLM ensemble votes as a **separate, attractor‑style agreement/convergence signal**—empirically orthogonal to vote‑count confidence—is a novel methodological contribution, albeit one grounded in well‑established information‑theoretic and energy‑based neural network ideas.
<span style="display:none">[^22][^23][^24][^25][^26][^27][^28][^29][^30]</span>

<div align="center">⁂</div>

[^1]: https://arxiv.org/abs/2507.07236

[^2]: https://arxiv.org/html/2412.09572v2

[^3]: https://onlinelibrary.wiley.com/doi/10.1155/2021/9953509

[^4]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7679268/

[^5]: https://en.wikipedia.org/wiki/Hopfield_network

[^6]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11573896/

[^7]: https://www.doc.ic.ac.uk/~ae/papers/julian.pdf

[^8]: https://ieeexplore.ieee.org/document/4721376/

[^9]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11643253/

[^10]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8863911/

[^11]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12702469/

[^12]: https://www.sciencedirect.com/science/article/pii/S089662732400802X

[^13]: https://www.doc.ic.ac.uk/~ae/papers/hopfield-networks.pdf

[^14]: https://www.cs.toronto.edu/~zemel/documents/lanNC.pdf

[^15]: https://elifesciences.org/reviewed-preprints/98725v1/figures

[^16]: https://arxiv.org/html/2411.16797v1

[^17]: https://www.amazon.science/publications/label-with-confidence-effective-confidence-calibration-and-ensembles-in-llm-powered-classification

[^18]: https://genai-ecommerce.github.io/assets/papers/GenAIECommerce2024/Genaiecom24_paper_17.pdf

[^19]: https://refuel.ai/blog-posts/labeling-with-confidence

[^20]: https://aclanthology.org/2025.trustnlp-main.26.pdf

[^21]: https://galileo.ai/blog/llm-reliability

[^22]: https://developer.nvidia.com/blog/entropy-based-methods-for-word-level-asr-confidence-estimation/

[^23]: https://subscription.packtpub.com/book/data/9781788624145/8/ch08lvl1sec57/interrating-agreement

[^24]: https://ui.adsabs.harvard.edu/abs/arXiv:1708.03496

[^25]: https://jmlr.org/papers/volume24/23-0041/23-0041.pdf

[^26]: https://openreview.net/forum?id=99K0EoKrCu

[^27]: https://www.lucykuncheva.co.uk/papers/shlkltif06.pdf

[^28]: https://www.techrxiv.org/users/907763/articles/1286087/master/file/data/energy/energy.pdf?inline=true

[^29]: https://repository.belmont.edu/surs/97/

[^30]: https://pubmed.ncbi.nlm.nih.gov/18188809/

