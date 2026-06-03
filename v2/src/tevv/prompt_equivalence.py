#!/usr/bin/env python3
"""TEVV prompt-equivalence gate for v-over-v reproducibility claims.

WHY THIS EXISTS
---------------
The v2 confirmation run is a REPRODUCIBILITY STUDY: re-run v1's logic on new
infrastructure with different models and check that the findings survive. That
claim is only valid if the QUESTION asked of the v2 models is the same QUESTION
v1 asked. If v2's prompt diverged from v1's, then a v1-vs-v2 disagreement is
confounded -- part model difference, part prompt difference -- and cannot be
reported cleanly as a model-reproducibility result.

The existing `_smoke.py` gate validates ROUND-TRIP INTEGRITY (did every record
we asked for get written and read back). It does NOT validate PROMPT FIDELITY
(is the rendered prompt the same question across versions). Round-trip smoke
catches "a pair vanished"; it cannot catch "we asked a subtly different
question." For a reproducibility study, prompt fidelity is the thing under
test, and until now it was assumed rather than checked.

This module mechanically diffs the RENDERED prompt text of a v1 builder against
a v2 builder, across four structural dimensions, and fails if any divergence is
not explicitly acknowledged in a checked-in allowlist. Acknowledged divergences
become documented design decisions with a written justification; new ones fail
loudly. This is the prompt-fidelity analogue of the source-SHA smoke stamp.

WHAT IT MEASURES (mechanical, no interpretation)
------------------------------------------------
  1. taxonomy_block   -- the shared instructional block, byte-for-byte.
  2. available_codes  -- the set of classification/feasibility codes the
                         prompt makes available (e.g. v2 adds NHB).
  3. output_schema    -- the set of fields the prompt asks the model to return
                         (e.g. v2 adds `classification`, drops
                         `additional_barriers`).
  4. task_framing     -- normalized instruction phrasing (batched-vs-single,
                         "main constraint" vs "SINGLE primary barrier").

The script reports each divergence with WHERE it is and WHAT changed. It does
NOT assert WHY the change biases results -- a directional-bias claim
(e.g. "isolation favors the most general bucket") is an interpretation, not a
measurement, and lives in the allowlist YAML as a human-authored
`justification` / `directional_bias` field. Baking an interpretation into a
validation script as if it were a measured fact is exactly the failure the
project's "validation scripts are the single source of truth for numbers"
principle forbids. The script measures text; humans annotate meaning.

WHAT IT DOES NOT DO
-------------------
  * It does NOT call any model. Prompt equivalence is a static-text property of
    the rendered string. Re-rating to "prove" a bias would burn API budget and
    conflate two questions. The diff stands on rendered text alone.
  * It does NOT edit any tracked file. It reads builders + the allowlist and
    writes evidence to docs/stages/tevv/. (The allowlist is authored by a human
    via a CC task, not mutated here.)

USAGE
-----
Run from v2/:

    python src/tevv/prompt_equivalence.py            # gate all registered pairs
    python src/tevv/prompt_equivalence.py --report   # write MD + JSON evidence
    python src/tevv/prompt_equivalence.py --stage stage3   # one pair only
    python src/tevv/prompt_equivalence.py --list     # show registered pairs

Exit codes:
    0  all VERIFIED pairs equivalent or every divergence acknowledged
    2  an unacknowledged divergence exists (the gate's FAIL)
    1  a configuration/IO FATAL (missing builder, malformed allowlist, etc.)
    4  no pair could be evaluated (every registered pair was UNVERIFIED)

The exit-code split mirrors _smoke.py: 1 = environment/contract FATAL,
2 = the substantive gate failure, and a dedicated code (4) for "nothing to
check," so a green run cannot be faked by registering only unverified pairs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FATAL: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# CONSTANTS / EXIT CODES (mirror _smoke.py conventions)
# =============================================================================

GATE_FAIL_EXIT = 2          # an unacknowledged divergence (the real failure)
FATAL_EXIT = 1              # config / IO error
NOTHING_CHECKED_EXIT = 4    # every registered pair was UNVERIFIED

REPO_ROOT = Path(__file__).resolve().parents[3]  # .../federal-survey-concept-mapper
# (this file is at v2/src/tevv/prompt_equivalence.py -> 3 parents up is repo root)
ALLOWLIST_PATH = REPO_ROOT / "v2" / "config" / "prompt_divergences.yaml"
EVIDENCE_DIR = REPO_ROOT / "docs" / "stages" / "tevv"
EVIDENCE_JSON = EVIDENCE_DIR / "prompt_equivalence_evidence.json"
EVIDENCE_MD = EVIDENCE_DIR / "prompt_equivalence_report.md"

# Dimensions a divergence can fall under. Stable identifiers; the allowlist
# keys its acknowledgements on (stage, dimension, signature).
DIM_TAXONOMY = "taxonomy_block"
DIM_CODES = "available_codes"
DIM_SCHEMA = "output_schema"
DIM_FRAMING = "task_framing"
ALL_DIMENSIONS = (DIM_TAXONOMY, DIM_CODES, DIM_SCHEMA, DIM_FRAMING)


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(FATAL_EXIT)


# =============================================================================
# SAMPLE PAIR -- a fixed, synthetic input both builders render against.
# =============================================================================
# A reproducibility diff must hold the INPUT constant so the only variation is
# the builder. This synthetic pair carries every field any registered builder
# is known to read; builders ignore keys they do not use. It is deliberately
# generic (no real survey text) so the rendered-prompt diff reflects builder
# STRUCTURE, not the content of any particular question.

SAMPLE_PAIR: dict[str, Any] = {
    "pair_id": "SAMPLE_00001",
    "source_survey": "SAMPLE_SURVEY",
    "shared_topic": "Sample.Topic",
    "shared_subtopic": "Sample.Topic.Subtopic",
    "survey_text": "How many hours did you usually work per week?",
    "acs_text": "How many hours did this person work in the past 12 months?",
    # fields some builders address by other names -- provided as aliases so a
    # builder written against either schema renders without KeyError:
    "survey_question": "How many hours did you usually work per week?",
    "acs_question": "How many hours did this person work in the past 12 months?",
    "subtopic": "Sample.Topic.Subtopic",
    "foodaps_text": "How many hours did you usually work per week?",
    "prior_classification": "Unknown",
    "claude_classification": "Unknown",
    "consolidation_potential": "Unknown",
}


# =============================================================================
# BUILDER REGISTRY
# =============================================================================
# Each registered pair names a v1 builder and a v2 builder by (module path,
# attribute). `verified` flags whether a human has confirmed BOTH builders are
# the real prompt path for that stage. UNVERIFIED pairs are reported but do NOT
# count toward a green gate -- we never claim coverage we have not confirmed.
#
# Stage 3 is verified: both builders were read end-to-end (v1
# create_barrier_prompt in 01_barrier_pipeline.py; v2 create_rater_prompt in
# stage3_barrier_classify.py). Stage 1 / Stage 2 are registered as targets but
# left UNVERIFIED until their v1 prompt source is located and confirmed --
# registering them as "covered" without reading both halves would be inventing
# coverage.

@dataclass
class BuilderRef:
    module_path: Path
    attr: str
    # builders differ in call signature; `kind` tells the harness how to call.
    #   "pair"  -> attr(SAMPLE_PAIR)                 (v2 single-pair builders)
    #   "batch" -> attr([SAMPLE_PAIR])               (v1 batched builders)
    #   "format"-> attr.format(**SAMPLE_PAIR)        (v1 PROMPT_TEMPLATE str)
    kind: str

    def render(self) -> str:
        obj = _load_attr(self.module_path, self.attr)
        if self.kind == "pair":
            return str(obj(SAMPLE_PAIR))
        if self.kind == "batch":
            return str(obj([SAMPLE_PAIR]))
        if self.kind == "format":
            return str(obj).format(**SAMPLE_PAIR)
        if self.kind == "arb_row":
            # Classification-arbitration builders take (row: pd.Series,
            # taxonomy: dict). Rendering them is NOT YET IMPLEMENTED: it needs a
            # synthetic arbitration row (rater A/B topic codings + confidence
            # tier) AND classification-aware extractors, since this gate's
            # extractors target the Stage 3 barrier-prompt shape. Wiring stage2
            # is the documented follow-up in the registry comment. Fail loudly
            # and actionably if a pair with this kind is ever marked verified.
            raise NotImplementedError(
                "builder kind 'arb_row' (classification arbitration) is not "
                "renderable yet: needs a synthetic arbitration row + "
                "classification-aware extractors. See the stage2 registry "
                "comment. Do not set this pair verified=True until both exist.")
        raise ValueError(f"unknown builder kind {self.kind!r}")


@dataclass
class PromptPair:
    stage: str
    description: str
    v1: BuilderRef
    v2: BuilderRef
    verified: bool


def _registry() -> list[PromptPair]:
    v2_core = REPO_ROOT / "v2" / "src" / "core"
    v1_pipe = REPO_ROOT / "src" / "pipelines"
    v1_core = REPO_ROOT / "src" / "core"
    return [
        PromptPair(
            stage="stage3",
            description="Harmonization barrier coding rater prompt",
            v1=BuilderRef(v1_pipe / "01_barrier_pipeline.py",
                          "create_barrier_prompt", "batch"),
            v2=BuilderRef(v2_core / "stage3_barrier_classify.py",
                          "create_rater_prompt", "pair"),
            verified=True,
        ),
        # ---- UNVERIFIED targets: sources CONFIRMED, runtime-verify blocked -
        # Both v1 sources below were located and read (CC task
        # 2026-06-03_tevv_prompt_equivalence_gate.md, Step 4). The placeholder
        # paths/attrs were wrong and are corrected here. Each stays
        # verified=False for a SPECIFIC, documented reason (NOT "unconfirmed"):
        # importing v1 stage1 is unsafe, and stage2 needs classification-aware
        # extractors. Flipping either to True now would fabricate coverage.
        #
        # stage1: v1 create_prompt body is BYTE-IDENTICAL to v2 create_prompt
        # (v2 stage1_classify.py line 134 says so; confirmed by static read).
        # BUT categorize_claude.py runs its pipeline at module level with NO
        # __main__ guard -- importing it to render fires the live v1
        # categorization (6987 questions, API calls). The runtime gate must not
        # import it. Equivalence here is established by STATIC source identity,
        # recorded in the evidence report, not by the importer.
        PromptPair(
            stage="stage1",
            description="Topic/subtopic classification prompt. v1 "
                        "categorize_claude.py:create_prompt is BYTE-IDENTICAL "
                        "to v2 stage1_classify.py:create_prompt (static read). "
                        "Not runtime-rendered: v1 module is import-unsafe "
                        "(runs its pipeline at import, no __main__ guard).",
            v1=BuilderRef(v1_core / "categorize_claude.py",
                          "create_prompt", "batch"),
            v2=BuilderRef(v2_core / "stage1_classify.py",
                          "create_prompt", "batch"),
            verified=False,
        ),
        # stage2: CORRECTED lineage. The placeholder paired v2 stage2_adjudicate
        # with v1 02_arbitration_pipeline -- WRONG: that v1 file is the BARRIER
        # arbitrator (final_barrier_code / F1-F3), a Stage 3 sibling. v2
        # stage2_adjudicate arbitrates TOPIC categorization (pick_rater_a /
        # dual_modal / new_concept). Its true v1 counterpart, named in the v2
        # header, is src/core/arbitrate_final.py:create_arbitration_prompt --
        # same signature (row: Series, taxonomy: dict), both import-safe.
        # NOT verified because this gate's extractors (codes/taxonomy/framing)
        # are tuned to the Stage 3 BARRIER prompt shape; against these
        # classification prompts they return empty sets for BOTH sides and would
        # emit a misleading EQUIVALENT that checked nothing. Verifying stage2
        # needs classification-aware probes (decision set, dual_modal criteria,
        # topic/subtopic schema, taxonomy-JSON identity) -- follow-up work.
        PromptPair(
            stage="stage2",
            description="Classification (topic) arbitration prompt. v1 "
                        "arbitrate_final.py:create_arbitration_prompt <-> v2 "
                        "stage2_adjudicate.py:create_arbitration_prompt (same "
                        "signature, both import-safe). Not verified: this gate's "
                        "extractors are tuned to the Stage 3 barrier-prompt "
                        "shape and would rubber-stamp these classification "
                        "prompts EQUIVALENT. Needs classification-aware probes.",
            v1=BuilderRef(v1_core / "arbitrate_final.py",
                          "create_arbitration_prompt", "arb_row"),
            v2=BuilderRef(v2_core / "stage2_adjudicate.py",
                          "create_arbitration_prompt", "arb_row"),
            verified=False,
        ),
    ]


# =============================================================================
# DYNAMIC IMPORT (modules have non-identifier names like "01_barrier_pipeline")
# =============================================================================

_MODULE_CACHE: dict[Path, Any] = {}


def _load_module(path: Path):
    if path in _MODULE_CACHE:
        return _MODULE_CACHE[path]
    if not path.exists():
        raise FileNotFoundError(path)
    mod_name = "tevv_dyn_" + hashlib.sha1(
        str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    # exec_module runs the target module's TOP-LEVEL code. For an import-safe
    # builder module (lazy SDK imports, work guarded behind __main__) this is
    # harmless. It is NOT harmless for every module: some v1 scripts (e.g.
    # categorize_claude.py) launch their pipeline at import time and would fire
    # live API calls. The caller MUST only reach here for `verified=True` pairs,
    # whose builder a human has read and confirmed import-safe. evaluate() never
    # renders unverified pairs for exactly this reason.
    spec.loader.exec_module(module)
    _MODULE_CACHE[path] = module
    return module


def _load_attr(path: Path, attr: str):
    module = _load_module(path)
    if not hasattr(module, attr):
        raise AttributeError(
            f"{path.name} has no attribute {attr!r} -- builder moved or "
            f"renamed. Update the TEVV registry.")
    return getattr(module, attr)


# =============================================================================
# EXTRACTORS -- pull the four structural dimensions out of a rendered prompt.
# =============================================================================
# These are deliberately conservative regexes over RENDERED text. They look for
# the taxonomy's own code tokens and the JSON output-schema keys. They are NOT
# a parser for arbitrary prompts; they target the shape these survey-methodology
# prompts actually have. If a future builder changes shape enough to defeat
# them, the extractor returns an empty set and the diff surfaces that as a
# divergence rather than silently passing.

# All Level-1 + special barrier codes the taxonomy can contain.
_CODE_TOKEN_RE = re.compile(
    r"\b(?:TC|CC|PC|RS|MC|PM)\.[0-9]\b"      # subtypes e.g. TC.1
    r"|\bNHB\b"                               # no-barrier special code
    r"|\bF[123]\b"                            # feasibility codes
)

# Bare L1 categories offered as a *choice set* (e.g. "TC | CC | PC | RS ...").
_L1_CHOICE_RE = re.compile(r"\b(TC|CC|PC|RS|MC|PM|NHB)\b")

# Output-schema field keys: JSON object keys in the OUTPUT FORMAT block.
_SCHEMA_KEY_RE = re.compile(r'"([a-z_][a-z0-9_]*)"\s*:')


def extract_taxonomy_block(text: str) -> str:
    """The shared instructional taxonomy block, normalized for whitespace.

    We isolate from the first '## Harmonization Barrier Taxonomy' heading to
    the start of the task/output section, so wrapper differences (the per-pair
    framing) do not contaminate the taxonomy-identity check.
    """
    start = text.find("## Harmonization Barrier Taxonomy")
    if start == -1:
        return ""
    tail = text[start:]
    # cut at the first task/output marker after the taxonomy
    for marker in ("## TASK", "## QUESTION PAIR", "## QUESTION PAIRS",
                   "## OUTPUT", "## RATER"):
        idx = tail.find(marker)
        if idx != -1:
            tail = tail[:idx]
    return _normalize_ws(tail)


def extract_available_codes(text: str) -> set[str]:
    codes = set(_CODE_TOKEN_RE.findall(text))
    # also capture bare L1 categories that appear in an explicit choice list
    # ("TC | CC | PC | RS | MC | PM | NHB"); these signal a separate L1 field.
    if "|" in text:
        for m in re.finditer(r"((?:\b(?:TC|CC|PC|RS|MC|PM|NHB)\b\s*\|\s*){2,}"
                             r"\b(?:TC|CC|PC|RS|MC|PM|NHB)\b)", text):
            codes.update(_L1_CHOICE_RE.findall(m.group(1)))
    return codes


def extract_output_schema(text: str) -> set[str]:
    """Field keys requested in the OUTPUT block.

    Restricts to the region after an OUTPUT/Respond marker so question-pair
    payload keys (e.g. 'survey_question') are not mistaken for output fields.
    """
    region = text
    for marker in ("## OUTPUT", "Respond with", "Respond in", "Return a JSON",
                   "Return ONLY"):
        idx = text.find(marker)
        if idx != -1:
            region = text[idx:]
            break
    return set(_SCHEMA_KEY_RE.findall(region))


# Framing signatures: normalized phrases whose presence/absence flips the
# question being asked. Each maps a stable signature key -> truth in the text.
_FRAMING_PROBES: dict[str, Callable[[str], bool]] = {
    "single_barrier_mandate":
        lambda t: bool(re.search(r"\bSINGLE\b.{0,40}\bbarrier\b", t, re.I)
                       or re.search(r"\bthe\s+SINGLE\s+primary\b", t, re.I)),
    "main_constraint_phrasing":
        lambda t: "main constraint" in t.lower(),
    "batched_multi_pair":
        lambda t: ("question pairs" in t.lower()
                   or "one object per pair" in t.lower()
                   or "in the same order" in t.lower()),
    "single_pair_object":
        lambda t: "single json object" in t.lower(),
    "additional_barriers_outlet":
        lambda t: "additional_barriers" in t.lower(),
    "explicit_l1_then_subtype":
        lambda t: ("classification" in t.lower()
                   and "primary_barrier" in t.lower()),
    "nhb_offered":
        lambda t: "nhb" in t.lower(),
}


def extract_framing(text: str) -> dict[str, bool]:
    return {k: bool(fn(text)) for k, fn in _FRAMING_PROBES.items()}


def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# =============================================================================
# DIFF ENGINE
# =============================================================================

@dataclass
class Divergence:
    stage: str
    dimension: str
    signature: str          # stable key for allowlist matching
    detail: str             # human-readable what-changed
    v1_value: Any
    v2_value: Any
    acknowledged: bool = False
    justification: str | None = None
    directional_bias: str | None = None

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def diff_pair(pair: PromptPair) -> tuple[str, str, list[Divergence]]:
    """Render both builders and return (v1_text, v2_text, divergences)."""
    v1_text = pair.v1.render()
    v2_text = pair.v2.render()
    divs: list[Divergence] = []

    # ---- 1. taxonomy block -------------------------------------------------
    tax1 = extract_taxonomy_block(v1_text)
    tax2 = extract_taxonomy_block(v2_text)
    if _sha(tax1) != _sha(tax2):
        c1, c2 = extract_available_codes(tax1), extract_available_codes(tax2)
        added = sorted(c2 - c1)
        removed = sorted(c1 - c2)
        divs.append(Divergence(
            stage=pair.stage, dimension=DIM_TAXONOMY,
            signature="taxonomy_block_text_differs",
            detail=("Taxonomy instructional block is not byte-identical. "
                    f"codes added in v2: {added or 'none'}; "
                    f"codes removed in v2: {removed or 'none'}."),
            v1_value=_sha(tax1)[:16], v2_value=_sha(tax2)[:16]))

    # ---- 2. available codes ------------------------------------------------
    # One divergence PER added/removed code (atomic signatures). Atomic keys
    # let the allowlist acknowledge each code on its own merits and stay stable
    # when the code set shifts: a comma-joined aggregate signature would rebuild
    # its whole string (and silently un-acknowledge everything) the moment one
    # code is added or removed. The allowlist contract is atomic (codes_added:NHB).
    codes1 = extract_available_codes(v1_text)
    codes2 = extract_available_codes(v2_text)
    for code in sorted(codes2 - codes1):
        divs.append(Divergence(
            stage=pair.stage, dimension=DIM_CODES,
            signature="codes_added:" + code,
            detail=f"v2 makes code {code!r} available that v1 did not.",
            v1_value=sorted(codes1), v2_value=sorted(codes2)))
    for code in sorted(codes1 - codes2):
        divs.append(Divergence(
            stage=pair.stage, dimension=DIM_CODES,
            signature="codes_removed:" + code,
            detail=f"v1 made code {code!r} available that v2 dropped.",
            v1_value=sorted(codes1), v2_value=sorted(codes2)))

    # ---- 3. output schema --------------------------------------------------
    # One divergence PER added/removed field (atomic signatures), same rationale.
    sch1 = extract_output_schema(v1_text)
    sch2 = extract_output_schema(v2_text)
    for field in sorted(sch2 - sch1):
        divs.append(Divergence(
            stage=pair.stage, dimension=DIM_SCHEMA,
            signature="schema_fields_added:" + field,
            detail=f"v2 output schema adds field {field!r} that v1 lacked.",
            v1_value=sorted(sch1), v2_value=sorted(sch2)))
    for field in sorted(sch1 - sch2):
        divs.append(Divergence(
            stage=pair.stage, dimension=DIM_SCHEMA,
            signature="schema_fields_removed:" + field,
            detail=f"v2 output schema drops field {field!r} that v1 had.",
            v1_value=sorted(sch1), v2_value=sorted(sch2)))

    # ---- 4. task framing ---------------------------------------------------
    fr1 = extract_framing(v1_text)
    fr2 = extract_framing(v2_text)
    for key in sorted(set(fr1) | set(fr2)):
        if fr1.get(key) != fr2.get(key):
            divs.append(Divergence(
                stage=pair.stage, dimension=DIM_FRAMING,
                signature=f"framing:{key}",
                detail=(f"Framing probe {key!r} differs: "
                        f"v1={fr1.get(key)}, v2={fr2.get(key)}."),
                v1_value=fr1.get(key), v2_value=fr2.get(key)))

    return v1_text, v2_text, divs


# =============================================================================
# ALLOWLIST
# =============================================================================
# Structure (v2/config/prompt_divergences.yaml):
#
#   version: 1
#   acknowledged:
#     - stage: stage3
#       dimension: available_codes
#       signature: "codes_added:NHB"
#       justification: "v2 added an explicit No-Harmonization-Barrier code ..."
#       directional_bias: "Splits no-barrier cases out of F1/F2, sparsening ..."
#
# A divergence is acknowledged iff a row matches (stage, dimension, signature)
# AND carries a non-empty justification. An acknowledgement with no
# justification is treated as UNacknowledged -- you cannot wave something
# through with a blank reason.

def load_allowlist() -> list[dict[str, Any]]:
    if not ALLOWLIST_PATH.exists():
        return []
    try:
        data = yaml.safe_load(ALLOWLIST_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        die(f"malformed allowlist {ALLOWLIST_PATH}: {e}")
    rows = data.get("acknowledged", [])
    if not isinstance(rows, list):
        die(f"allowlist 'acknowledged' must be a list, got {type(rows)}")
    return rows


def apply_allowlist(divs: list[Divergence],
                    allow: list[dict[str, Any]]) -> None:
    index: dict[tuple[Any, Any, Any], dict[str, Any]] = {}
    for row in allow:
        key = (row.get("stage"), row.get("dimension"), row.get("signature"))
        index[key] = row
    for d in divs:
        row = index.get((d.stage, d.dimension, d.signature))
        if row and str(row.get("justification", "")).strip():
            d.acknowledged = True
            d.justification = row.get("justification")
            d.directional_bias = row.get("directional_bias")


# =============================================================================
# EVIDENCE WRITERS
# =============================================================================

def write_evidence(results: list[dict[str, Any]],
                   unverified: list[str]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "allowlist_path": str(ALLOWLIST_PATH.relative_to(REPO_ROOT)),
        "sample_pair": SAMPLE_PAIR,
        "results": results,
        "unverified_pairs": unverified,
    }
    EVIDENCE_JSON.write_text(json.dumps(payload, indent=2, default=str),
                             encoding="utf-8")

    L: list[str] = []
    L.append("# TEVV Evidence: v1-vs-v2 Prompt Equivalence")
    L.append("")
    L.append(f"Generated: {payload['generated_at']}")
    L.append("")
    L.append("This report is produced by "
             "`v2/src/tevv/prompt_equivalence.py`. It mechanically diffs the "
             "rendered v1 and v2 prompts for each registered pipeline stage "
             "and checks every divergence against the acknowledged-divergence "
             "allowlist (`v2/config/prompt_divergences.yaml`). It calls no "
             "model; the diff is a static-text property.")
    L.append("")
    L.append("Why it matters: the v2 confirmation run is a reproducibility "
             "study. A v1-vs-v2 disagreement is only a clean MODEL finding if "
             "the rendered prompt was the same question across versions. "
             "Unacknowledged divergence means the comparison is confounded.")
    L.append("")
    for r in results:
        L.append(f"## {r['stage']} -- {r['description']}")
        L.append("")
        L.append(f"- verified pair: {r['verified']}")
        L.append(f"- divergences found: {len(r['divergences'])}")
        unack = [d for d in r["divergences"] if not d["acknowledged"]]
        L.append(f"- unacknowledged: {len(unack)}")
        L.append(f"- verdict: **{r['verdict']}**")
        L.append("")
        if r["divergences"]:
            L.append("| dimension | signature | what changed | ack | "
                     "directional bias (human annotation) |")
            L.append("|---|---|---|---|---|")
            for d in r["divergences"]:
                # collapse any internal whitespace (folded-YAML scalars carry
                # newlines) so each cell stays on one table row.
                bias = " ".join((d.get("directional_bias") or "").split()
                                ).replace("|", "/")
                detail = " ".join(d["detail"].split()).replace("|", "/")
                L.append(f"| {d['dimension']} | `{d['signature']}` | "
                         f"{detail} | {'yes' if d['acknowledged'] else 'NO'} "
                         f"| {bias} |")
            L.append("")
    if unverified:
        L.append("## Unverified pairs (registered, not asserted)")
        L.append("")
        L.append("These stages are registered targets the gate does NOT "
                 "runtime-verify. They do NOT count toward a green gate. Each "
                 "line states its specific reason: a source may be confirmed "
                 "yet still unverified because the v1 module is import-unsafe "
                 "or because the gate's extractors do not yet fit that prompt "
                 "shape. Closing these is documented follow-up work.")
        L.append("")
        for u in unverified:
            L.append(f"- {u}")
        L.append("")
    EVIDENCE_MD.write_text("\n".join(L), encoding="utf-8")
    print(f"   evidence: {EVIDENCE_JSON.relative_to(REPO_ROOT)}")
    print(f"   report:   {EVIDENCE_MD.relative_to(REPO_ROOT)}")


# =============================================================================
# DRIVER
# =============================================================================

def evaluate(stage_filter: str | None) -> tuple[int, list[dict[str, Any]],
                                                 list[str]]:
    allow = load_allowlist()
    results: list[dict[str, Any]] = []
    unverified: list[str] = []
    verified_evaluated = 0
    gate_fail = False

    for pair in _registry():
        if stage_filter and pair.stage != stage_filter:
            continue
        if not pair.verified:
            # DO NOT render/import an unverified pair. Rendering a builder means
            # dynamically importing its module, which executes that module's
            # top-level code. An unverified v1 source is a BEST-GUESS placeholder
            # we have not read; some such modules (e.g. categorize_claude.py) run
            # their pipeline at import time -- importing one fires live API calls.
            # `verified=True` is precisely the human attestation that a builder
            # was read and is safe to import. Until then we make NO claim and do
            # NO import; the pair is reported as unverified and never imported.
            unverified.append(f"{pair.stage}: {pair.description}")
            results.append({
                "stage": pair.stage, "description": pair.description,
                "verified": False, "verdict": "UNVERIFIED (not imported)",
                "divergences": [],
            })
            continue

        try:
            _, _, divs = diff_pair(pair)
        except (FileNotFoundError, AttributeError, ValueError) as e:
            die(f"[{pair.stage}] cannot render builders: {e}")
        apply_allowlist(divs, allow)
        verified_evaluated += 1
        unack = [d for d in divs if not d.acknowledged]
        verdict = "EQUIVALENT" if not divs else (
            "ACKNOWLEDGED_DIVERGENCE" if not unack else "FAIL")
        if unack:
            gate_fail = True
        results.append({
            "stage": pair.stage, "description": pair.description,
            "verified": True, "verdict": verdict,
            "divergences": [d.to_record() for d in divs],
        })

    if verified_evaluated == 0 and not gate_fail:
        return NOTHING_CHECKED_EXIT, results, unverified
    return (GATE_FAIL_EXIT if gate_fail else 0), results, unverified


def print_summary(results: list[dict[str, Any]]) -> None:
    print("=" * 70)
    print("TEVV PROMPT-EQUIVALENCE GATE")
    print("=" * 70)
    for r in results:
        flag = {"EQUIVALENT": "ok", "ACKNOWLEDGED_DIVERGENCE": "ack",
                "FAIL": "FAIL"}.get(r["verdict"], "skip")
        print(f"[{flag:>4}] {r['stage']:<8} {r['verdict']:<24} "
              f"({len(r['divergences'])} divergence(s))")
        for d in r["divergences"]:
            if not d["acknowledged"] and r["verified"]:
                print(f"        UNACKNOWLEDGED  {d['dimension']}/"
                      f"{d['signature']}: {d['detail']}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="TEVV gate: diff v1-vs-v2 rendered prompts; fail on "
                    "unacknowledged divergence.")
    ap.add_argument("--stage", default=None,
                    help="evaluate one stage (e.g. stage3)")
    ap.add_argument("--report", action="store_true",
                    help="write JSON + MD evidence to docs/stages/tevv/")
    ap.add_argument("--list", action="store_true",
                    help="list registered prompt pairs and exit")
    args = ap.parse_args()

    if args.list:
        for p in _registry():
            tag = "VERIFIED" if p.verified else "unverified"
            print(f"[{tag:>10}] {p.stage:<8} {p.description}")
            print(f"             v1: {p.v1.module_path.name}:{p.v1.attr} "
                  f"({p.v1.kind})")
            print(f"             v2: {p.v2.module_path.name}:{p.v2.attr} "
                  f"({p.v2.kind})")
        return 0

    exit_code, results, unverified = evaluate(args.stage)
    print_summary(results)
    if args.report:
        write_evidence(results, unverified)

    if exit_code == NOTHING_CHECKED_EXIT:
        print("\nNOTHING CHECKED: no verified pair was evaluated. A green "
              "gate requires at least one verified pair.", file=sys.stderr)
    elif exit_code == GATE_FAIL_EXIT:
        print("\nGATE FAIL: at least one unacknowledged prompt divergence. "
              "Either acknowledge it in v2/config/prompt_divergences.yaml "
              "with a written justification, or fix the prompt.",
              file=sys.stderr)
    else:
        print("\nGATE PASS: all verified pairs equivalent or every divergence "
              "acknowledged.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
