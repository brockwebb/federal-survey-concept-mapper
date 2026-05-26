#!/usr/bin/env python3
"""v2 Stage 2 dashboard: data-driven EDA on the master classification.

Reads Stage 1 + Stage 2 outputs already produced by stage1_compare.py,
stage2_adjudicate.py, and stage2_finalize.py, then writes:

  * 7 data files (JSON/CSV) under output/stage2/dashboard/ that are the
    source of truth for every visual.
  * 4 PNG figures (300 DPI matplotlib) for the Quarto report.
  * One standalone HTML dashboard with the JSON blob embedded so the
    file opens directly in a browser without a server.

Nothing is hardcoded. Paths, thresholds, the Phase 3 survey subset, and
reliability cutoffs all come from config/stage2.yaml. Run from v2/:

    python src/core/stage2_dashboard.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score


CONFIG_PATH = Path("config/stage2.yaml")

# xdgov Data Design Standards — the figures and HTML CSS both reference
# these. Locally defined here because v2 has no src/figures/ tree.
COLOR_NAVY = "#112E51"
COLOR_TEAL = "#0095A8"
COLOR_ORANGE = "#FF7043"
COLOR_GREY = "#78909C"
COLOR_LIGHT_GREY = "#ECEFF1"
COLOR_BORDER = "#CFD8DC"
COLOR_TEXT = "#1A1A1A"
COLOR_MUTED = "#4B636E"


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# CONFIG
# =============================================================================

def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        die(f"Config not found at {CONFIG_PATH.resolve()}. "
            f"Run from the v2/ directory.")
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    required = {"output", "finalize", "stage1_comparison",
                "phase3_surveys", "dashboard"}
    missing = required - set(cfg.keys())
    if missing:
        die(f"Config missing top-level keys: {missing}")
    return cfg


# =============================================================================
# DATA LOADERS
# =============================================================================

def load_v2_master(path: Path) -> pd.DataFrame:
    if not path.exists():
        die(f"v2 master not found at {path.resolve()}. "
            f"Run stage2_finalize.py first.")
    df = pd.read_csv(path)
    for col in ("id", "primary_survey", "final_topic",
                "final_subtopic", "decision_method"):
        if col not in df.columns:
            die(f"v2 master missing column {col!r}")
    df["id"] = df["id"].astype(int)
    return df


def load_v1_master(path: Path) -> pd.DataFrame:
    if not path.exists():
        die(f"v1 master not found at {path.resolve()}")
    df = pd.read_csv(path)
    needed = ["id", "final_topic", "final_subtopic", "decision_method",
              "primary_survey"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        die(f"v1 master missing columns: {missing}")
    df = df[needed].copy()
    df["id"] = df["id"].astype(int)
    return df.rename(columns={
        "final_topic": "v1_final_topic",
        "final_subtopic": "v1_final_subtopic",
        "decision_method": "v1_decision_method",
        "primary_survey": "v1_primary_survey",
    })


def load_resolutions(path: Path) -> pd.DataFrame:
    if not path.exists():
        die(f"Resolutions CSV not found at {path.resolve()}")
    df = pd.read_csv(path)
    if "decision" not in df.columns:
        die("Resolutions CSV missing 'decision' column")
    return df


def load_changed(path: Path) -> pd.DataFrame:
    if not path.exists():
        die(f"Changed-questions CSV not found at {path.resolve()}. "
            f"Run stage2_finalize.py first.")
    return pd.read_csv(path)


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        die(f"{label}: JSON not found at {path.resolve()}")
    return json.loads(path.read_text(encoding="utf-8"))


# =============================================================================
# JOINED v1+v2 (the reference frame for migration/per-survey analysis)
# =============================================================================

UNRESOLVABLE = "Unresolvable"


def build_joined(v2_master: pd.DataFrame, v1: pd.DataFrame) -> pd.DataFrame:
    j = v2_master[
        ["id", "primary_survey", "final_topic", "final_subtopic",
         "decision_method"]
    ].rename(columns={
        "final_topic": "v2_final_topic",
        "final_subtopic": "v2_final_subtopic",
        "decision_method": "v2_decision_method",
    }).merge(v1, on="id", how="inner", validate="one_to_one")

    # Same null-normalization as stage2_finalize.compare_v1_v2 so kappa
    # is computable and "both unresolvable" counts as a match.
    for col in ["v1_final_topic", "v2_final_topic",
                "v1_final_subtopic", "v2_final_subtopic"]:
        j[col] = j[col].fillna(UNRESOLVABLE)
    return j


# =============================================================================
# COMPUTE: per-section data products
# =============================================================================

def compute_interrater_matrix(stage1_summary: dict[str, Any]) -> list[dict]:
    """Project the stage1 comparison summary into a flat table."""
    rows: list[dict[str, Any]] = []
    for c in stage1_summary.get("comparisons", []):
        topic = c.get("topic", {}) or {}
        sub = c.get("subtopic", {}) or {}
        rows.append({
            "pair": c.get("pair") or c.get("comparison") or "?",
            "n": int(topic.get("n", 0)),
            "topic_agreement_pct": topic.get("raw_agreement_pct"),
            "topic_kappa": topic.get("kappa"),
            "subtopic_agreement_pct": sub.get("raw_agreement_pct"),
            "subtopic_kappa": sub.get("kappa"),
        })
    return rows


def compute_change_decomposition(
    joined: pd.DataFrame,
    resolutions: pd.DataFrame,
) -> dict[str, Any]:
    topic_diff = joined["v1_final_topic"] != joined["v2_final_topic"]
    sub_diff = joined["v1_final_subtopic"] != joined["v2_final_subtopic"]
    changed = topic_diff | sub_diff
    topic_driven = int(topic_diff.sum())
    subtopic_only = int((~topic_diff & sub_diff).sum())
    total_changed = int(changed.sum())

    if "confidence_tier" in resolutions.columns:
        tier_counts = (
            resolutions["confidence_tier"].fillna("unknown")
            .value_counts().to_dict()
        )
    else:
        tier_counts = {}

    return {
        "changed_total": total_changed,
        "topic_driven": topic_driven,
        "subtopic_only": subtopic_only,
        "topic_driven_pct": round(
            100.0 * topic_driven / total_changed, 2,
        ) if total_changed else 0.0,
        "subtopic_only_pct": round(
            100.0 * subtopic_only / total_changed, 2,
        ) if total_changed else 0.0,
        "adjudication_outcomes": {
            str(k): int(v)
            for k, v in resolutions["decision"].value_counts().items()
        },
        "confidence_tiers": {str(k): int(v) for k, v in tier_counts.items()},
        "resolutions_total": int(len(resolutions)),
    }


def compute_topic_migration(joined: pd.DataFrame) -> pd.DataFrame:
    """v1 topic (rows) x v2 topic (cols) count matrix, no margins."""
    return pd.crosstab(
        joined["v1_final_topic"], joined["v2_final_topic"],
    )


def compute_subtopic_migrations(joined: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Top-N subtopic-only migration pairs (topic matched, subtopic shifted)."""
    mask = (
        (joined["v1_final_topic"] == joined["v2_final_topic"])
        & (joined["v1_final_subtopic"] != joined["v2_final_subtopic"])
    )
    sub = joined[mask].copy()
    if not len(sub):
        return pd.DataFrame(
            columns=["v1_subtopic", "v2_subtopic", "count", "pct"]
        )
    g = (sub.groupby(["v1_final_subtopic", "v2_final_subtopic"])
         .size().reset_index(name="count"))
    g = g.rename(columns={
        "v1_final_subtopic": "v1_subtopic",
        "v2_final_subtopic": "v2_subtopic",
    })
    total = int(g["count"].sum())
    g["pct"] = (g["count"] / total * 100.0).round(2) if total else 0.0
    g = g.sort_values("count", ascending=False).head(top_n).reset_index(drop=True)
    return g


