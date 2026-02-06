# Decision: Fix Stage 4 Hardcoded Values

**Date:** 2026-02-04
**Status:** Implemented
**Tags:** technical-debt, stage4, pipeline

## Problem

Stage4 model validation visuals script had hardcoded values despite JSON data existing.

## Root Cause

Incorrect TODO comments claimed data didn't exist:
- "TODO: Add pairwise rater kappas to stage2 metrics" - DATA EXISTS
- "TODO: Add single-model divergence to stage2/stage3 metrics" - DATA EXISTS

## Solution

1. Added `extract_rater_kappas(stage2)` function
2. Added `extract_single_model_risk(stage2)` function
3. Removed hardcoded values and TODO comments
4. Registered pipeline artifacts in trace system

## Lesson Learned

**Always verify JSON structure before claiming data is missing.**

The previous developer did not fully explore the stage2 JSON structure, missing:
- `stage2['L1_agreement']['overall']['pairwise']` - pairwise kappas
- `stage2['extended_analytics']['multimodel_value']['single_model_risk']` - divergence data

## Impact

- Stage4 now reads ALL data from JSON
- Pipeline reruns produce consistent outputs
- No manual sync required between stages
