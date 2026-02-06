# LOW Confidence Pairs Review

**Generated**: 2026-01-30  
**Purpose**: Manual inspection of 28 pairs where arbitrators disagreed (three-way split or two-way disagreement without Google tiebreaker)

## Summary Statistics

- Total LOW confidence pairs: 28
- CPS pairs: 19
- FoodAPS pairs: 9
- All 28 are OA vs AN disagreements
- 7 pairs have Google data; Google sided with AN in 5/7 cases

## Disagreement Taxonomy

| OA calls | AN calls | Count |
|----------|----------|-------|
| CC | TC | 7 |
| CC | RS | 8 |
| CC | PC/MC | 4 |
| TC | RS | 1 |
| RS/NHB | NHB/TC | 3 |
| PM | CC/RS | 2 |
| MC | CC | 2 |
| Other | | 1 |

**Pattern**: OpenAI consistently assigns CC (Construct/Concept = fundamental incompatibility, F3) while Anthropic identifies specific barriers (TC=Temporal, RS=Response Scale) that may be addressable (F1/F2). This aligns with OpenAI's documented "optimism bias toward F3."

## Arbitrator Bias Summary (from Stage 3 Metrics, n=503 three-way)

**Position Bias** (chi-square vs 33.3% uniform, p<0.05):
- OpenAI: SIGNIFICANT (χ²=169.7, p=0.0) - 59.4% synthesis, A>B>C preference (48%/43%/9%)
- Anthropic: SIGNIFICANT (χ²=23.6, p=0.0) - 77.2% synthesis, A>B>C preference (42%/37%/22%)
- **Google: SIGNIFICANT - 7.0% synthesis, EXTREME A preference (82%/13%/4%)** ⚠️

**Family Bias** (same-vendor selection vs 33.3% expected):
- **OpenAI: SIGNIFICANT - 51.8% same-family rate (STRONG bias toward own rater)**
- Anthropic: NOT SIGNIFICANT - 36.8% same-family rate (neutral)
- **Google: SIGNIFICANT OPPOSITE - avoids own vendor**