def compute_per_survey_stability(
    joined: pd.DataFrame,
    surveys: list[str],
) -> pd.DataFrame:
    """For each survey in `surveys`, compute n, topic% agreement,
    subtopic% agreement, full% agreement, and kappas."""
    rows: list[dict[str, Any]] = []
    for s in surveys:
        sub = joined[joined["primary_survey"] == s]
        n = len(sub)
        if n == 0:
            rows.append({
                "survey": s, "n": 0,
                "topic_agree_pct": None, "subtopic_agree_pct": None,
                "full_agree_pct": None,
                "topic_kappa": None, "subtopic_kappa": None,
            })
            continue
        tm = (sub["v1_final_topic"] == sub["v2_final_topic"])
        sm = (sub["v1_final_subtopic"] == sub["v2_final_subtopic"])
        # Kappa needs >=2 distinct labels on each side; fall back to None.
        def _k(a: pd.Series, b: pd.Series) -> float | None:
            try:
                if a.nunique() < 2 or b.nunique() < 2:
                    return None
                return round(float(cohen_kappa_score(a, b)), 4)
            except Exception:
                return None
        rows.append({
            "survey": s, "n": n,
            "topic_agree_pct": round(100.0 * float(tm.mean()), 2),
            "subtopic_agree_pct": round(100.0 * float(sm.mean()), 2),
            "full_agree_pct": round(100.0 * float((tm & sm).mean()), 2),
            "topic_kappa": _k(sub["v1_final_topic"], sub["v2_final_topic"]),
            "subtopic_kappa": _k(
                sub["v1_final_subtopic"], sub["v2_final_subtopic"]),
        })
    df = pd.DataFrame(rows)
    if "subtopic_agree_pct" in df.columns:
        df = df.sort_values(
            "subtopic_agree_pct", ascending=False, na_position="last",
        ).reset_index(drop=True)
    return df


