#!/usr/bin/env python3
"""
Generate visualizations for Report 03: Harmonization Constraints.

Produces exec-friendly charts from Stage 4/5 outputs.

Outputs (in output/visuals/):
  consolidation_rates.png  - Stacked bar by survey
  expert_review_load.png   - Donut: auto-process vs expert review
  barrier_distribution.png - Horizontal bar of F3 barrier categories
  triage_quadrant.png      - 2-axis scatter (Borda × Entropy)
  process_flow.png         - Pipeline overview (via mmdc if available)

Usage:
    python scripts/generate_visuals.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

BASE = Path(__file__).parent.parent
ANALYSIS = BASE / "output" / "analysis"
VISUALS = BASE / "output" / "visuals"

# Palette
GREEN = "#4CAF50"
ORANGE = "#FF9800"
RED = "#F44336"
GRAY = "#9E9E9E"
BLUE = "#2196F3"
QUAD_COLORS = {"Q1": GREEN, "Q2": GRAY, "Q3": ORANGE, "Q4": RED}
QUAD_LABELS = {
    "Q1": "Q1 — Auto-accept",
    "Q2": "Q2 — Auto-reject",
    "Q3": "Q3 — Edge case",
    "Q4": "Q4 — Ambiguous",
}
SURVEY_LABELS = {"CPS": "CPS", "FOODAPS": "FoodAPS"}

DPI = 150


def load_data():
    df = pd.read_csv(ANALYSIS / "expert_review_combined.csv")
    print(f"Loaded {len(df)} questions from expert_review_combined.csv")
    return df


def fig_consolidation_rates(df):
    """Stacked horizontal bar chart: consolidable vs not, by survey."""
    fig, ax = plt.subplots(figsize=(10, 3.5))

    surveys = (
        df.groupby("survey")
        .agg(
            total=("source_q_id", "count"),
            consolidable=(
                "best_feasibility",
                lambda x: x.isin(["F1", "F2"]).sum(),
            ),
        )
        .sort_index()
    )
    surveys["not_consolidable"] = surveys["total"] - surveys["consolidable"]
    surveys["rate"] = surveys["consolidable"] / surveys["total"] * 100

    y_labels = [SURVEY_LABELS.get(s, s) for s in surveys.index]
    y_pos = range(len(surveys))

    ax.barh(y_pos, surveys["consolidable"], color=GREEN, label="Consolidable (F1/F2)")
    ax.barh(
        y_pos,
        surveys["not_consolidable"],
        left=surveys["consolidable"],
        color=GRAY,
        label="Not Consolidable (F3)",
    )

    for i, (_, row) in enumerate(surveys.iterrows()):
        ax.text(
            row["total"] + 3,
            i,
            f'{row["rate"]:.1f}%',
            va="center",
            fontweight="bold",
            fontsize=12,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=12)
    ax.set_xlabel("Number of Questions", fontsize=11)
    ax.set_title("Survey Question Consolidation Potential with ACS", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.set_xlim(0, surveys["total"].max() * 1.15)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.tight_layout()
    out = VISUALS / "consolidation_rates.png"
    plt.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out.name}")


def fig_expert_review_load(df):
    """Donut chart: auto-process vs expert review."""
    fig, ax = plt.subplots(figsize=(7, 7))

    auto = df["triage_quadrant"].isin(["Q1", "Q2"]).sum()
    review = df["triage_quadrant"].isin(["Q3", "Q4"]).sum()
    total = len(df)

    wedges, texts = ax.pie(
        [auto, review],
        colors=[GREEN, ORANGE],
        startangle=90,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
    )

    ax.text(0, 0.08, f"{total}", ha="center", va="center", fontsize=28, fontweight="bold")
    ax.text(0, -0.10, "questions", ha="center", va="center", fontsize=12, color=GRAY)

    ax.legend(
        wedges,
        [
            f"Auto-Process: {auto} ({100 * auto / total:.0f}%)",
            f"Expert Review: {review} ({100 * review / total:.0f}%)",
        ],
        loc="lower center",
        fontsize=11,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )

    ax.set_title("Classification Confidence Distribution", fontsize=13, fontweight="bold", pad=20)

    plt.tight_layout()
    out = VISUALS / "expert_review_load.png"
    plt.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out.name}")


def fig_barrier_distribution(df):
    """Horizontal bar chart of barrier categories for F3 questions."""
    fig, ax = plt.subplots(figsize=(10, 5))

    f3 = df[df["best_feasibility"] == "F3"]
    barriers = f3["barrier_category"].value_counts()

    # Full names for display
    names = {
        "CC": "Construct / Concept",
        "TC": "Temporal / Chronological",
        "RS": "Response Scale",
        "MC": "Mode / Context",
        "PC": "Population / Coverage",
        "PM": "Policy / Market",
        "NHB": "No Barrier Identified",
    }

    labels = [f"{code} — {names.get(code, code)}" for code in barriers.index]

    bars = ax.barh(range(len(barriers)), barriers.values, color=RED, alpha=0.85)
    ax.set_yticks(range(len(barriers)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Number of F3 Questions", fontsize=11)
    ax.set_title("Barriers Preventing Consolidation", fontsize=13, fontweight="bold")

    for bar, val in zip(bars, barriers.values):
        ax.text(val + 1, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=10)

    ax.set_xlim(0, barriers.max() * 1.12)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.tight_layout()
    out = VISUALS / "barrier_distribution.png"
    plt.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out.name}")


def fig_triage_quadrant(df):
    """Scatter plot: Borda (direction) × Entropy (stability), colored by quadrant."""
    fig, ax = plt.subplots(figsize=(9, 9))

    borda_med = df["score_borda"].median()
    entropy_med = df["score_entropy"].median()

    for q in ["Q2", "Q1", "Q4", "Q3"]:  # draw background first, review on top
        sub = df[df["triage_quadrant"] == q]
        ax.scatter(
            sub["score_borda"],
            sub["score_entropy"],
            c=QUAD_COLORS[q],
            label=f"{QUAD_LABELS[q]}  (n={len(sub)})",
            alpha=0.55,
            s=45,
            edgecolors="white",
            linewidth=0.3,
        )

    ax.axhline(entropy_med, color="gray", linestyle="--", alpha=0.4, linewidth=1)
    ax.axvline(borda_med, color="gray", linestyle="--", alpha=0.4, linewidth=1)

    # Quadrant labels in corners
    pad = 0.03
    ax.text(0.95, 0.95, "Q1\nConfident\nConsolidable", transform=ax.transAxes,
            ha="right", va="top", fontsize=9, color=GREEN, alpha=0.7)
    ax.text(0.05, 0.95, "Q2\nConfident\nNon-consolidable", transform=ax.transAxes,
            ha="left", va="top", fontsize=9, color=GRAY, alpha=0.7)
    ax.text(0.95, 0.05, "Q3\nEdge Case", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9, color=ORANGE, alpha=0.7)
    ax.text(0.05, 0.05, "Q4\nAmbiguous", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=9, color=RED, alpha=0.7)

    ax.set_xlabel("Borda Score (Direction → Consolidable)", fontsize=11)
    ax.set_ylabel("Entropy Score (Stability → Agreement)", fontsize=11)
    ax.set_title("Two-Axis Triage Framework", fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=10, framealpha=0.9)

    plt.tight_layout()
    out = VISUALS / "triage_quadrant.png"
    plt.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out.name}")


def fig_process_flow():
    """Pipeline overview diagram via Mermaid CLI (mmdc)."""
    mermaid_src = """\
