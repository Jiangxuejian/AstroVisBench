#!/usr/bin/env python3
"""Build the static leaderboard figure from docs/data/leaderboard.json."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/data/leaderboard.json"
OUT = ROOT / "docs/assets"


def main() -> None:
    payload = json.loads(DATA.read_text())
    rows = payload["rows"]
    chart = payload["chart_metrics"]
    labels = [r["label"] for r in rows]
    # Missing metrics are rendered as gaps rather than zeros.  This matters for
    # processing-only Lite runs: a zero would falsely imply an evaluated score.
    values = np.array([
        [np.nan if r.get(key) is None else r[key] for key in chart]
        for r in rows
    ], dtype=float)
    x = np.arange(len(rows))
    width = 0.24
    colors = ["#89a8ee", "#91dce9", "#8fe7a5"]
    names = ["Processing No Error %", "Visualization No Error %", "CorrectV %"]

    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(15.5, 7.8), dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for i, (metric, name, color) in enumerate(zip(chart, names, colors)):
        bars = ax.bar(x + (i - 1) * width, values[:, i], width * 0.92,
                      color=color, label=name, edgecolor="none")
        for bar, row in zip(bars, rows):
            if row["source"] == "independent-local":
                bar.set_hatch("//")
                bar.set_edgecolor("#4b5563")
                bar.set_linewidth(0.55)
            if row.get(metric) is None:
                # Keep the missing value visible in the same visual language as
                # the reference figure without inventing a numeric bar.
                ax.text(bar.get_x() + bar.get_width() / 2, 1.2, "n/a",
                        ha="center", va="bottom", fontsize=8,
                        color="#8b95a7", rotation=90)
    ax.set_title("AstroVisBench Leaderboard Snapshot", fontsize=22, fontweight="bold", pad=20)
    ax.set_ylabel("Percent (%)", fontsize=13)
    ax.set_xlabel("Models", fontsize=13, labelpad=18)
    ax.set_ylim(0, 85)
    ax.set_yticks(np.arange(0, 81, 10))
    ax.grid(axis="y", color="#d9dde5", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#cbd1da")
    ax.tick_params(axis="y", colors="#596273", labelsize=10, length=0)
    ax.tick_params(axis="x", colors="#596273", labelsize=10, length=0, pad=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=3,
              frameon=False, fontsize=11, handlelength=1.8, columnspacing=1.5)
    fig.text(0.99, 0.015,
             "Hatched bars: independent local runs; Lite labels are Lite-72.",
             ha="right", va="bottom", fontsize=9, color="#596273")
    fig.subplots_adjust(left=0.07, right=0.99, bottom=0.22, top=0.82)
    fig.savefig(OUT / "leaderboard-full.svg", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "leaderboard-full.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT / 'leaderboard-full.svg'} and {OUT / 'leaderboard-full.png'}")


if __name__ == "__main__":
    main()