def compute_reliability(
    per_survey: pd.DataFrame, thresholds: dict[str, float],
) -> pd.DataFrame:
    tr = float(thresholds["topic_reliable_pct"])
    tm = float(thresholds["topic_marginal_pct"])
    sr = float(thresholds["subtopic_reliable_pct"])
    sm = float(thresholds["subtopic_marginal_pct"])

    def verdict(pct: float | None, hi: float, lo: float) -> str:
        if pct is None or pd.isna(pct):
            return "n/a"
        if pct >= hi:
            return "✓ Reliable"
        if pct >= lo:
            return "⚠ Marginal"
        return "✗ Unreliable"

    def overall(topic_v: str, sub_v: str) -> str:
        if topic_v == "✓ Reliable" and sub_v == "✓ Reliable":
            return "Full confidence"
        if topic_v == "✓ Reliable" and sub_v == "⚠ Marginal":
            return "Use topic-level or normalize subtopics"
        if "✗" in topic_v or "✗" in sub_v:
            return "Exclude or caveat heavily"
        return "Use topic-level only"

    rows: list[dict[str, Any]] = []
    for _, r in per_survey.iterrows():
        tv = verdict(r["topic_agree_pct"], tr, tm)
        sv = verdict(r["subtopic_agree_pct"], sr, sm)
        rows.append({
            "survey": r["survey"],
            "n": int(r["n"]),
            "topic_agree_pct": r["topic_agree_pct"],
            "subtopic_agree_pct": r["subtopic_agree_pct"],
            "topic_verdict": tv,
            "subtopic_verdict": sv,
            "overall": overall(tv, sv),
        })
    return pd.DataFrame(rows)


# =============================================================================
# FIGURES (matplotlib)
# =============================================================================

def _serif_rc() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Palatino", "Palatino Linotype", "Book Antiqua",
                       "DejaVu Serif", "Bitstream Vera Serif", "serif"],
        "axes.edgecolor": COLOR_MUTED,
        "axes.labelcolor": COLOR_TEXT,
        "xtick.color": COLOR_MUTED,
        "ytick.color": COLOR_MUTED,
        "axes.titleweight": "bold",
        "axes.titlecolor": COLOR_NAVY,
        "savefig.dpi": 300,
        "figure.dpi": 120,
    })


def fig_change_decomposition(decomp: dict[str, Any], out: Path) -> None:
    _serif_rc()
    fig, ax = plt.subplots(figsize=(8, 1.6))
    td = decomp["topic_driven"]
    so = decomp["subtopic_only"]
    total = max(td + so, 1)
    ax.barh([0], [td], color=COLOR_NAVY, edgecolor="white",
            label=f"Topic-driven  ({td:,} · {100*td/total:.1f}%)")
    ax.barh([0], [so], left=[td], color=COLOR_TEAL, edgecolor="white",
            label=f"Subtopic-only ({so:,} · {100*so/total:.1f}%)")
    ax.set_xlim(0, total)
    ax.set_yticks([])
    ax.set_xlabel("Changed questions (v1 → v2)")
    ax.set_title("Change decomposition")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.6),
              ncol=2, frameon=False)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_topic_migration_heatmap(crosstab: pd.DataFrame, out: Path) -> None:
    _serif_rc()
    M = crosstab.to_numpy()
    rows, cols = crosstab.index.tolist(), crosstab.columns.tolist()
    fig, ax = plt.subplots(figsize=(max(6, 0.8 * len(cols) + 2),
                                    max(4, 0.6 * len(rows) + 2)))
    im = ax.imshow(M, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(rows)))
    ax.set_xticklabels(cols, rotation=35, ha="right")
    ax.set_yticklabels(rows)
    ax.set_xlabel("v2 topic")
    ax.set_ylabel("v1 topic")
    ax.set_title("Topic migration matrix (full population)")
    # Annotate every cell
    if len(M):
        vmax = float(M.max())
    else:
        vmax = 1.0
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            val = int(M[i, j])
            if val == 0:
                continue
            color = "white" if val > 0.6 * vmax else COLOR_TEXT
            ax.text(j, i, f"{val:,}", ha="center", va="center",
                    color=color, fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label="count")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_per_survey_stability(per_survey: pd.DataFrame, out: Path) -> None:
    _serif_rc()
    df = per_survey.dropna(subset=["subtopic_agree_pct"]).copy()
    df = df.sort_values("subtopic_agree_pct", ascending=True)
    y = np.arange(len(df))
    bar_h = 0.38
    fig, ax = plt.subplots(figsize=(8.0, max(2.5, 0.55 * len(df) + 1.5)))
    ax.barh(y - bar_h / 2, df["topic_agree_pct"], height=bar_h,
            color=COLOR_NAVY, label="Topic %")
    ax.barh(y + bar_h / 2, df["subtopic_agree_pct"], height=bar_h,
            color=COLOR_TEAL, label="Subtopic %")
    ax.set_yticks(y)
    # Truncate long survey names
    ax.set_yticklabels(
        [s if len(s) < 48 else s[:46] + "…" for s in df["survey"]]
    )
    ax.set_xlabel("Agreement % (v1 vs v2)")
    ax.set_xlim(0, 100)
    ax.set_title("Per-survey stability — Phase 3 subset")
    ax.legend(loc="lower right", frameon=False)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_subtopic_top20(top: pd.DataFrame, out: Path) -> None:
    _serif_rc()
    df = top.copy()
    if not len(df):
        # write a tiny placeholder rather than crashing
        fig, ax = plt.subplots(figsize=(6, 1.5))
        ax.text(0.5, 0.5, "No subtopic-only migrations",
                ha="center", va="center", color=COLOR_MUTED)
        ax.axis("off")
        fig.savefig(out, bbox_inches="tight")
        plt.close(fig)
        return

    # ASCII arrow -- the serif fallback fonts don't carry U+2192 reliably.
    labels = [f"{r['v1_subtopic']}  ->  {r['v2_subtopic']}"
              for _, r in df.iterrows()]
    counts = df["count"].to_numpy()
    fig, ax = plt.subplots(figsize=(8.0, max(3.5, 0.32 * len(df) + 1.5)))
    y = np.arange(len(df))
    ax.barh(y, counts, color=COLOR_TEAL)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Count")
    ax.set_title(f"Top {len(df)} subtopic-only migrations (full population)")
    for i, c in enumerate(counts):
        ax.text(c + max(counts) * 0.01, i, f"{int(c):,}",
                va="center", fontsize=8, color=COLOR_TEXT)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


