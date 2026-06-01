"""Unit tests for the shared smoke-test gate helper (`src/core/_smoke.py`).

These cover the pure, deterministic core of the smoke gate: the round-trip
invariant checker, the script-source hash, the stamp/gate decision, and the
biased-sample picker. The harness-integration half of smoke mode (real API
calls on SMOKE_N records) is exercised by the per-script `--smoke` runs, not
here, because mocking the harness would hide the exact contract bugs the gate
exists to catch.

Run from v2/:
    python -m pytest tests/test_smoke.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# _smoke lives in src/core; make it importable without a package install.
CORE = Path(__file__).resolve().parent.parent / "src" / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

import _smoke  # noqa: E402


# ---------------------------------------------------------------------------
# SMOKE_N
# ---------------------------------------------------------------------------

def test_smoke_n_is_at_least_three():
    # Need agreement + disagreement + edge case; below 3 is forbidden.
    assert _smoke.SMOKE_N >= 3


# ---------------------------------------------------------------------------
# check_roundtrip — the four invariants
# ---------------------------------------------------------------------------

def test_check_roundtrip_all_good_returns_no_problems():
    problems = _smoke.check_roundtrip(
        requested=3, written=3, loaded=3,
        served_models={"some-served-model-id"}, model_requested="pool_alias",
        unknown_model=False,
        key_field="pair_id", key_values=["CPS_00000", "CPS_00001", "CPS_00002"],
    )
    assert problems == []


def test_check_roundtrip_flags_written_not_equal_requested():
    problems = _smoke.check_roundtrip(requested=3, written=2, loaded=2)
    assert len(problems) == 1
    assert "written" in problems[0].lower()
    assert "3" in problems[0] and "2" in problems[0]


def test_check_roundtrip_flags_loaded_not_equal_written():
    # The pair_id=None / silent-drop bug: wrote N, read back fewer.
    problems = _smoke.check_roundtrip(requested=3, written=3, loaded=0)
    assert len(problems) == 1
    assert "loaded" in problems[0].lower()
    assert "0" in problems[0] and "3" in problems[0]


def test_check_roundtrip_flags_empty_served_models_when_model_requested():
    problems = _smoke.check_roundtrip(
        requested=3, written=3, loaded=3,
        served_models=set(), model_requested="pool_alias", unknown_model=False,
    )
    assert len(problems) == 1
    assert "served" in problems[0].lower()


def test_check_roundtrip_flags_unknown_model_error():
    problems = _smoke.check_roundtrip(
        requested=3, written=3, loaded=3,
        served_models={"x"}, model_requested="pool_alias", unknown_model=True,
    )
    assert len(problems) == 1
    assert "unknown" in problems[0].lower() and "model" in problems[0].lower()


def test_check_roundtrip_served_model_check_skipped_when_no_model_requested():
    # Data-only scripts (compare, finalize, pair_builder) pass no model and
    # must not trip the served-model invariant.
    problems = _smoke.check_roundtrip(
        requested=3, written=3, loaded=3,
        served_models=None, model_requested=None,
    )
    assert problems == []


def test_check_roundtrip_flags_null_key_value():
    problems = _smoke.check_roundtrip(
        requested=3, written=3, loaded=3,
        key_field="pair_id", key_values=["CPS_00000", None, "CPS_00002"],
    )
    assert len(problems) == 1
    assert "pair_id" in problems[0]


def test_check_roundtrip_flags_empty_string_key_value():
    problems = _smoke.check_roundtrip(
        requested=3, written=3, loaded=3,
        key_field="id", key_values=["7", "   ", "9"],
    )
    assert len(problems) == 1
    assert "id" in problems[0]


def test_check_roundtrip_accumulates_multiple_problems():
    problems = _smoke.check_roundtrip(
        requested=3, written=2, loaded=1,
        served_models=set(), model_requested="m", unknown_model=False,
        key_field="pair_id", key_values=[None],
    )
    # written!=requested, loaded!=written, empty served, null key = 4 distinct.
    assert len(problems) == 4


# ---------------------------------------------------------------------------
# assert_roundtrip — raises SmokeFailure on violation
# ---------------------------------------------------------------------------

def test_assert_roundtrip_passes_silently_when_clean():
    # Should not raise.
    _smoke.assert_roundtrip(
        "stage3_rater_a", requested=3, written=3, loaded=3,
        served_models={"served-id"}, model_requested="alias",
    )


def test_assert_roundtrip_raises_smokefailure_naming_invariant():
    with pytest.raises(_smoke.SmokeFailure) as exc:
        _smoke.assert_roundtrip(
            "stage3_rater_a", requested=3, written=3, loaded=0,
            served_models={"served-id"}, model_requested="alias",
        )
    msg = str(exc.value)
    assert "loaded" in msg.lower()
    assert "stage3_rater_a" in msg


# ---------------------------------------------------------------------------
# script_source_hash
# ---------------------------------------------------------------------------

def test_script_source_hash_is_stable_for_same_content(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("print('hello')\n", encoding="utf-8")
    h1 = _smoke.script_source_hash(f)
    h2 = _smoke.script_source_hash(f)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_script_source_hash_changes_when_content_changes(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("print('a')\n", encoding="utf-8")
    h1 = _smoke.script_source_hash(f)
    f.write_text("print('b')\n", encoding="utf-8")
    h2 = _smoke.script_source_hash(f)
    assert h1 != h2


# ---------------------------------------------------------------------------
# smoke gate: write stamp + decide
# ---------------------------------------------------------------------------

def test_smoke_gate_fails_when_stamp_missing(tmp_path):
    script = tmp_path / "s.py"
    script.write_text("x = 1\n", encoding="utf-8")
    stamp = tmp_path / "smoke" / "smoke_pass.json"
    ok, reason = _smoke.smoke_gate_ok(stamp, script_path=script)
    assert ok is False
    assert "smoke" in reason.lower()


def test_smoke_gate_passes_after_matching_stamp_written(tmp_path):
    script = tmp_path / "s.py"
    script.write_text("x = 1\n", encoding="utf-8")
    stamp = tmp_path / "smoke" / "smoke_pass.json"
    _smoke.write_smoke_stamp(stamp, script_path=script)
    ok, reason = _smoke.smoke_gate_ok(stamp, script_path=script)
    assert ok is True


def test_smoke_gate_fails_when_source_changed_since_stamp(tmp_path):
    script = tmp_path / "s.py"
    script.write_text("x = 1\n", encoding="utf-8")
    stamp = tmp_path / "smoke" / "smoke_pass.json"
    _smoke.write_smoke_stamp(stamp, script_path=script)
    # Edit the script after the smoke pass — stamp is now stale.
    script.write_text("x = 2\n", encoding="utf-8")
    ok, reason = _smoke.smoke_gate_ok(stamp, script_path=script)
    assert ok is False
    assert "changed" in reason.lower() or "hash" in reason.lower()


def test_write_smoke_stamp_records_expected_fields(tmp_path):
    script = tmp_path / "s.py"
    script.write_text("x = 1\n", encoding="utf-8")
    stamp = tmp_path / "smoke" / "smoke_pass.json"
    payload = _smoke.write_smoke_stamp(stamp, script_path=script)
    assert stamp.exists()
    for field in ("timestamp", "script", "source_sha256"):
        assert field in payload
    assert payload["source_sha256"] == _smoke.script_source_hash(script)


# ---------------------------------------------------------------------------
# classify_run — three-state verdict (PASS / PASS_WITH_RESIDUAL / FAIL)
# ---------------------------------------------------------------------------

def test_classify_run_clean_is_pass():
    v = _smoke.classify_run(requested=788, written=788, loaded=788)
    assert v["state"] == "PASS"
    assert v["exit_code"] == 0
    assert v["fatal"] is False
    assert v["residual"] == 0


def test_classify_run_one_loud_straggler_is_pass_with_residual():
    # 787/788, one loud arbitration_failed, all written records read back.
    v = _smoke.classify_run(requested=788, written=787, loaded=787)
    assert v["state"] == "PASS_WITH_RESIDUAL"
    assert v["exit_code"] == 0
    assert v["fatal"] is False
    assert v["residual"] == 1
    assert "retry" in v["reason"].lower()


def test_classify_run_silent_drop_is_fatal_fail():
    # Wrote 788, can only read back 787 -> records silently dropped.
    v = _smoke.classify_run(requested=788, written=788, loaded=787)
    assert v["state"] == "FAIL"
    assert v["fatal"] is True
    assert v["exit_code"] != 0
    assert "silent" in v["reason"].lower() or "read-back" in v["reason"].lower()


def test_classify_run_single_silent_drop_fatal_even_below_threshold():
    # A 1-record silent drop is fatal regardless of how small the fraction is.
    v = _smoke.classify_run(requested=10000, written=10000, loaded=9999)
    assert v["state"] == "FAIL"
    assert v["fatal"] is True


def test_classify_run_loud_failures_above_threshold_is_fail():
    # 10% loud failures (> 2%): systemic, not flakiness.
    v = _smoke.classify_run(requested=100, written=90, loaded=90)
    assert v["state"] == "FAIL"
    assert v["fatal"] is False  # not a silent drop; loud but over threshold
    assert v["exit_code"] != 0


def test_classify_run_total_failure_is_fatal():
    v = _smoke.classify_run(requested=788, written=0, loaded=0)
    assert v["state"] == "FAIL"
    assert v["fatal"] is True
    assert v["exit_code"] != 0


def test_classify_run_exactly_two_percent_is_residual():
    # Boundary: residual == threshold -> tolerated.
    v = _smoke.classify_run(requested=100, written=98, loaded=98)
    assert v["state"] == "PASS_WITH_RESIDUAL"
    assert v["exit_code"] == 0


def test_classify_run_just_over_two_percent_is_fail():
    v = _smoke.classify_run(requested=100, written=97, loaded=97)
    assert v["state"] == "FAIL"


def test_classify_run_zero_requested_is_pass():
    v = _smoke.classify_run(requested=0, written=0, loaded=0)
    assert v["state"] == "PASS"
    assert v["exit_code"] == 0


# ---------------------------------------------------------------------------
# fatal_roundtrip_problems — the always-fatal subset (for the initial gate)
# ---------------------------------------------------------------------------

def test_fatal_problems_flags_silent_drop():
    problems = _smoke.fatal_roundtrip_problems(requested=788, written=788, loaded=0)
    assert len(problems) == 1
    assert "loaded" in problems[0].lower()


def test_fatal_problems_flags_total_failure():
    problems = _smoke.fatal_roundtrip_problems(requested=788, written=0, loaded=0)
    assert len(problems) == 1


def test_fatal_problems_does_not_flag_loud_residual():
    # written < requested but every written record read back: NOT fatal here
    # (the threshold verdict handles it, not the gate).
    problems = _smoke.fatal_roundtrip_problems(requested=788, written=787, loaded=787)
    assert problems == []


def test_fatal_problems_flags_null_key():
    problems = _smoke.fatal_roundtrip_problems(
        requested=3, written=3, loaded=3,
        key_field="pair_id", key_values=["A", None, "C"],
    )
    assert len(problems) == 1
    assert "pair_id" in problems[0]


# ---------------------------------------------------------------------------
# biased smoke sample picker
# ---------------------------------------------------------------------------

def test_pick_smoke_indices_includes_a_tricky_row_when_present():
    # flags[i] True == row i is a known-tricky/edge record.
    flags = [False, False, False, False, True, False]
    idx = _smoke.pick_smoke_indices(flags, n=3)
    assert len(idx) == 3
    assert 4 in idx  # the tricky row must be included


def test_pick_smoke_indices_no_tricky_row_returns_first_n():
    flags = [False, False, False, False]
    idx = _smoke.pick_smoke_indices(flags, n=3)
    assert len(idx) == 3
    assert all(0 <= i < 4 for i in idx)


def test_pick_smoke_indices_caps_at_available_rows():
    flags = [True, False]
    idx = _smoke.pick_smoke_indices(flags, n=3)
    assert len(idx) == 2
