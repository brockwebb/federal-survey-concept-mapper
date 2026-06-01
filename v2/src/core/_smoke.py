#!/usr/bin/env python3
"""Shared smoke-test gate for the v2 pipeline scripts.

Every v2 Stage 1-3 bug was interface-contract drift between separately
written components -- a task_id builder vs its parser regex, a JSONL writer
field vs the reader field, a config model name vs the harness pool name, a
max_tokens value carried over from v1, or a silent "wrote N, loaded 0". Every
one of them surfaced at the END of a full run instead of the START.

A round-trip smoke test on a tiny atomic unit (`SMOKE_N` records) catches all
of them in seconds: ask the pipeline for N records, confirm it wrote N, read
them back, confirm we got N with non-null keys, and confirm a model actually
served. This module is the shared, pipeline-agnostic core of that gate. It
operates only on counts and key-field names handed in by the caller -- it
makes no assumptions about any specific stage.

Two halves:

  * `assert_roundtrip(...)` / `check_roundtrip(...)` -- the hard invariant
    check a `--smoke` run calls after each record-producing phase, and that
    the normal run path calls too (Part 4: a 100%-failure run must exit
    non-zero loudly, not emit a calm FAIL-verdict markdown and exit 0).

  * `write_smoke_stamp(...)` / `smoke_gate_ok(...)` -- the stamp a passing
    `--smoke` writes, and the gate a full/initial run checks before it
    submits any batch. The stamp records a SHA-256 of the script's own
    source, so "smoke passed last week on different code" does not count.

The served-model invariant intentionally does NOT require the requested pool
alias (e.g. ``claude_4_5_sonnet``) to appear verbatim in the served-model set.
Per usai-harness ADR-012 the pool alias and the served API model id are
distinct strings -- the response carries the returned id, not the alias. The
real failure mode the invariant guards (a configured model absent from the
pool) is already a hard error inside the harness before any call, and shows up
here as an empty served-model set or an unknown-model flag. So the invariant
checks exactly those two observable signals.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


# The atomic unit size. Small enough to be fast and cheap, large enough to
# exercise at least one likely-agreement, one likely-disagreement, and one
# edge case. Do NOT drop below 3.
SMOKE_N = 3

# Dedicated non-zero exit code for a failed --smoke run, distinguishable from
# a normal FAIL verdict (which uses 2) and an ordinary FATAL (which uses 1).
SMOKE_EXIT_CODE = 3

# Tolerated fraction of LOUD, recorded failures (request_failed / parse_failed
# / arbitration_failed) on a full run. At or below this, the run is a
# PASS_WITH_RESIDUAL -- a normal retryable residual from API flakiness, cleared
# by --retry-failed. Above it, the failures are systemic and the run FAILs.
# This is the single cross-stage policy knob; it is deliberately NOT a silent
# magic number buried in three scripts. A caller may override per invocation
# via the `threshold` argument to classify_run.
RESIDUAL_THRESHOLD = 0.02


class SmokeFailure(Exception):
    """A round-trip invariant broke. The run loop converts this to a fatal
    exit with code SMOKE_EXIT_CODE and a 'SMOKE FAILED' banner."""


# ---------------------------------------------------------------------------
# ROUND-TRIP INVARIANTS
# ---------------------------------------------------------------------------

def _empty_key(value: Any) -> bool:
    """A key-field value that would cause a silent drop on read-back."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def check_roundtrip(
    *,
    requested: int,
    written: int,
    loaded: int,
    served_models: set[str] | None = None,
    model_requested: str | None = None,
    unknown_model: bool = False,
    key_field: str | None = None,
    key_values: Sequence[Any] | None = None,
) -> list[str]:
    """Pure invariant checker. Returns a list of human-readable violation
    strings; an empty list means every invariant holds.

    Invariants:
      1. written == requested      -- we asked for N, did we write N?
      2. loaded == written         -- we wrote N, can we read N back?
                                      (the pair_id=None silent-drop bug)
      3. a model actually served   -- only when `model_requested` is given:
                                      served_models non-empty and no
                                      unknown-model error (the model
                                      name/pool bug)
      4. no null/empty key value   -- only when `key_field`/`key_values`
                                      given: every loaded record's key field
                                      is populated (the silent-drop bug)
    """
    problems: list[str] = []

    if written != requested:
        problems.append(
            f"written != requested: wrote {written}, requested {requested}"
        )
    if loaded != written:
        problems.append(
            f"loaded != written: read back {loaded}, wrote {written} "
            f"(records dropped on read -- check the key field)"
        )
    if model_requested is not None:
        served = served_models or set()
        if unknown_model:
            problems.append(
                f"served model: unknown-model error for requested "
                f"{model_requested!r} (not in harness pool?)"
            )
        elif not served:
            problems.append(
                f"served model: no model served for requested "
                f"{model_requested!r} (every call failed before reaching a model)"
            )
    if key_field is not None and key_values is not None:
        bad = sum(1 for v in key_values if _empty_key(v))
        if bad:
            problems.append(
                f"null/empty key field {key_field!r}: {bad} of "
                f"{len(key_values)} loaded records have no {key_field}"
            )

    return problems


