#!/usr/bin/env python3
"""Reorder existing rows without altering metrics or provenance."""
import argparse
import json
from pathlib import Path

from leaderboard_order import GROUPS, group_id, ordered_rows

ROOT = Path(__file__).resolve().parents[1]


def reorder_markdown(text, old_rows, new_rows):
    """Move existing result-table lines verbatim; do not reformat scores."""
    lines = text.splitlines(keepends=True)
    # Only the comprehensive results table has Model/Suite as its first fields.
    header = next(i for i, line in enumerate(lines) if line.startswith('| Model | Suite'))
    start = header + 2
    end = start
    while end < len(lines) and lines[end].startswith('| '):
        end += 1
    lookup = {}
    for row in old_rows:
        name = row.get('table_label', row['label']).split(' (', 1)[0].replace('\n', ' ')
        matches = [line for line in lines[start:end]
                   if line.split('|')[1].strip().rstrip('†‡§¶') == name
                   and (('historical inputs' in line) == ('v2-selection' in row['id']))
                   and (('subset v1' in line) == (row['id'] == 'claude-code-k3-lite72'))]
        assert len(matches) == 1, f"Ambiguous/missing table row: {row['id']}"
        lookup[row['id']] = matches[0]
    assert len(set(lookup.values())) == end - start == len(old_rows)
    lines[start:end] = [lookup[row['id']] for row in new_rows]
    return ''.join(lines)


def main(check=False):
    path = ROOT / 'docs/data/leaderboard.json'
    payload = json.loads(path.read_text())
    before = payload['rows']
    after = ordered_rows(before)
    payload['rows'] = after
    payload['display_order'] = dict(
        groups=[dict(id=key, label=label) for key, label, _ in GROUPS
                if any(group_id(row) == key for row in after)],
        within_group='CorrectV descending; missing values last; ties by model ID',
        note='Display order only. Different suites, judges and recovery budgets do not form one comparable ranking.')
    outputs = {path: json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n'}
    markdown = ROOT / 'docs/index.md'
    outputs[markdown] = reorder_markdown(markdown.read_text(), before, after)
    if check:
        assert all(path.read_text() == content for path, content in outputs.items()), 'Run scripts/order_leaderboard.py'
    else:
        for path, content in outputs.items():
            path.write_text(content)
    for key, label, _ in GROUPS:
        print(label + ': ' + ', '.join(row['id'] for row in after if group_id(row) == key))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
