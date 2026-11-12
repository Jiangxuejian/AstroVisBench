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
    elif row['id'] == 'gpt6-lite72-v2-selection':
        name = 'GPT-6 Astra medium\n+ Codex'
    elif row['id'] == 'codex-qwen38-lite72-v2-selection-recovery':
        name = 'Codex + Qwen3.8\n27B Q4_K_M'
    return name + ('\n(lite-bench)' if 'v2-selection' in row['id'] else '')


def main():
    payload = json.loads(DATA.read_text())
    rows = ordered_rows(payload['rows'])
    assert rows == payload['rows'], 'Run scripts/order_leaderboard.py first'
    # Figure-only exclusion: retain the original no-tool Qwen audit/table row.
    rows = [row for row in rows if row['id'] != 'qwen38-27b-q4-k-m']
    chart = [metric for metric in payload['chart_metrics'] if metric != 'vi_score']
    assert 'vi_score' in payload['chart_metrics'], 'VIscore must be included in the figure'
    y = np.arange(len(rows), dtype=float)
    height = 0.21
    colors = ['#89a8ee', '#91dce9', '#8fe7a5']
    names = ['Processing No Error %', 'Visualization No Error %', 'CorrectV %']
    fig, (ax, vi_ax) = plt.subplots(
        1, 2, sharey=True, figsize=(12.8, 17.5), dpi=180,
        gridspec_kw={'width_ratios': [4.5, 1.5], 'wspace': 0.32})
    fig.patch.set_facecolor('white')
    for panel in (ax, vi_ax):
        panel.set_facecolor('white')
        for index in range(len(rows)):
            if index % 2 == 0:
                panel.axhspan(index - 0.47, index + 0.47, color='#f6f8fb', zorder=0)
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
                    va='center', ha='left', fontsize=18,
                    fontweight='bold' if correct else 'normal',
                    color='#237445' if correct else '#596273', zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels([row_label(row) for row in rows], fontsize=19, linespacing=1.2)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xlim(0, 90)
    ax.set_xticks(np.arange(0, 91, 10))
    ax.set_xlabel('Percent (%)', fontsize=21, labelpad=12)
    # VIscore is a conditional data-product agreement score, not a percentage.
    # Keep its original scale and share model positions, never the percent axis.
    vi_values = [np.nan if row.get('vi_score') is None else row['vi_score'] for row in rows]
    vi_bars = vi_ax.barh(y, vi_values, height=0.4, color='#c7b1ec',
                         edgecolor='none', zorder=3)
    for bar, row in zip(vi_bars, rows):
        if row['source'] == 'independent-local':
            bar.set_hatch('//')
            bar.set_edgecolor('#80669f')
            bar.set_linewidth(0.45)
        value = row.get('vi_score')
        vi_ax.text(value + 0.035 if value is not None else 0.035, bar.get_y() + bar.get_height()/2,
                   f'{value:.3f}' if value is not None else 'n/a',
                   ha='left', va='center', fontsize=18, fontweight='bold', color='#65468c')
    vi_ax.set_title('VIscore ↑', fontsize=22, color='#65468c', pad=14)
    vi_ax.set_xlim(0, 1)
    vi_ax.set_xticks([0, 0.5, 1], labels=['0', '0.5', '1'])
    vi_ax.set_xlabel('Score (0–1)', fontsize=21, labelpad=12)
    vi_ax.tick_params(axis='y', left=False, labelleft=False)
    vi_ax.tick_params(axis='x', length=0, pad=6, labelsize=18, colors='#596273')
    for panel in (ax, vi_ax):
        panel.grid(axis='x', color='#d9dde5', linewidth=0.7, zorder=1)
        panel.set_axisbelow(True)
        panel.spines[['top', 'right', 'left']].set_visible(False)
        panel.spines['bottom'].set_color('#cbd1da')
    ax.tick_params(axis='y', length=0, pad=12, colors='#3d4858')
    ax.tick_params(axis='x', length=0, pad=6, labelsize=18, colors='#596273')
    fig.suptitle('AstroVisBench Leaderboard', fontsize=32, fontweight='bold', y=0.98)
    fig.text(0.5, 0.945, 'Sorted by CorrectV ↓ · lite-bench = selected 144 tasks from the full 864 tasks',
             ha='center', fontsize=18, color='#596273')
    fig.text(0.5, 0.92, 'github.com/Jiangxuejian/AstroVisBench',
             ha='center', fontsize=17, color='#596273',
             url='https://github.com/Jiangxuejian/AstroVisBench')
    fig.legend(*ax.get_legend_handles_labels(), loc='upper center',
               bbox_to_anchor=(0.5, 0.9), ncol=3, frameon=False,
               fontsize=16, handlelength=1.4, columnspacing=1.0)
    fig.subplots_adjust(left=0.31, right=0.94, bottom=0.06, top=0.845)
    # Center the complete plot, including model labels and numeric annotations,
    # not just the bar axes (which would clip long model names on the left).
    fig.canvas.draw()
    bounds = [panel.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
              for panel in (ax, vi_ax)]
    shift = 0.5 - (min(b.x0 for b in bounds) + max(b.x1 for b in bounds)) / 2
    for panel in (ax, vi_ax):
        position = panel.get_position()
        panel.set_position([position.x0 + shift, position.y0, position.width, position.height])
    fig.canvas.draw()
    centered = [panel.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
                for panel in (ax, vi_ax)]
    left, right = min(b.x0 for b in centered), max(b.x1 for b in centered)
    assert abs((left + right) / 2 - 0.5) < 0.001, 'Plot is not centered'
    assert left >= 0 and right <= 1, 'Plot labels would be clipped'
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