# =============================================================================
# HTML RENDERING
# =============================================================================

HTML_CSS = """
:root {
  --navy: #112E51;
  --teal: #0095A8;
  --orange: #FF7043;
  --grey: #78909C;
  --light: #ECEFF1;
  --border: #CFD8DC;
  --text: #1A1A1A;
  --muted: #4B636E;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Source Sans 3", system-ui, sans-serif;
  color: var(--text);
  background: #FFFFFF;
  line-height: 1.45;
  font-size: 15px;
}
.container { max-width: 1180px; margin: 0 auto; padding: 32px 28px 80px; }
header { border-bottom: 3px solid var(--navy); padding-bottom: 16px; margin-bottom: 24px; }
header h1 { font-family: "Source Serif 4", Georgia, serif;
            font-weight: 700; color: var(--navy);
            margin: 0 0 4px; font-size: 28px; }
header .subtitle { color: var(--muted); font-size: 14px; }
h2 { font-family: "Source Serif 4", Georgia, serif;
     color: var(--navy); border-bottom: 1px solid var(--border);
     padding-bottom: 4px; margin-top: 36px; font-size: 21px; }
h3 { font-family: "Source Serif 4", Georgia, serif;
     color: var(--navy); margin-top: 18px; font-size: 17px; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 14px; margin: 18px 0 8px; }
.kpi { border: 1px solid var(--border); border-left: 4px solid var(--teal);
       padding: 12px 14px; background: #FAFCFD; }
.kpi .label { font-size: 12px; color: var(--muted); text-transform: uppercase;
              letter-spacing: 0.04em; }
.kpi .value { font-family: "IBM Plex Mono", "Menlo", monospace;
              font-size: 24px; color: var(--navy); margin-top: 2px; }
.kpi .note  { font-family: "IBM Plex Mono", "Menlo", monospace;
              font-size: 12px; color: var(--muted); margin-top: 2px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0 18px;
        font-size: 14px; }
th, td { border: 1px solid var(--border); padding: 6px 10px;
         text-align: right; }
th { background: var(--light); color: var(--navy);
     font-family: "Source Serif 4", Georgia, serif; font-weight: 700; }
td.txt, th.txt { text-align: left; }
td.num { font-family: "IBM Plex Mono", "Menlo", monospace; }
td.hot { background: #DCEEFB; font-weight: 600; }
td.diag { background: #F1F5F8; color: var(--muted); }
td.unre { color: var(--orange); font-weight: 600; }
.bar-cell { position: relative; }
.bar { display: inline-block; height: 10px; background: var(--teal);
       vertical-align: middle; margin-right: 6px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.verdict-ok   { color: #2E7D32; font-weight: 600; }
.verdict-warn { color: #B26A00; font-weight: 600; }
.verdict-bad  { color: #C62828; font-weight: 600; }
.verdict-na   { color: var(--muted); }
figure { margin: 14px 0 24px; }
figure img { max-width: 100%; height: auto;
             border: 1px solid var(--border); padding: 4px;
             background: white; }
figcaption { font-size: 12px; color: var(--muted); margin-top: 6px; }
footer { margin-top: 48px; padding-top: 16px;
         border-top: 1px solid var(--border);
         font-size: 12px; color: var(--muted); }
@media print {
  body { font-size: 11px; }
  .container { padding: 10px; max-width: 100%; }
  h2 { page-break-after: avoid; }
  table { page-break-inside: avoid; }
}
"""

HTML_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Source+Serif+4:wght@400;600;700&'
    'family=Source+Sans+3:wght@400;600&'
    'family=IBM+Plex+Mono:wght@400;600&display=swap">'
)


def _fmt_pct(x: Any) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{float(x):.2f}%"


def _fmt_k(x: Any) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{float(x):.3f}"


def _fmt_int(x: Any) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{int(x):,}"


def _verdict_class(v: str) -> str:
    if v.startswith("✓"):
        return "verdict-ok"
    if v.startswith("⚠"):
        return "verdict-warn"
    if v.startswith("✗"):
        return "verdict-bad"
    return "verdict-na"


