# TEVV Evidence: v1-vs-v2 Prompt Equivalence

Generated: 2026-06-03T16:08:36.666857+00:00

This report is produced by `v2/src/tevv/prompt_equivalence.py`. It mechanically diffs the rendered v1 and v2 prompts for each registered pipeline stage and checks every divergence against the acknowledged-divergence allowlist (`v2/config/prompt_divergences.yaml`). It calls no model; the diff is a static-text property.

Why it matters: the v2 confirmation run is a reproducibility study. A v1-vs-v2 disagreement is only a clean MODEL finding if the rendered prompt was the same question across versions. Unacknowledged divergence means the comparison is confounded.

## stage3 -- Harmonization barrier coding rater prompt

- verified pair: True
- divergences found: 21
- unacknowledged: 0
- verdict: **ACKNOWLEDGED_DIVERGENCE**

| dimension | signature | what changed | ack | directional bias (human annotation) |
|---|---|---|---|---|
| taxonomy_block | `taxonomy_block_text_differs` | Taxonomy instructional block is not byte-identical. codes added in v2: ['NHB']; codes removed in v2: none. | yes | See codes_added:NHB (toward F3 at margin). PROVISIONAL. |
| available_codes | `codes_added:CC` | v2 makes code 'CC' available that v1 did not. | yes | See schema_fields_added:classification (toward CC). PROVISIONAL. |
| available_codes | `codes_added:MC` | v2 makes code 'MC' available that v1 did not. | yes | See schema_fields_added:classification (toward CC). PROVISIONAL. |
| available_codes | `codes_added:NHB` | v2 makes code 'NHB' available that v1 did not. | yes | PROVISIONAL. Adding a dedicated no-barrier sink at the bottom of the feasibility range drains the "weak barrier but still harmonizable" cases out of F1/F2, leaving F1/F2 sparser and pushing genuinely hard pairs toward F3. Expected to inflate F3 share relative to v1 and to depress a v1-vs-v2 feasibility kappa simply because v1 used a 3-bucket scale and v2 a 4-bucket scale. Direction: toward F3 at the margin. |
| available_codes | `codes_added:PC` | v2 makes code 'PC' available that v1 did not. | yes | See schema_fields_added:classification (toward CC). PROVISIONAL. |
| available_codes | `codes_added:PM` | v2 makes code 'PM' available that v1 did not. | yes | See schema_fields_added:classification (toward CC). PROVISIONAL. |
| available_codes | `codes_added:RS` | v2 makes code 'RS' available that v1 did not. | yes | See schema_fields_added:classification (toward CC). PROVISIONAL. |
| available_codes | `codes_added:TC` | v2 makes code 'TC' available that v1 did not. | yes | See schema_fields_added:classification (toward CC). PROVISIONAL. |
| output_schema | `schema_fields_added:classification` | v2 output schema adds field 'classification' that v1 lacked. | yes | PROVISIONAL. Forcing a top-level bucket commitment before the subtype may anchor the model on the broadest defensible L1 (CC, whose definition "concept definition or operationalization differences" absorbs most cases) before it reasons to a specific subtype. Hypothesized to favor CC. Direction: toward CC. This is a hypothesis about ordering effects, not a measured fact. |
| output_schema | `schema_fields_added:confidence` | v2 output schema adds field 'confidence' that v1 lacked. | yes | PROVISIONAL. Metadata about the rating, not an input to choosing the code. Used downstream to gate a high-confidence gold set, not to select the barrier. Direction: none expected on the barrier-label distribution. |
| output_schema | `schema_fields_added:consolidation_potential` | v2 output schema adds field 'consolidation_potential' that v1 lacked. | yes | PROVISIONAL. Orthogonal to the barrier label; captures a downstream enrichment signal rather than the harmonization barrier. Direction: none expected on the barrier code. |
| output_schema | `schema_fields_added:reference_period_a` | v2 output schema adds field 'reference_period_a' that v1 lacked. | yes | PROVISIONAL. Foregrounding reference periods could prime TC (temporal) classifications relative to v1, which never asked for them. NOTE: this points toward TC, the OPPOSITE direction from the CC-attractor the other divergences predict. Flag for Brock: net effect is unmeasured and could partially offset the CC pull. Hypothesis only. |
| output_schema | `schema_fields_added:reference_period_b` | v2 output schema adds field 'reference_period_b' that v1 lacked. | yes | PROVISIONAL. See reference_period_a: possibly toward TC at the margin, the opposite direction from the CC-attractor. Unmeasured. Flag for Brock. |
| output_schema | `schema_fields_removed:additional_barriers` | v2 output schema drops field 'additional_barriers' that v1 had. | yes | PROVISIONAL. With no outlet for a secondary barrier, a pair that has both (say) a temporal and a construct difference must collapse to one code in v2, whereas v1 could record TC.1 primary + CC.2 additional. When forced to pick one, the broader category (CC) is the safer choice, so the collapse is hypothesized to move mass toward CC. Direction: toward CC. |
| output_schema | `schema_fields_removed:specific_conflict` | v2 output schema drops field 'specific_conflict' that v1 had. | yes | PROVISIONAL. Free-text descriptive field, not a coded outlet. Its removal is not expected to move the barrier-label distribution (unlike the dropped additional_barriers field, which WAS a coded secondary outlet). Direction: none expected. |
| task_framing | `framing:additional_barriers_outlet` | Framing probe 'additional_barriers_outlet' differs: v1=True, v2=False. | yes | See schema_fields_removed:additional_barriers (toward CC). PROVISIONAL. |
| task_framing | `framing:batched_multi_pair` | Framing probe 'batched_multi_pair' differs: v1=True, v2=False. | yes | See framing:single_barrier_mandate (isolation favors general bucket). PROVISIONAL. |
| task_framing | `framing:main_constraint_phrasing` | Framing probe 'main_constraint_phrasing' differs: v1=True, v2=False. | yes | See framing:single_barrier_mandate (toward CC). PROVISIONAL. |
| task_framing | `framing:nhb_offered` | Framing probe 'nhb_offered' differs: v1=False, v2=True. | yes | See codes_added:NHB (toward F3 at margin). PROVISIONAL. |
| task_framing | `framing:single_barrier_mandate` | Framing probe 'single_barrier_mandate' differs: v1=False, v2=True. | yes | PROVISIONAL. Two effects, same direction. (a) "SINGLE" wording plus the dropped additional_barriers field removes the secondary outlet (see above). (b) Coding one pair in isolation removes the cross-pair contrast a batch provides; with no neighbors to differentiate against, the model is hypothesized to reach for the most general explanation (CC). Believed to be the largest single contributor to the v2 CC-attractor. Direction: toward CC. Magnitude unmeasured. |
| task_framing | `framing:single_pair_object` | Framing probe 'single_pair_object' differs: v1=False, v2=True. | yes | See framing:single_barrier_mandate. PROVISIONAL. |