flowchart LR
    A["1,598 Question Pairs<br/>(CPS + FoodAPS vs ACS)"] --> B["AI Classification<br/>3 Independent Models"]
    B --> C["Agreement Analysis<br/>κ = 0.845"]
    C --> D["Arbitration<br/>3 Flagship Models"]
    D --> E["Findings<br/>~44% Consolidable"]
    E --> F["Expert Review<br/>93 Edge Cases"]
    style A fill:#e1f5fe,stroke:#0277BD
    style B fill:#e8f5e9,stroke:#2E7D32
    style C fill:#e8f5e9,stroke:#2E7D32
    style D fill:#e8f5e9,stroke:#2E7D32
    style E fill:#c8e6c9,stroke:#2E7D32
    style F fill:#fff3e0,stroke:#E65100
"""
    out = VISUALS / "process_flow.png"

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(mermaid_src)
            mmd_path = f.name

        result = subprocess.run(
            ["mmdc", "-i", mmd_path, "-o", str(out), "-b", "white", "-s", "2"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"  [OK] {out.name}")
        else:
            print(f"  [WARN] mmdc failed: {result.stderr.strip()}")
            print("         Install with: npm install -g @mermaid-js/mermaid-cli")
    except FileNotFoundError:
        print("  [SKIP] mmdc not found — install with: npm install -g @mermaid-js/mermaid-cli")
    except Exception as e:
        print(f"  [WARN] process_flow.png skipped: {e}")


def main():
    plt.style.use("seaborn-v0_8-whitegrid")
    VISUALS.mkdir(parents=True, exist_ok=True)

    df = load_data()

    print("\nGenerating visualizations...")
    fig_consolidation_rates(df)
    fig_expert_review_load(df)
    fig_barrier_distribution(df)
    fig_triage_quadrant(df)
    fig_process_flow()

    print(f"\nAll visuals saved to {VISUALS}/")


if __name__ == "__main__":
    main()
