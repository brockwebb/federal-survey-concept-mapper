# Phase 1 — Inventory (Read-Only)

**Audit:** v2 Stage 1 ground-truth restoration
**Date captured:** 2026-05-06
**HEAD at capture:** `b51f4c4` (`origin/main`)

## Working-tree files

### `v2/config/stage1.yaml`
| Field | Value |
|---|---|
| Path | `v2/config/stage1.yaml` |
| Size (bytes) | 5,885 |
| Line count | 120 |
| SHA-256 | `1cb966e7200c81bce315e4834a405c5d3dede303870da479d1049042f2fac6e5` |
| Last commit touching it | `6e5777b` (2026-05-06 13:36:46 -0400) — "v2: stage1 load logic fix" |
| Uncommitted modifications | None |

### `v2/src/core/stage1_classify.py`
| Field | Value |
|---|---|
| Path | `v2/src/core/stage1_classify.py` |
| Size (bytes) | 37,848 |
| Line count | 958 |
| SHA-256 | `ca8ed307d607a0db7a512d5ae5f7c716f155835c6b6ce4bfbf82a5de30360117` |
| Last commit touching it | `6e5777b` (2026-05-06 13:36:46 -0400) — "v2: stage1 load logic fix" |
| Uncommitted modifications | YES — `git diff --stat HEAD` reports `1 file changed, 21 insertions(+), 1 deletion(-)`; net +20 lines vs HEAD. These working-tree edits are the primary candidate for the rejected stopgap (`d0f8830a`). |

## CC task files (gitignored — no git history)

### `cc_tasks/2026-05-05_v2_stage1_classify.md`
| Field | Value |
|---|---|
| Size (bytes) | 7,829 |
| Line count | 193 |
| SHA-256 | `a35bc08886fa8e50c6cd2f667268310690fa77e246f3fbf612c29f38c74357ce` |
| Last commit | n/a (gitignored) |
| Uncommitted modifications | n/a |

### `cc_tasks/2026-05-06_v2_stage1_load_logic_fix.md`
| Field | Value |
|---|---|
| Size (bytes) | 7,786 |
| Line count | 191 |
| SHA-256 | `18806c7d1c363d830db0efee7eed250ad9949a670a301e0127226788e26933e6` |
| Last commit | n/a (gitignored) |
| Uncommitted modifications | n/a |

### `cc_tasks/2026-05-06_v2_stage1_visibility_stopgap.md`
| Field | Value |
|---|---|
| Size (bytes) | 10,450 |
| Line count | 206 |
| SHA-256 | `5413185333c92d0025dedd88ebbbb20b6d368920da2500f402ef19700931bd67` |
| Last commit | n/a (gitignored) |
| Uncommitted modifications | n/a |

## Summary

- Two of five inventoried files are tracked. The other three are CC task descriptors (gitignored by repo policy).
- Both tracked files were last committed together in `6e5777b`.
- Only `v2/src/core/stage1_classify.py` carries uncommitted working-tree edits (+20 net lines). These are the primary investigation target for Phase 2 and Phase 3.
- All five files exist and are readable; none are corrupted.