## stage1 -- Topic/subtopic classification prompt. v1 categorize_claude.py:create_prompt is BYTE-IDENTICAL to v2 stage1_classify.py:create_prompt (static read). Not runtime-rendered: v1 module is import-unsafe (runs its pipeline at import, no __main__ guard).

- verified pair: False
- divergences found: 0
- unacknowledged: 0
- verdict: **UNVERIFIED (not imported)**

## stage2 -- Classification (topic) arbitration prompt. v1 arbitrate_final.py:create_arbitration_prompt <-> v2 stage2_adjudicate.py:create_arbitration_prompt (same signature, both import-safe). Not verified: this gate's extractors are tuned to the Stage 3 barrier-prompt shape and would rubber-stamp these classification prompts EQUIVALENT. Needs classification-aware probes.

- verified pair: False
- divergences found: 0
- unacknowledged: 0
- verdict: **UNVERIFIED (not imported)**

## Unverified pairs (registered, not asserted)

These stages are registered targets the gate does NOT runtime-verify. They do NOT count toward a green gate. Each line states its specific reason: a source may be confirmed yet still unverified because the v1 module is import-unsafe or because the gate's extractors do not yet fit that prompt shape. Closing these is documented follow-up work.

- stage1: Topic/subtopic classification prompt. v1 categorize_claude.py:create_prompt is BYTE-IDENTICAL to v2 stage1_classify.py:create_prompt (static read). Not runtime-rendered: v1 module is import-unsafe (runs its pipeline at import, no __main__ guard).
- stage2: Classification (topic) arbitration prompt. v1 arbitrate_final.py:create_arbitration_prompt <-> v2 stage2_adjudicate.py:create_arbitration_prompt (same signature, both import-safe). Not verified: this gate's extractors are tuned to the Stage 3 barrier-prompt shape and would rubber-stamp these classification prompts EQUIVALENT. Needs classification-aware probes.