def assert_roundtrip(
    stage: str,
    *,
    requested: int,
    written: int,
    loaded: int,
    served_models: set[str] | None = None,
    model_requested: str | None = None,
    unknown_model: bool = False,
    key_field: str | None = None,
    key_values: Sequence[Any] | None = None,
) -> None:
    """Hard-assert the round-trip invariants for one phase. Raises
    SmokeFailure naming exactly which invariant(s) broke. `stage` is a label
    such as 'stage3_rater_a' used in the diagnostic."""
    problems = check_roundtrip(
        requested=requested, written=written, loaded=loaded,
        served_models=served_models, model_requested=model_requested,
        unknown_model=unknown_model, key_field=key_field, key_values=key_values,
    )
    if problems:
        detail = "; ".join(problems)
        raise SmokeFailure(f"[{stage}] {detail}")


def fatal_roundtrip_problems(
    *,
    requested: int,
    written: int,
    loaded: int,
    key_field: str | None = None,
    key_values: Sequence[Any] | None = None,
) -> list[str]:
    """The ALWAYS-FATAL subset of the round-trip invariants: a broken read-back
    contract, total failure, or a null/empty key. Use this for the normal
    initial-run per-phase gate.

    Deliberately omits the `written < requested` check: a shortfall from LOUD,
    recorded failures is a retryable residual, not a code-contract break, and
    is graded by classify_run against RESIDUAL_THRESHOLD instead. (--smoke
    keeps the strict check_roundtrip, where written==requested must hold
    because every task writes a line.)
    """
    problems: list[str] = []
    if loaded != written:
        problems.append(
            f"loaded != written: read back {loaded}, wrote {written} "
            f"(records silently dropped on read -- broken read-back contract)"
        )
    if written == 0 and requested > 0:
        problems.append(
            f"total failure: 0 of {requested} records produced"
        )
    if key_field is not None and key_values is not None:
        bad = sum(1 for v in key_values if _empty_key(v))
        if bad:
            problems.append(
                f"null/empty key field {key_field!r}: {bad} of "
                f"{len(key_values)} loaded records have no {key_field}"
            )
    return problems


# ---------------------------------------------------------------------------
# RUN VERDICT (three-state: PASS / PASS_WITH_RESIDUAL / FAIL)
# ---------------------------------------------------------------------------

def classify_run(
    *,
    requested: int,
    written: int,
    loaded: int,
    threshold: float = RESIDUAL_THRESHOLD,
) -> dict[str, Any]:
    """Grade a full run into one of three states. Returns a dict with keys
    `state`, `exit_code`, `fatal`, `residual`, `residual_pct`, `reason`.

    Two count checks get OPPOSITE treatment (do not blur them):

      * `loaded != written` (read-back contract) -> FAIL, fatal, ALWAYS.
        Writing N records but reading back fewer means records are silently
        dropped (the pair_id=None class of bug). Never softened, even for a
        single record.
      * `written < requested` (loud, recorded failures) -> threshold-based.
        A small fraction failing loudly is expected API flakiness and is
        retryable; only a systemic rate FAILs.

    States:
      PASS                -- written == requested, loaded == written.
      PASS_WITH_RESIDUAL  -- loaded == written, residual <= threshold. Exit 0.
      FAIL                -- loaded != written (fatal), OR written == 0 with
                             requested > 0 (fatal), OR loud failures > threshold.
    """
    residual = max(0, requested - written)
    residual_pct = (residual / requested) if requested else 0.0

    if loaded != written:
        return {
            "state": "FAIL", "exit_code": 2, "fatal": True,
            "residual": residual, "residual_pct": residual_pct,
            "reason": (f"read-back contract broken: loaded {loaded} != "
                       f"written {written} (silent drop -- code bug, not "
                       f"flakiness)"),
        }
    if written == 0 and requested > 0:
        return {
            "state": "FAIL", "exit_code": 2, "fatal": True,
            "residual": residual, "residual_pct": residual_pct,
            "reason": f"total failure: 0 of {requested} records produced",
        }
    if residual == 0:
        return {
            "state": "PASS", "exit_code": 0, "fatal": False,
            "residual": 0, "residual_pct": 0.0,
            "reason": f"clean: {written}/{requested} produced and read back",
        }
    if residual_pct <= threshold:
        return {
            "state": "PASS_WITH_RESIDUAL", "exit_code": 0, "fatal": False,
            "residual": residual, "residual_pct": residual_pct,
            "reason": (f"{residual} residual loud failure(s) "
                       f"({residual_pct*100:.2f}% <= {threshold*100:.0f}%) -- "
                       f"run --retry-failed to resolve"),
        }
    return {
        "state": "FAIL", "exit_code": 2, "fatal": False,
        "residual": residual, "residual_pct": residual_pct,
        "reason": (f"loud failures {residual}/{requested} "
                   f"({residual_pct*100:.2f}%) exceed the "
                   f"{threshold*100:.0f}% threshold -- systemic, not flakiness"),
    }


