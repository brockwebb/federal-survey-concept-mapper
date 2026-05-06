# Phase 4 — Remediation Plan

**Audit:** v2 Stage 1 ground-truth restoration
**Status:** Plan only. NO file edits have been applied as of this document.
**Pre-execution HEAD:** `b51f4c4` on `origin/main`.

## Decision matrix

| File | Current status | Decision | Operation | Expected post-state SHA-256 |
|---|---|---|---|---|
| `v2/config/stage1.yaml` | Clean (no uncommitted edits) | **KEEP AS-IS** | None | `1cb966e7200c81bce315e4834a405c5d3dede303870da479d1049042f2fac6e5` (unchanged) |
| `v2/src/core/stage1_classify.py` | Carries 4 `log(...)` call sites + 1 `log()` helper definition; all entirely in working-tree (uncommitted); all attributable to rejected task `d0f8830a` per the comment block at lines 41-44 | **REVERT PARTIAL EDITS** | `git restore --source=HEAD --staged --worktree v2/src/core/stage1_classify.py` (single command — restores the file to its HEAD state, since 100% of the uncommitted changes are stopgap edits) | `dd3c0b550fc4068693edd6a7b1da6b06ea549a8bd8a55d6e7a1810d3b75bf60d` (must equal `git rev-parse HEAD:v2/src/core/stage1_classify.py`'s blob hash; recompute as SHA-256 of the file post-restore for direct comparison) |
| `cc_tasks/2026-05-05_v2_stage1_classify.md` | Clean | **KEEP AS-IS** | None | unchanged |
| `cc_tasks/2026-05-06_v2_stage1_load_logic_fix.md` | Clean | **KEEP AS-IS** | None | unchanged |
| `cc_tasks/2026-05-06_v2_stage1_visibility_stopgap.md` | Clean | **KEEP AS-IS** | None | unchanged |

## Why `git restore` is the right tool

Three checks confirm `git restore` is sufficient and surgical here:

1. **All stopgap edits are uncommitted.** Phase 2's uncommitted-only diff (`02_diff_stage1_classify.py.uncommitted.patch`) covers exactly the stopgap edits and nothing else. There are no committed stopgap edits to undo.
2. **All uncommitted edits are stopgap.** Phase 3 reconciliation identified zero uncommitted edits attributable to either in-progress task. Reverting all uncommitted changes therefore preserves all legitimate work.
3. **No staged changes exist.** `git status -s` shows `M` only in the working-tree column, not staged. `--staged --worktree` is included for safety; it is a no-op on the index but ensures both layers are restored if anything has been silently staged.

## Pre-flight (before Phase 5 execution)

Verify that the working-tree diff still matches `02_diff_stage1_classify.py.uncommitted.patch`. If anything has changed in the working tree since Phase 2 was captured, **stop and re-run from Phase 1**.

```bash
diff <(git diff HEAD -- v2/src/core/stage1_classify.py) audit/2026-05-06_v2_stage1_audit/02_diff_stage1_classify.py.uncommitted.patch
```

Expected: empty output (the two diffs match exactly). Any difference means the tree has drifted since Phase 2 and the audit must be restarted.

## Execution sequence (Phase 5 will follow this exactly)

1. Pre-flight check above. Halt if not empty.
2. `git restore --source=HEAD --staged --worktree v2/src/core/stage1_classify.py`
3. Compute SHA-256 of the post-restore file: `shasum -a 256 v2/src/core/stage1_classify.py | awk '{print $1}'`
4. Confirm post-restore SHA-256 equals the committed-blob SHA-256 of HEAD's version of the file (computed directly from the file content).
5. `git status -s` — must show no modifications to `v2/src/core/stage1_classify.py`.
6. `git diff HEAD -- v2/src/core/stage1_classify.py` — must be empty.

If any of steps 3–6 deviate, **halt and surface to human review**. Do NOT proceed to Phase 6.

## What this plan deliberately does NOT do

- Does not touch any cc_task file (cc_tasks are immutable).
- Does not modify `v2/config/stage1.yaml`.
- Does not commit. Phase 5 leaves the working tree clean (matching HEAD) but does not author a new commit. The audit directory commit happens at the end as a separate step per the task's "After Completion" guidance.
- Does not graph-transition the rejected stopgap task `d0f8830a`. Per the audit task: "The blocked stopgap cc_task can stay blocked. Eventually it will be moot when FR-066 ships."