def render_kpis(data: dict[str, Any]) -> str:
    s = data["comparison_summary"]
    decomp = data["change_decomposition"]
    parts = []
    parts.append('<section class="kpis">')
    parts.append(
        f'<div class="kpi"><div class="label">Topic agreement</div>'
        f'<div class="value">{_fmt_pct(s["topic_agreement_pct"])}</div>'
        f'<div class="note">κ = {_fmt_k(s["topic_kappa"])}</div></div>'
    )
    parts.append(
        f'<div class="kpi"><div class="label">Subtopic agreement</div>'
        f'<div class="value">{_fmt_pct(s["subtopic_agreement_pct"])}</div>'
        f'<div class="note">κ = {_fmt_k(s["subtopic_kappa"])}</div></div>'
    )
    parts.append(
        f'<div class="kpi"><div class="label">Full agreement</div>'
        f'<div class="value">{_fmt_pct(s["full_agreement_pct"])}</div>'
        f'<div class="note">topic+subtopic match</div></div>'
    )
    parts.append(
        f'<div class="kpi"><div class="label">Changed questions</div>'
        f'<div class="value">{_fmt_int(decomp["changed_total"])}</div>'
        f'<div class="note">of {_fmt_int(s["n_compared"])} compared</div></div>'
    )
    parts.append(
        f'<div class="kpi"><div class="label">Unresolvable (v1 → v2)</div>'
        f'<div class="value">{_fmt_int(s["v1_unresolvable"])} → '
        f'{_fmt_int(s["v2_unresolvable"])}</div>'
        f'<div class="note">Δ = {s["unresolvable_delta"]:+d}</div></div>'
    )
    parts.append("</section>")
    return "".join(parts)


def render_interrater(matrix: list[dict]) -> str:
    if not matrix:
        return ('<h2>Stage 1 Inter-Rater Agreement</h2>'
                '<p>No comparisons in summary.</p>')
    L = ['<h2>Stage 1 Inter-Rater Agreement</h2>',
         '<table><thead><tr>',
         '<th class="txt">Pair</th><th>n</th>',
         '<th>Topic %</th><th>Topic κ</th>',
         '<th>Subtopic %</th><th>Subtopic κ</th>',
         '</tr></thead><tbody>']
    for r in matrix:
        L.append(
            f'<tr><td class="txt">{r["pair"]}</td>'
            f'<td class="num">{_fmt_int(r["n"])}</td>'
            f'<td class="num">{_fmt_pct(r["topic_agreement_pct"])}</td>'
            f'<td class="num">{_fmt_k(r["topic_kappa"])}</td>'
            f'<td class="num">{_fmt_pct(r["subtopic_agreement_pct"])}</td>'
            f'<td class="num">{_fmt_k(r["subtopic_kappa"])}</td></tr>'
        )
    L.append('</tbody></table>')
    return "".join(L)


def render_decomposition(decomp: dict[str, Any], fig_rel: str) -> str:
    L = ['<h2>Disagreement Decomposition</h2>',
         f'<figure><img src="{fig_rel}" alt="Change decomposition">'
         f'<figcaption>Topic-driven vs subtopic-only of '
         f'{decomp["changed_total"]:,} changed questions.</figcaption></figure>',
         '<div class="two-col"><div>',
         '<h3>Adjudication outcomes</h3>',
         '<table><thead><tr><th class="txt">Decision</th><th>Count</th>'
         '<th>% of resolutions</th></tr></thead><tbody>']
    total = max(decomp["resolutions_total"], 1)
    for k, v in sorted(decomp["adjudication_outcomes"].items(),
                       key=lambda kv: -kv[1]):
        L.append(
            f'<tr><td class="txt">{k}</td>'
            f'<td class="num">{_fmt_int(v)}</td>'
            f'<td class="num">{100*v/total:.2f}%</td></tr>'
        )
    L.append('</tbody></table></div><div>')
    L.append('<h3>Confidence tiers (disagreements)</h3>')
    L.append('<table><thead><tr><th class="txt">Tier</th><th>Count</th>'
             '<th>% of resolutions</th></tr></thead><tbody>')
    tiers_in_order = ["very_low", "low", "medium", "high", "very_high",
                      "unknown"]
    tiers = decomp["confidence_tiers"]
    seen = set()
    for t in tiers_in_order:
        if t in tiers:
            v = tiers[t]; seen.add(t)
            L.append(
                f'<tr><td class="txt">{t}</td>'
                f'<td class="num">{_fmt_int(v)}</td>'
                f'<td class="num">{100*v/total:.2f}%</td></tr>'
            )
    for t, v in tiers.items():
        if t in seen:
            continue
        L.append(
            f'<tr><td class="txt">{t}</td>'
            f'<td class="num">{_fmt_int(v)}</td>'
            f'<td class="num">{100*v/total:.2f}%</td></tr>'
        )
    L.append('</tbody></table></div></div>')
    return "".join(L)


def render_topic_migration_table(
    crosstab: pd.DataFrame,
    title: str,
    highlight_threshold: int,
    fig_rel: str | None = None,
) -> str:
    L = [f'<h2>{title}</h2>']
    if fig_rel:
        L.append(f'<figure><img src="{fig_rel}" alt="{title}">'
                 f'<figcaption>Counts; '
                 f'cells ≥ {highlight_threshold} highlighted in table.'
                 f'</figcaption></figure>')
    cols = crosstab.columns.tolist()
    L.append('<table><thead><tr><th class="txt">v1 \\ v2</th>')
    for c in cols:
        L.append(f'<th>{c}</th>')
    L.append('<th>Σ</th></tr></thead><tbody>')
    row_totals = crosstab.sum(axis=1)
    for idx in crosstab.index:
        L.append(f'<tr><td class="txt">{idx}</td>')
        for c in cols:
            v = int(crosstab.loc[idx, c])
            cls = "num"
            if idx == c:
                cls += " diag"
            elif v >= highlight_threshold:
                cls += " hot"
            label = f'{v:,}' if v else '—'
            if idx == UNRESOLVABLE or c == UNRESOLVABLE:
                if v:
                    cls += " unre"
            L.append(f'<td class="{cls}">{label}</td>')
        L.append(f'<td class="num">{int(row_totals[idx]):,}</td></tr>')
    col_totals = crosstab.sum(axis=0)
    L.append('<tr><td class="txt"><b>Σ</b></td>')
    for c in cols:
        L.append(f'<td class="num">{int(col_totals[c]):,}</td>')
    L.append(f'<td class="num"><b>{int(crosstab.values.sum()):,}</b></td>'
             '</tr></tbody></table>')
    return "".join(L)


