#!/usr/bin/env python3
"""Display Full-432/v2 by CorrectV; archive v1 without changing any score."""
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
    archived = {row['id']: row for row in payload.get('archived_rows', [])}
    archived.update({row['id']: row for row in before if group_id(row) == 'lite-v1-t1'})
    payload['archived_rows'] = list(archived.values())
    payload['suite'] = 'AstroVisBench Full-432 + historical Lite-72 v2-selection snapshot'
    payload['notes'] = [note for note in payload['notes']
                        if not note.startswith("The chart's (lite-72 subset) row")]
    display_note = '2026-10-30: Portrait horizontal chart, Full-432 and historical Lite-72 v2 selection only, globally sorted by CorrectV. Lite-72 v1 retained in archived_rows, not displayed. No scores changed.'
    if display_note not in payload['notes']:
        payload['notes'].insert(0, display_note)
    payload['display_order'] = dict(
        sort_by='correct_v', direction='descending',
        scope='Full-432 and Lite-72 v2 task selection; Lite-72 v1 excluded',
        groups=[dict(id=key, label=label) for key, label, _ in GROUPS
                if any(group_id(row) == key for row in after)],
        tie_break='model ID; missing metrics last',
        note='Globally sorted for display only. Different suites, judges and recovery budgets do not form one comparable ranking.')
    outputs = {path: json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n'}
    markdown = ROOT / 'docs/index.md'
    outputs[markdown] = reorder_markdown(markdown.read_text(), before, after)
    if check:
        assert all(path.read_text() == content for path, content in outputs.items()), 'Run scripts/order_leaderboard.py'
    else:
        for path, content in outputs.items():
            path.write_text(content)
    for key, label, _ in GROUPS:
        matches = [row['id'] for row in after if group_id(row) == key]
        if matches:
            print(label + ': ' + ', '.join(matches))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