**Interpretation**: Google's extreme primacy bias (82% selects position A) and OpenAI's family bias (51.8% selects own vendor's rater) are methodologically notable. Anthropic shows most neutral behavior. AN-GO has highest pairwise agreement (κ=0.887).

## Detailed Question-Level Analysis

| Pair | Q1 (Survey) | Q2 (ACS) | OA Verdict | AN Verdict | Assessment |
|------|-------------|----------|------------|------------|------------|
| **CPS_0000** | Names roster: "What are the names of all persons living or staying here?" | Count: "How many people are living or staying at this address?" | CC.2/F3 (construct) | RS.1/F1 (response scale) | **OA correct** - roster≠count; can count names but can't roster from count |
| **CPS_0004** | Probe: "Have I missed any babies or small children?" | Count: "How many people are living or staying at this address?" | CC.4/F3 (construct) | PC.3/F2 (population) | **OA correct** - completeness probe ≠ count |
| **CPS_0017** | "Hours per week USUALLY work at main job" | "Hours usually work per week at this rate" | CC.2/F2 | MC.3/F1 | **Ambiguous** - both have valid points |
| **CPS_0031** | "Hours per week at OTHER jobs" | "Past 12 months, weeks worked, hours usually work each week" | CC.4/F3 | TC.1/F2 | **Both valid** - scope AND temporal differ |
| **CPS_0047** | "Exact hours worked LAST WEEK" | "Past 12 months, weeks worked, hours usually work each week" | CC.2/F3 | TC.1/F2 | **AN correct** - both measure hours; temporal is primary barrier |
| **CPS_0105** | "Is job 35+ hours per week?" (binary) | "How many hours usually work per week?" (continuous) | CC.3/F1 | PC.1/F2 | **OA correct** - binary vs continuous is construct difference |
| **CPS_0216** | "Are you NOW in Armed Forces?" | "Has person EVER served on active duty?" | CC.1/F3 | TC.2/F2 | **AN correct** - both measure military service; temporal is primary |
| **FOODAPS_0140** | "Has NAME ever served?" (Y/N) | "WHEN did person serve?" | CC.2/F3 | RS.1/F1 | **OA correct** - can't derive "when" from "yes/no" |
| **FOODAPS_0165** | "What is NAME's relationship to you?" | "How is Person 2 related to Person 1?" | RS.3/F2 | PC.1/F1 | **Ambiguous** - reference person framing differs |
| **FOODAPS_0326** | "Hours normally work, including paid sick/leave time" | "Hours usually work per week at this rate" | MC.3/F2 | CC.4/F1 | **OA correct** - paid leave inclusion is operational difference |
| **FOODAPS_0330** | "Hours normally work, including paid sick/leave time" | "Best estimate of hours per week at this rate" | CC.4/F2 | MC.3/F1 | **Split** - both identify valid barriers |

## Interpretation

**Qualitative Assessment**:
- OA "wins" in ~5-6 cases (construct differences are genuine)
- AN "wins" in ~2-3 cases (temporal/response barriers are more precise)
- ~3-4 cases are genuinely ambiguous

**Pattern confirmed**: OpenAI sees broader construct incompatibilities; Anthropic sees specific technical barriers and is more optimistic about harmonization. Neither is systematically wrong—these are genuine edge cases where expert judgment varies.

**Recommendation**: Flag these 28 pairs as "requires expert review" in final deliverable rather than claiming definitive verdicts. The tiebreaker rule (OA default) is defensible for conservative analysis, but cases like CPS_0047 and CPS_0216 would benefit from AN's more precise temporal coding.

## Data Lineage

### Source Files
- Final verdicts: `output/analysis/final_verdicts.csv`
- Question pairs (CPS): `output/question_matching/cps/cps_candidate_pairs_all.csv`
- Question pairs (FoodAPS): `output/question_matching/foodaps/foodaps_candidate_pairs_all.csv`
- Arbitration results: `output/results/arbitration_v3_results_*.jsonl`

### Reproduction Scripts

```bash
# 1. Extract LOW confidence pairs with arbitrator verdicts
cd /Users/brock/Documents/GitHub/federal-survey-concept-mapper && \
python3 -c "
import pandas as pd
df = pd.read_csv('reports/03_harmonization_constraints/output/analysis/final_verdicts.csv')
low = df[df['confidence'] == 'LOW'][['pair_id', 'survey', 'final_L1', 'final_barrier_code', 'final_feasibility',
    'L1_oa', 'final_barrier_code_oa', 'final_feasibility_oa',
    'L1_an', 'final_barrier_code_an', 'final_feasibility_an', 
    'L1_go', 'final_barrier_code_go', 'final_feasibility_go']]
print(f'LOW confidence pairs: {len(low)}')
print(low.to_string(index=False))
"

# 2. Get question text for LOW confidence pairs
cd /Users/brock/Documents/GitHub/federal-survey-concept-mapper && \
python3 -c "
import pandas as pd
cps = pd.read_csv('output/question_matching/cps/cps_candidate_pairs_all.csv')
food = pd.read_csv('output/question_matching/foodaps/foodaps_candidate_pairs_all.csv')
pairs = pd.concat([cps, food])

low_ids = ['CPS_0000','CPS_0004','CPS_0017','CPS_0031','CPS_0047','CPS_0105','CPS_0216',
           'FOODAPS_0140','FOODAPS_0165','FOODAPS_0326','FOODAPS_0330']

for pid in low_ids:
    row = pairs[pairs['pair_id']==pid]
    if len(row) > 0:
        r = row.iloc[0]
        print(f'=== {pid} ===')
        print(f'Q1: {r[\"survey_text\"][:150]}')
        print(f'Q2: {r[\"acs_text\"][:150]}')
        print()
"

# 3. Full extraction of all 28 LOW pairs with question text
cd /Users/brock/Documents/GitHub/federal-survey-concept-mapper && \
python3 << 'EOF'
import pandas as pd

# Load verdicts
verdicts = pd.read_csv('reports/03_harmonization_constraints/output/analysis/final_verdicts.csv')
low = verdicts[verdicts['confidence'] == 'LOW']

# Load question pairs
cps = pd.read_csv('output/question_matching/cps/cps_candidate_pairs_all.csv')
food = pd.read_csv('output/question_matching/foodaps/foodaps_candidate_pairs_all.csv')
pairs = pd.concat([cps, food])

# Merge
merged = low.merge(pairs[['pair_id', 'survey_text', 'acs_text']], on='pair_id', how='left')

# Output
cols = ['pair_id', 'survey', 'survey_text', 'acs_text', 
        'final_barrier_code', 'final_feasibility',
        'final_barrier_code_oa', 'final_feasibility_oa',
        'final_barrier_code_an', 'final_feasibility_an',
        'final_barrier_code_go', 'final_feasibility_go']
merged[cols].to_csv('reports/03_harmonization_constraints/output/analysis/low_confidence_pairs_detail.csv', index=False)
print(f'Saved {len(merged)} pairs to low_confidence_pairs_detail.csv')
EOF
```