def render_subtopic_table(df: pd.DataFrame, title: str,
                          fig_rel: str | None = None) -> str:
    L = [f'<h2>{title}</h2>']
    if fig_rel:
        L.append(f'<figure><img src="{fig_rel}" alt="{title}">'
                 f'<figcaption>Subtopic shifts within a stable topic.'
                 f'</figcaption></figure>')
    if not len(df):
        L.append('<p>No subtopic-only migrations.</p>')
        return "".join(L)
    L.append('<table><thead><tr><th class="txt">v1 subtopic</th>'
             '<th class="txt">v2 subtopic</th><th>Count</th>'
             '<th>% of subtopic-only</th></tr></thead><tbody>')
    max_count = int(df["count"].max())
    for _, r in df.iterrows():
        bar_w = max(2, int(100 * r["count"] / max_count)) if max_count else 0
        L.append(
            f'<tr><td class="txt">{r["v1_subtopic"]}</td>'
            f'<td class="txt">{r["v2_subtopic"]}</td>'
            f'<td class="num">{int(r["count"]):,}</td>'
            f'<td class="bar-cell num">'
            f'<span class="bar" style="width:{bar_w}px"></span>'
            f'{r["pct"]:.2f}%</td></tr>'
        )
    L.append('</tbody></table>')
    return "".join(L)


def render_per_survey(df: pd.DataFrame, fig_rel: str) -> str:
    L = ['<h2>Phase 3 Subset — Per-Survey Stability</h2>',
         f'<figure><img src="{fig_rel}" alt="Per-survey stability">'
         '<figcaption>Topic (navy) and subtopic (teal) agreement '
         'between v1 and v2 within the Phase 3 subset.</figcaption></figure>',
         '<table><thead><tr><th class="txt">Survey</th><th>n</th>'
         '<th>Topic %</th><th>Subtopic %</th><th>Full %</th>'
         '<th>Topic κ</th><th>Subtopic κ</th></tr></thead><tbody>']
    for _, r in df.iterrows():
        L.append(
            f'<tr><td class="txt">{r["survey"]}</td>'
            f'<td class="num">{_fmt_int(r["n"])}</td>'
            f'<td class="num">{_fmt_pct(r["topic_agree_pct"])}</td>'
            f'<td class="num">{_fmt_pct(r["subtopic_agree_pct"])}</td>'
            f'<td class="num">{_fmt_pct(r["full_agree_pct"])}</td>'
            f'<td class="num">{_fmt_k(r["topic_kappa"])}</td>'
            f'<td class="num">{_fmt_k(r["subtopic_kappa"])}</td></tr>'
        )
    L.append('</tbody></table>')
    return "".join(L)


def render_assessment(df: pd.DataFrame, thresholds: dict[str, float]) -> str:
    L = ['<h2>Reliability Assessment</h2>',
         f'<p style="color:var(--muted);font-size:13px;">'
         f'Topic verdicts: ≥{thresholds["topic_reliable_pct"]}% Reliable, '
         f'≥{thresholds["topic_marginal_pct"]}% Marginal, otherwise Unreliable. '
         f'Subtopic verdicts: ≥{thresholds["subtopic_reliable_pct"]}% Reliable, '
         f'≥{thresholds["subtopic_marginal_pct"]}% Marginal, otherwise Unreliable.'
         f'</p>',
         '<table><thead><tr><th class="txt">Survey</th><th>n</th>'
         '<th>Topic %</th><th>Subtopic %</th>'
         '<th class="txt">Topic verdict</th>'
         '<th class="txt">Subtopic verdict</th>'
         '<th class="txt">Overall</th></tr></thead><tbody>']
    for _, r in df.iterrows():
        L.append(
            f'<tr><td class="txt">{r["survey"]}</td>'
            f'<td class="num">{_fmt_int(r["n"])}</td>'
            f'<td class="num">{_fmt_pct(r["topic_agree_pct"])}</td>'
            f'<td class="num">{_fmt_pct(r["subtopic_agree_pct"])}</td>'
            f'<td class="txt {_verdict_class(r["topic_verdict"])}">'
            f'{r["topic_verdict"]}</td>'
            f'<td class="txt {_verdict_class(r["subtopic_verdict"])}">'
            f'{r["subtopic_verdict"]}</td>'
            f'<td class="txt">{r["overall"]}</td></tr>'
        )
    L.append('</tbody></table>')
    return "".join(L)


