# Inter-Rater Reliability Citations

**Document ID:** `LIT-R03-IRR-001`  
**Created:** 2025-01-30  
**Purpose:** Citations supporting Stage 2 agreement analysis methodology

---

## Primary Methodological References

### Threshold Standards

**McHugh, M. L. (2012)**  
*Interrater reliability: the kappa statistic*  
Biochemia Medica, 22(3), 276-282.  
https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/

> Key citation for using κ ≥ 0.80 threshold in health-related research. McHugh argues Cohen's traditional interpretation (0.41 = moderate) is "too lenient for health related studies."

**Landis, J. R., & Koch, G. G. (1977)**  
*The measurement of observer agreement for categorical data*  
Biometrics, 33(1), 159-174.

> Classic interpretation scale:
> - κ < 0.00 = Poor
> - κ 0.00–0.20 = Slight  
> - κ 0.21–0.40 = Fair
> - κ 0.41–0.60 = Moderate
> - κ 0.61–0.80 = Substantial
> - κ 0.81–1.00 = Almost Perfect

---

### Krippendorff's Alpha

**Krippendorff, K. (2004)**  
*Content Analysis: An Introduction to Its Methodology* (2nd ed.)  
Sage Publications.

> Foundational reference. Threshold guidance (p. 241):
> - α ≥ 0.80 = Reliable for substantive conclusions
> - 0.67 ≤ α < 0.80 = Tentative conclusions only
> - α < 0.67 = Insufficient reliability

**Hayes, A. F., & Krippendorff, K. (2007)**  
*Answering the call for a standard reliability measure for coding data*  
Communication Methods and Measures, 1(1), 77-89.

> Methodological paper on Krippendorff's alpha computation.

**Zapf, A., Castell, S., Mober, L., & Kreienbrock, L. (2016)**  
*Measuring inter-rater reliability for nominal data – which coefficients and confidence intervals are appropriate?*  
BMC Medical Research Methodology, 16, 93.  
https://pmc.ncbi.nlm.nih.gov/articles/PMC4974794/

> Simulation study comparing Fleiss' kappa and Krippendorff's alpha. Key finding: "Point estimates of Fleiss' K and Krippendorff's alpha did not differ from each other in all scenarios."

---

### Prevalence and Bias Effects

**Hallgren, K. A. (2012)**  
*Computing inter-rater reliability for observational data: An overview and tutorial*  
Tutorials in Quantitative Methods for Psychology, 8(1), 23-34.  
https://pmc.ncbi.nlm.nih.gov/articles/PMC3402032/

> Key methodological paper on IRR computation. Documents:
> - **Prevalence problem**: When one category dominates (our CC at 80%), kappa underestimates true agreement
> - **Bias problem**: When raters have different marginal distributions
> - Recommends reporting both % agreement AND kappa

**Byrt, T., Bishop, J., & Carlin, J. B. (1993)**  
*Bias, prevalence and kappa*  
Journal of Clinical Epidemiology, 46(5), 423-429.

> Introduces PABAK (Prevalence-Adjusted Bias-Adjusted Kappa).

---

### Fleiss' Kappa (Multi-Rater)

**Fleiss, J. L. (1971)**  
*Measuring nominal scale agreement among many raters*  
Psychological Bulletin, 76(5), 378-382.

> Extension of kappa for 3+ raters.

---

### Cohen's Kappa (Original)

**Cohen, J. (1960)**  
*A coefficient of agreement for nominal scales*  
Educational and Psychological Measurement, 20(1), 37-46.

> Original kappa paper for two raters.

---

## Application Notes

### Our Threshold Justification

We use **κ ≥ 0.80** as primary quality gate because:
1. McHugh (2012) recommends stricter thresholds for consequential research
2. Krippendorff (2004) uses 0.80 as "reliable for substantive conclusions"
3. Consistent with health research standards

### Interpretation Layers

| Threshold | Landis & Koch | Krippendorff | McHugh | Our Use |
|-----------|---------------|--------------|--------|---------|
| ≥ 0.80 | Almost Perfect | Reliable | Acceptable | **Quality Gate** |
| 0.61–0.79 | Substantial | Tentative | Cautious | Flag for Review |
| 0.41–0.60 | Moderate | Insufficient | Unacceptable | Requires Revision |
| < 0.41 | Fair/Slight | Insufficient | Unacceptable | Reject |

### Prevalence Adjustment

Given CC category prevalence at ~80%, we report:
1. Raw % agreement (for transparency)
2. Cohen's/Fleiss' kappa (standard)
3. Krippendorff's alpha (robustness check)
4. Category-specific kappas (to identify difficult categories)

---

## URLs for PDF Collection

- Hallgren (2012): https://pmc.ncbi.nlm.nih.gov/articles/PMC3402032/
- McHugh (2012): https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/
- Zapf et al. (2016): https://pmc.ncbi.nlm.nih.gov/articles/PMC4974794/
- De Swert (2012): https://www.polcomm.org/wp-content/uploads/ICR01022012.pdf
