#!/usr/bin/env python3
"""Build the portrait horizontal leaderboard and backwards-compatible assets."""
from __future__ import annotations

import json
from pathlib import Path

from leaderboard_order import ordered_rows

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.hashsalt'] = 'astrovisbench-leaderboard'
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/data/leaderboard.json'
OUT = ROOT / 'docs/assets'


def row_label(row):
    name = row.get('table_label', row['label']).split(' (', 1)[0]
    if row['id'] == 'qwen38-27b-q4-k-m':
        name = 'Qwen3.8\n27B Q4_K_M'
    elif row['id'] == 'codex-qwen38-lite72-v2-selection-recovery':
        name = 'Codex + Qwen3.8\n27B Q4_K_M'
    return name + ('\n(lite-bench)' if 'v2-selection' in row['id'] else '')


def main():
    payload = json.loads(DATA.read_text())
    rows = ordered_rows(payload['rows'])
    assert rows == payload['rows'], 'Run scripts/order_leaderboard.py first'
    # Figure-only exclusion: retain the original no-tool Qwen audit/table row.
    rows = [row for row in rows if row['id'] != 'qwen38-27b-q4-k-m']
    chart = payload['chart_metrics']
    y = np.arange(len(rows), dtype=float)
    height = 0.21
    colors = ['#89a8ee', '#91dce9', '#8fe7a5']
    names = ['Processing No Error %', 'Visualization No Error %', 'CorrectV %']
    fig, ax = plt.subplots(figsize=(10.8, 15.5), dpi=180)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    for index in range(len(rows)):
        if index % 2 == 0:
            ax.axhspan(index - 0.47, index + 0.47, color='#f6f8fb', zorder=0)
    for i, (metric, color, label) in enumerate(zip(chart, colors, names)):
        values = [np.nan if row.get(metric) is None else row[metric] for row in rows]
        bars = ax.barh(y + (i - 1) * height, values, height * 0.9,
                       color=color, edgecolor='none', label=label, zorder=3)
        for bar, row in zip(bars, rows):
            if row['source'] == 'independent-local':
                bar.set_hatch('//')
                bar.set_edgecolor('#697586')
                bar.set_linewidth(0.45)
            value = row.get(metric)
            correct = metric == 'correct_v'
            ax.text((value + 0.8) if value is not None else 0.8,
                    bar.get_y() + bar.get_height() / 2,
                    f'{value:.2f}' if value is not None else 'n/a',
                    va='center', ha='left', fontsize=8.5,
                    fontweight='bold' if correct else 'normal',
                    color='#237445' if correct else '#596273', zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels([row_label(row) for row in rows], fontsize=9.5, linespacing=1.35)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xlim(0, 90)
    ax.set_xticks(np.arange(0, 91, 10))
    ax.set_xlabel('Percent (%)', fontsize=11, labelpad=12)
    ax.grid(axis='x', color='#d9dde5', linewidth=0.7, zorder=1)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#cbd1da')
    ax.tick_params(axis='y', length=0, pad=12, colors='#3d4858')
    ax.tick_params(axis='x', length=0, pad=6, labelsize=9, colors='#596273')
    fig.suptitle('AstroVisBench Leaderboard', fontsize=19, fontweight='bold', y=0.975)
    fig.text(0.5, 0.945, 'Sorted by CorrectV ↓ · lite-bench = Lite-72 v2 selection',
             ha='center', fontsize=11, color='#596273')
    fig.legend(*ax.get_legend_handles_labels(), loc='upper center',
               bbox_to_anchor=(0.5, 0.925), ncol=3, frameon=False,
               fontsize=9, handlelength=1.6, columnspacing=1.2)
    fig.text(0.04, 0.022,
             'Display order only: suites, tool access, judges and inputs differ.\n'
             'Lite-72 v2 selection uses historical inputs—not frozen-input v2.\n'
             'Qwen recovery includes supplemental attempts; not original capped T1.\n'
             'Hatched bars: independent runs. Lite-72 v1 and no-tool Qwen omitted.',
             ha='left', va='bottom', fontsize=9, color='#596273', linespacing=1.5)
    fig.subplots_adjust(left=0.37, right=0.95, bottom=0.13, top=0.89)
    OUT.mkdir(parents=True, exist_ok=True)
    svg, png = OUT / 'leaderboard-portrait.svg', OUT / 'leaderboard-portrait.png'
    fig.savefig(svg, facecolor='white', metadata={'Date': None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    fig.savefig(png, facecolor='white')
    plt.close(fig)
    # Preserve existing external/README URLs while serving the current design.
    (OUT / 'leaderboard-full.svg').write_bytes(svg.read_bytes())
    (OUT / 'leaderboard-full.png').write_bytes(png.read_bytes())
    print(f'Wrote portrait SVG/PNG and compatibility aliases ({len(rows)} rows).')


if __name__ == '__main__':
    main()