def render_html(data: dict[str, Any], fig_paths: dict[str, str],
                thresholds: dict[str, float], n_questions: int) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title = "v2 Stage 2 Dashboard"
    subtitle = (f"{n_questions:,} questions  ·  v1 vs v2 final "
                f"classification  ·  generated {generated}")

    body = [
        '<div class="container">',
        f'<header><h1>{title}</h1>'
        f'<div class="subtitle">{subtitle}</div></header>',
        render_kpis(data),
        render_interrater(data["interrater_matrix"]),
        render_decomposition(data["change_decomposition"],
                             fig_paths["change_decomposition"]),
        render_topic_migration_table(
            data["topic_migration_full_df"],
            "Topic Migration Matrix (Full Population)",
            data["highlight_threshold"],
            fig_rel=fig_paths["topic_migration_heatmap"],
        ),
        render_subtopic_table(
            data["subtopic_migrations_full_df"],
            "Top Subtopic Migrations (Full Population)",
            fig_rel=fig_paths["subtopic_top20"],
        ),
        render_per_survey(
            data["per_survey_stability_df"],
            fig_paths["per_survey_stability"],
        ),
        render_topic_migration_table(
            data["topic_migration_subset_df"],
            "Phase 3 Topic Migration",
            data["highlight_threshold"],
        ),
        render_subtopic_table(
            data["subtopic_migrations_subset_df"],
            "Phase 3 Subtopic Migrations",
        ),
        render_assessment(data["reliability_df"], thresholds),
        '<footer>Generated by '
        '<code>v2/src/core/stage2_dashboard.py</code>. '
        'All numbers, tables, and figures are computed from '
        '<code>output/stage2/</code> data files at run time. '
        'See <code>dashboard_data.json</code> for the embedded blob.'
        '</footer>',
        '</div>',
    ]

    # Build the DATA blob. DataFrames go to records for JSON.
    embed = {
        "comparison_summary": data["comparison_summary"],
        "interrater_matrix": data["interrater_matrix"],
        "change_decomposition": data["change_decomposition"],
        "topic_migration_full": data["topic_migration_full_df"]
            .reset_index().to_dict(orient="records"),
        "topic_migration_subset": data["topic_migration_subset_df"]
            .reset_index().to_dict(orient="records"),
        "subtopic_migrations_full": data["subtopic_migrations_full_df"]
            .to_dict(orient="records"),
        "subtopic_migrations_subset": data["subtopic_migrations_subset_df"]
            .to_dict(orient="records"),
        "per_survey_stability": data["per_survey_stability_df"]
            .to_dict(orient="records"),
        "reliability": data["reliability_df"].to_dict(orient="records"),
        "generated": generated,
    }

    return (
        '<!doctype html>'
        '<html lang="en"><head><meta charset="utf-8">'
        f'<title>{title}</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        + HTML_FONTS
        + f'<style>{HTML_CSS}</style></head><body>'
        + "".join(body)
        + '<script>const DATA = '
        + json.dumps(embed, default=str)
        + ';</script>'
        + '</body></html>'
    )


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    cfg = load_config()
    fin = cfg["finalize"]
    out_root = Path(cfg["output"]["output_dir"])
    dash_cfg = cfg["dashboard"]
    dash_dir = out_root / dash_cfg["output_subdir"]
    dash_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("v2 STAGE 2 DASHBOARD")
    print("=" * 70)

    # ----- Load inputs -------------------------------------------------------
    print("\n1. Loading inputs...")
    v2_master = load_v2_master(out_root / fin["v2_master"])
    print(f"   v2 master: {len(v2_master)} rows")
    v1 = load_v1_master(Path(fin["v1_master"]))
    print(f"   v1 master: {len(v1)} rows")
    resolutions = load_resolutions(
        out_root / cfg["output"]["all_resolutions_csv"]
    )
    print(f"   resolutions: {len(resolutions)} rows")
    changed = load_changed(out_root / fin["changed_questions_csv"])
    print(f"   changed:    {len(changed)} rows")
    v1v2_summary = load_json(
        out_root / fin["comparison_summary_json"], "v1_v2 summary",
    )
    stage1_summary = load_json(
        Path(cfg["stage1_comparison"]["summary_json"]), "stage1 summary",
    )

    joined = build_joined(v2_master, v1)
    print(f"   joined:     {len(joined)} rows")

    # ----- Compute data products --------------------------------------------
    print("\n2. Computing data products...")
    interrater = compute_interrater_matrix(stage1_summary)
    decomp = compute_change_decomposition(joined, resolutions)
    topic_full = compute_topic_migration(joined)
    surveys = list(cfg["phase3_surveys"])
    subset = joined[joined["primary_survey"].isin(surveys)].copy()
    topic_subset = compute_topic_migration(subset)
    subtopic_full = compute_subtopic_migrations(
        joined, int(dash_cfg["subtopic_top_n_full"]),
    )
    subtopic_subset = compute_subtopic_migrations(
        subset, int(dash_cfg["subtopic_top_n_subset"]),
    )
    per_survey = compute_per_survey_stability(joined, surveys)
    reliability = compute_reliability(per_survey, dash_cfg["reliability"])

    # ----- Write data files --------------------------------------------------
    print("\n3. Writing data files...")
    df = dash_cfg["data_files"]
    (dash_dir / df["interrater_matrix"]).write_text(
        json.dumps(interrater, indent=2, default=str), encoding="utf-8",
    )
    print(f"   wrote {dash_dir / df['interrater_matrix']}")
    (dash_dir / df["change_decomposition"]).write_text(
        json.dumps(decomp, indent=2, default=str), encoding="utf-8",
    )
    print(f"   wrote {dash_dir / df['change_decomposition']}")

    topic_full.to_csv(dash_dir / df["topic_migration_full"], encoding="utf-8")
    print(f"   wrote {dash_dir / df['topic_migration_full']}")
    topic_subset.to_csv(dash_dir / df["topic_migration_subset"], encoding="utf-8")
    print(f"   wrote {dash_dir / df['topic_migration_subset']}")
    subtopic_full.to_csv(
        dash_dir / df["subtopic_migrations_full"],
        index=False, encoding="utf-8",
    )
    print(f"   wrote {dash_dir / df['subtopic_migrations_full']}")
    subtopic_subset.to_csv(
        dash_dir / df["subtopic_migrations_subset"],
        index=False, encoding="utf-8",
    )
    print(f"   wrote {dash_dir / df['subtopic_migrations_subset']}")
    per_survey.to_csv(
        dash_dir / df["per_survey_stability"],
        index=False, encoding="utf-8",
    )
    print(f"   wrote {dash_dir / df['per_survey_stability']}")

    # ----- Figures -----------------------------------------------------------
    print("\n4. Generating figures...")
    figs = dash_cfg["figures"]
    fig_change_decomposition(decomp, dash_dir / figs["change_decomposition"])
    print(f"   wrote {dash_dir / figs['change_decomposition']}")
    fig_topic_migration_heatmap(
        topic_full, dash_dir / figs["topic_migration_heatmap"],
    )
    print(f"   wrote {dash_dir / figs['topic_migration_heatmap']}")
    fig_per_survey_stability(
        per_survey, dash_dir / figs["per_survey_stability"],
    )
    print(f"   wrote {dash_dir / figs['per_survey_stability']}")
    fig_subtopic_top20(subtopic_full, dash_dir / figs["subtopic_top20"])
    print(f"   wrote {dash_dir / figs['subtopic_top20']}")

    # ----- Combined JSON blob + HTML ----------------------------------------
    data = {
        "comparison_summary": v1v2_summary,
        "interrater_matrix": interrater,
        "change_decomposition": decomp,
        "topic_migration_full_df": topic_full,
        "topic_migration_subset_df": topic_subset,
        "subtopic_migrations_full_df": subtopic_full,
        "subtopic_migrations_subset_df": subtopic_subset,
        "per_survey_stability_df": per_survey,
        "reliability_df": reliability,
        "highlight_threshold": int(
            dash_cfg["topic_migration_highlight_threshold"]
        ),
    }

    fig_rels = {k: v for k, v in dash_cfg["figures"].items()}
    html = render_html(data, fig_rels, dash_cfg["reliability"], len(v2_master))
    html_path = dash_dir / dash_cfg["html_filename"]
    html_path.write_text(html, encoding="utf-8")
    print(f"\n5. Wrote HTML dashboard: {html_path}")

    combined_path = dash_dir / df["combined_json"]
    combined_blob = {
        "comparison_summary": v1v2_summary,
        "interrater_matrix": interrater,
        "change_decomposition": decomp,
        "topic_migration_full": topic_full.reset_index()
            .to_dict(orient="records"),
        "topic_migration_subset": topic_subset.reset_index()
            .to_dict(orient="records"),
        "subtopic_migrations_full": subtopic_full.to_dict(orient="records"),
        "subtopic_migrations_subset": subtopic_subset.to_dict(orient="records"),
        "per_survey_stability": per_survey.to_dict(orient="records"),
        "reliability": reliability.to_dict(orient="records"),
        "config_snapshot": {
            "phase3_surveys": surveys,
            "reliability_thresholds": dash_cfg["reliability"],
            "subtopic_top_n_full": int(dash_cfg["subtopic_top_n_full"]),
            "subtopic_top_n_subset": int(dash_cfg["subtopic_top_n_subset"]),
            "highlight_threshold": int(
                dash_cfg["topic_migration_highlight_threshold"]
            ),
        },
    }
    combined_path.write_text(
        json.dumps(combined_blob, indent=2, default=str), encoding="utf-8",
    )
    print(f"   wrote {combined_path}")

    print("\n" + "=" * 70)
    print("HEADLINE")
    print("=" * 70)
    s = v1v2_summary
    print(f"  topic agreement:    {s.get('topic_agreement_pct')}%   "
          f"κ={s.get('topic_kappa')}")
    print(f"  subtopic agreement: {s.get('subtopic_agreement_pct')}%   "
          f"κ={s.get('subtopic_kappa')}")
    print(f"  changed questions:  {decomp['changed_total']:,}")
    print(f"  topic-driven:       {decomp['topic_driven']:,} "
          f"({decomp['topic_driven_pct']}%)")
    print(f"  subtopic-only:      {decomp['subtopic_only']:,} "
          f"({decomp['subtopic_only_pct']}%)")
    print(f"  Phase 3 surveys:    {len(surveys)} surveys, "
          f"{len(subset):,} questions")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