# ---------------------------------------------------------------------------
# SCRIPT-SOURCE HASH + SMOKE STAMP / GATE
# ---------------------------------------------------------------------------

def script_source_hash(script_path: str | Path) -> str:
    """SHA-256 hex digest of a script file's bytes. The gate compares this
    against the stamp so a code change since the last smoke pass invalidates
    the gate."""
    return hashlib.sha256(Path(script_path).read_bytes()).hexdigest()


def git_commit_hash(cwd: str | Path | None = None) -> str | None:
    """Current git commit, or None if unavailable (not a repo, no git)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def write_smoke_stamp(
    stamp_path: str | Path,
    *,
    script_path: str | Path,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a passing smoke run. Writes timestamp, git commit (if any),
    script filename, and a SHA-256 of the script's own source to
    `stamp_path`. Returns the payload."""
    stamp_path = Path(stamp_path)
    script_path = Path(script_path)
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit_hash(script_path.parent),
        "script": script_path.name,
        "source_sha256": script_source_hash(script_path),
    }
    if extra:
        payload.update(extra)
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def read_smoke_stamp(stamp_path: str | Path) -> dict[str, Any] | None:
    """Load a stamp, or None if it is missing or unreadable."""
    stamp_path = Path(stamp_path)
    if not stamp_path.exists():
        return None
    try:
        return json.loads(stamp_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def smoke_gate_ok(
    stamp_path: str | Path,
    *,
    script_path: str | Path,
) -> tuple[bool, str]:
    """Decide whether a full/initial run may proceed. Returns (ok, reason).

    ok is False if no stamp exists, or if the script's current source hash
    does not match the stamp's (the code changed since smoke last passed)."""
    stamp = read_smoke_stamp(stamp_path)
    if stamp is None:
        return False, (
            "no smoke pass recorded for current code. Run with --smoke first."
        )
    current = script_source_hash(script_path)
    if stamp.get("source_sha256") != current:
        return False, (
            "script source changed since the last smoke pass. "
            "Run with --smoke again."
        )
    return True, "smoke pass valid for current code"


# ---------------------------------------------------------------------------
# BIASED SMOKE-SAMPLE PICKER
# ---------------------------------------------------------------------------

def pick_smoke_indices(flags: Sequence[bool], n: int = SMOKE_N) -> list[int]:
    """Choose up to `n` row indices for a smoke sample, biased to include at
    least one known-tricky record. `flags[i]` is True when row i is tricky
    (e.g. NaN/empty text), so edge handling is exercised, not just the happy
    path. Returns fewer than n only when fewer than n rows are available."""
    total = len(flags)
    n = min(n, total)
    if n == 0:
        return []

    tricky = [i for i, f in enumerate(flags) if f]
    plain = [i for i, f in enumerate(flags) if not f]

    chosen: list[int] = []
    if tricky:
        chosen.append(tricky[0])
    # Fill the rest from plain rows first, then any remaining tricky rows,
    # preserving original order and never duplicating.
    for i in plain + tricky[1:]:
        if len(chosen) >= n:
            break
        if i not in chosen:
            chosen.append(i)
    return sorted(chosen)
