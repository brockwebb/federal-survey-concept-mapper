# Example Question Pairs for Presentation

**Generated:** 2026-02-02
**Purpose:** Slide deck examples showing consolidation spectrum

---

# HIGH CONSOLIDABILITY (F1)

Direct mapping - questions can be consolidated without transformation.

## HIGH CONSOLIDABILITY: CPS_105 → ACS_12

**Source Question (CPS):**
> How many hours per week (do/does) (name/you) USUALLY work at (your/his/her) (job?/ main job?)

**ACS Match:**
> What is your best estimate of the number of hours per week you usually work at this rate?

**Verdict:** F1
**Barrier Code:** N/A
**Scores:** Borda = 1.000, Entropy = 1.000
**Triage:** Q1

**LLM Reasoning:**
> All three raters coded RS.3 (Anchoring/labels) with F1 feasibility, citing minor wording differences like 'best estimate' vs direct question format. However, upon closer examination, both questions ask for the same numeric response (hours per week usually worked), and the differences are purely s...

---

## HIGH CONSOLIDABILITY: CPS_107 → ACS_6

**Source Question (CPS):**
> (Do / Does) (you/he/she) usually work 35 hours or more per week (at (your/his/her) job/in the family business/ at all (y

**ACS Match:**
> How many hours do you usually work per week at this rate?

**Verdict:** F1
**Barrier Code:** N/A
**Scores:** Borda = 1.000, Entropy = 1.000
**Triage:** Q1

**LLM Reasoning:**
> All three raters unanimously agree on RS.1 (scale type difference) with F1 feasibility. The CPS question uses a binary threshold format (yes/no for 35+ hours) while the ACS question collects continuous numeric hours. This is a clear response scale type difference. The harmonization is feasible vi...

---

## HIGH CONSOLIDABILITY: FOODAPS_287 → ACS_1

**Source Question (FOODAPS):**
> What is the easiest way for you to tell us about NAME’s earnings from work before taxes and other deductions?

**ACS Match:**
> For your [main] job, what is the easiest way for you to report your total earnings BEFORE taxes or other deductions: hou

**Verdict:** F1
**Barrier Code:** N/A
**Scores:** Borda = 1.000, Entropy = 1.000
**Triage:** Q1

**LLM Reasoning:**
> All three raters agree on F1 feasibility and recognize the questions are near-duplicates in substantive content. The key differences are: (1) FOODAPS asks about 'NAME's earnings from work' (any job, proxy-capable), while ACS asks about 'your main job' (self-report, main job only). The primary con...

---

## HIGH CONSOLIDABILITY: FOODAPS_214 → ACS_1

**Source Question (FOODAPS):**
> What is the easiest way for you to tell us about your earnings from work before taxes and other deductions?

**ACS Match:**
> For your [main] job, what is the easiest way for you to report your total earnings BEFORE taxes or other deductions: hou

**Verdict:** F1
**Barrier Code:** N/A
**Scores:** Borda = 1.000, Entropy = 1.000
**Triage:** Q1

**LLM Reasoning:**
> All three raters agree on F1 feasibility and recognize the questions are nearly identical in purpose and format. The key difference is whether the 'main job' specification in ACS versus general 'earnings from work' in FOODAPS constitutes a meaningful barrier. Rater A codes PC.1 (universe definiti...

---

## HIGH CONSOLIDABILITY: FOODAPS_184 → ACS_103

**Source Question (FOODAPS):**
> Last week, did you do any work for either pay or profit? 

**ACS Match:**
> LAST WEEK, did this person do ANY work for pay, even for as little as one hour?

**Verdict:** F1
**Barrier Code:** N/A
**Scores:** Borda = 1.000, Entropy = 1.000
**Triage:** Q1

**LLM Reasoning:**
> All three raters agree on F1 feasibility, indicating direct recoding is possible. The differences between the questions are minimal: (1) 'pay or profit' vs 'pay' - profit is typically considered a form of pay/compensation for self-employed work, (2) the ACS includes an explicit threshold 'as litt...

---


# MEDIUM CONSOLIDABILITY (F2)

Consolidable with transformation - questions map with adjustments.

## MEDIUM CONSOLIDABILITY: FOODAPS_63 → ACS_15

**Source Question (FOODAPS):**
> Last week, was NAME enrolled in school as a full-time or part-time student, or was NAME not enrolled in school?

**ACS Match:**
> Are you enrolled in school as a full-time or part-time student?

**Verdict:** F2
**Barrier Code:** N/A
**Scores:** Borda = 0.700, Entropy = 0.260
**Triage:** Q3

**LLM Reasoning:**
> All three raters agree the primary barrier is temporal in nature. Raters A and B both coded TC.1 (reference period length), while Rater C coded TC.2 (temporal framing). The key distinction is whether this is a reference period length difference (TC.1) or a framing difference (TC.2). The FOODAPS q...

---

## MEDIUM CONSOLIDABILITY: FOODAPS_33 → ACS_14

**Source Question (FOODAPS):**
> This week and next week are you attending classes for: (1)Middle/junior  high school (2) High School (3) Homeschool (4) 

**ACS Match:**
> Would that be high school, college, or university?

**Verdict:** F2
**Barrier Code:** N/A
**Scores:** Borda = 0.700, Entropy = 0.260
**Triage:** Q3

**LLM Reasoning:**
> All three raters identify that the response categories differ between the two questions. Rater A codes CC.4 (scope inclusions), Rater B codes RS.1 (scale type), and Rater C codes RS.2 (category structure). The core issue is that FoodAPS includes middle school, homeschool, and 'other school' as ex...

---

## MEDIUM CONSOLIDABILITY: CPS_174 → ACS_113

**Source Question (CPS):**
> (THE WEEK BEFORE LAST/LAST WEEK), could (you/he/she) have started a job IF one had been offered?

**ACS Match:**
> LAST WEEK, could this person have started a job if offered one, or returned to work if recalled?

**Verdict:** F2
**Barrier Code:** N/A
**Scores:** Borda = 0.667, Entropy = 0.282
**Triage:** Q3

**LLM Reasoning:**
> While all raters identify temporal differences (CPS uses 'week before last/last week' vs ACS's fixed 'last week'), the more substantive barrier is the scope difference: ACS explicitly includes 'or returned to work if recalled' which expands the construct beyond just starting a new job. This is a ...

---

## MEDIUM CONSOLIDABILITY: CPS_284 → ACS_4

**Source Question (CPS):**
> (EXCLUDING overtime pay, tips and commissions) what is (your/his/her) hourly rate of pay on (this job/ (your/his/her) MA

**ACS Match:**
> What is your hourly rate of pay on [this/ your main] job?

**Verdict:** F2
**Barrier Code:** N/A
**Scores:** Borda = 0.600, Entropy = 0.365
**Triage:** Q1

**LLM Reasoning:**
> Two raters (A and C) agree on CC.4 with F2 feasibility, while Rater B coded CC.3 with F1. The key distinction is whether this is a boundary/threshold issue (CC.3) or a scope/components issue (CC.4). The CPS question explicitly excludes overtime pay, tips, and commissions - these are specific pay ...

---

## MEDIUM CONSOLIDABILITY: FOODAPS_96 → ACS_54

**Source Question (FOODAPS):**
> On what date did [you/you and names of SNAP group 1 from B1ba ] last receive [FILL IN STATE SNAP NAME] benefits?

**ACS Match:**
> IN THE PAST 12 MONTHS, did you or any member of this household receive benefits from the Food Stamp Program or SNAP (the

**Verdict:** F2
**Barrier Code:** N/A
**Scores:** Borda = 0.600, Entropy = 0.365
**Triage:** Q1

**LLM Reasoning:**
> Two raters (A and C) agree on TC.1 with F2 feasibility, while Rater B coded RS.1 with F1. The core issue is temporal: FOODAPS asks for a specific date of last receipt while ACS asks about receipt within a 12-month window. While there is technically a response scale difference (date vs. binary), t...

---


# LOW/NO CONSOLIDABILITY (F3)

Not consolidable - fundamental construct mismatch.

## LOW CONSOLIDABILITY: CPS_102 → ACS_1

**Source Question (CPS):**
> (Are / Is) ( you/he/she) being paid by (your/his/her) employer for any of the time off (the week before last/last week)?

**ACS Match:**
> For your [main] job, what is the easiest way for you to report your total earnings BEFORE taxes or other deductions: hou

**Verdict:** F3
**Barrier Code:** CC.1
**Scores:** Borda = 0.000, Entropy = 0.330
**Triage:** Q2

**LLM Reasoning:**
> All three raters unanimously agree on CC.1 (Concept definition) with F3 (Incompatible) feasibility. Their reasoning is consistent and correct: the CPS question asks about whether the respondent received paid leave from their employer during time off, which measures a compensation/benefit construc...

---

## LOW CONSOLIDABILITY: CPS_108 → ACS_102

**Source Question (CPS):**
> (Do / Does) (name/you) want to work a full time workweek of 35 hours or more per week?

**ACS Match:**
> LAST WEEK, did this person work for pay at a job (or business)?

**Verdict:** F3
**Barrier Code:** CC.1
**Scores:** Borda = 0.000, Entropy = 0.330
**Triage:** Q2

**LLM Reasoning:**
> All three raters unanimously agree on CC.1 (Concept definition) with F3 (Incompatible) feasibility. Their reasoning is consistent and correct: the CPS question measures a subjective preference/desire about wanting to work full-time hours (35+ hours per week), while the ACS question measures an ob...

---

## LOW CONSOLIDABILITY: CPS_109 → ACS_102

**Source Question (CPS):**
> Some people work part time because they cannot find full time work or because business is poor. Others work part time be

**ACS Match:**
> LAST WEEK, did this person work for pay at a job (or business)?

**Verdict:** F3
**Barrier Code:** CC.1
**Scores:** Borda = 0.000, Entropy = 0.330
**Triage:** Q2

**LLM Reasoning:**
> All three raters unanimously agree on CC.1 (Concept definition) with F3 (Incompatible) feasibility. The CPS question asks about the REASON for working part-time (a motivational/causal construct targeting only part-time workers), while the ACS question asks whether the person worked for pay last w...

---

## LOW CONSOLIDABILITY: CPS_110 → ACS_102

**Source Question (CPS):**
> What is the main reason (you/he/she) (do/does) not want to work full time?

**ACS Match:**
> LAST WEEK, did this person work for pay at a job (or business)?

**Verdict:** F3
**Barrier Code:** CC.1
**Scores:** Borda = 0.000, Entropy = 0.330
**Triage:** Q2

**LLM Reasoning:**
> All three raters unanimously agree on CC.1 (Construct - Concept definition) with F3 (Incompatible) feasibility. Their reasoning is consistent and compelling: the CPS question measures motivations/reasons for not wanting full-time work (an attitudinal/explanatory construct), while the ACS question...

---

## LOW CONSOLIDABILITY: CPS_112 → ACS_6

**Source Question (CPS):**
> How many hours did (name/you) take off?

**ACS Match:**
> How many hours do you usually work per week at this rate?

**Verdict:** F3
**Barrier Code:** CC.2
**Scores:** Borda = 0.000, Entropy = 0.330
**Triage:** Q2

**LLM Reasoning:**
> All three raters agree on F3 (incompatible) and identify this as a construct-level barrier. The key distinction is between CC.1 (concept definition) and CC.2 (operationalization). Raters A and C chose CC.2, while Rater B chose CC.1. The fundamental issue here is that these questions measure entir...

---

