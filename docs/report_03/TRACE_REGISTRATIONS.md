# Trace Artifact Registrations for Stage4 Fix

**Date:** 2026-02-04
**Related Decision:** DD_STAGE4_HARDCODED_FIX.md

## Purpose

Register the Report 03 pipeline scripts and data outputs in the trace system to document data dependencies fixed by removing hardcoded values.

## Required Registrations

### Pipeline Scripts (type: module)

```python
# Stage 4 visuals script (now reads from JSON)
add_artifact(
    artifact_id="reports/03_harmonization_constraints/scripts/stage4_model_validation_visuals.py",
    artifact_type="module",
    file_path="reports/03_harmonization_constraints/scripts/stage4_model_validation_visuals.py",
    tags=["pipeline", "stage4", "visuals"]
)

# Stage 3 arbitration script (produces metrics)
add_artifact(
    artifact_id="reports/03_harmonization_constraints/scripts/04_stage3_arbitration.py",
    artifact_type="module",
    file_path="reports/03_harmonization_constraints/scripts/04_stage3_arbitration.py",
    tags=["pipeline", "stage3", "arbitration"]
)

# Stage 2 agreement script (produces metrics)
add_artifact(
    artifact_id="reports/03_harmonization_constraints/03_stage2_agreement.py",
    artifact_type="module",
    file_path="reports/03_harmonization_constraints/03_stage2_agreement.py",
    tags=["pipeline", "stage2", "agreement"]
)
```

### Data Outputs (type: data)

```python
# Stage 2 metrics (source of rater kappas and single-model risk)
add_artifact(
    artifact_id="reports/03_harmonization_constraints/output/analysis/stage2_agreement_metrics.json",
    artifact_type="data",
    file_path="reports/03_harmonization_constraints/output/analysis/stage2_agreement_metrics.json",
    tags=["output", "stage2", "metrics"]
)

# Stage 3 metrics (source of arbitrator kappas and synthesis rates)
add_artifact(
    artifact_id="reports/03_harmonization_constraints/output/analysis/stage3_arbitration_metrics.json",
    artifact_type="data",
    file_path="reports/03_harmonization_constraints/output/analysis/stage3_arbitration_metrics.json",
    tags=["output", "stage3", "metrics"]
)
```

## Dependency Links

### Critical Dependencies (Stage4 reads from Stage2/3)

```python
# Stage4 depends on Stage2 metrics
propose_link(
    source_id="reports/03_harmonization_constraints/scripts/stage4_model_validation_visuals.py",
    target_id="reports/03_harmonization_constraints/output/analysis/stage2_agreement_metrics.json",
    relationship_type="depends_on",
    rationale="Stage4 visuals reads rater kappas (L1_agreement.overall.pairwise) and single-model risk (extended_analytics.multimodel_value.single_model_risk) from stage2 metrics"
)

# Stage4 depends on Stage3 metrics
propose_link(
    source_id="reports/03_harmonization_constraints/scripts/stage4_model_validation_visuals.py",
    target_id="reports/03_harmonization_constraints/output/analysis/stage3_arbitration_metrics.json",
    relationship_type="depends_on",
    rationale="Stage4 visuals reads arbitrator kappas (three_way_agreement.L1_pairwise), synthesis rates (synthesis_detection), and family bias (family_bias) from stage3 metrics"
)
```

### Producer Relationships

```python
# Stage2 script produces stage2 metrics
propose_link(
    source_id="reports/03_harmonization_constraints/03_stage2_agreement.py",
    target_id="reports/03_harmonization_constraints/output/analysis/stage2_agreement_metrics.json",
    relationship_type="implements",
    rationale="Stage2 script produces agreement metrics JSON output with rater kappas and multimodel value analysis"
)

# Stage3 script produces stage3 metrics
propose_link(
    source_id="reports/03_harmonization_constraints/scripts/04_stage3_arbitration.py",
    target_id="reports/03_harmonization_constraints/output/analysis/stage3_arbitration_metrics.json",
    relationship_type="implements",
    rationale="Stage3 script produces arbitration metrics JSON output with arbitrator kappas, synthesis rates, and family bias analysis"
)
```

## Execution Instructions

Run these commands using the trace MCP server:

```bash
# From repository root with trace MCP server available
# Each add_artifact and propose_link command should be executed
# The trace system will append to .trace/events.jsonl
```

## Validation

After registration, verify with:

```python
# Check artifacts exist
list_artifacts(tags=["stage4"])
list_artifacts(tags=["stage2"])

# Check dependency chain
get_downstream("reports/03_harmonization_constraints/output/analysis/stage2_agreement_metrics.json")
# Should include stage4_model_validation_visuals.py
```

## Notes

- This registration documents the data flow that was previously hidden by hardcoded values
- Future pipeline changes should maintain these documented dependencies
- If stage2/stage3 JSON schemas change, stage4 extraction functions must be updated accordingly
