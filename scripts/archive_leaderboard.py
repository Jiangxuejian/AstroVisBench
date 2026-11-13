#!/usr/bin/env python3
"""Freeze a dated public leaderboard; never overwrite an existing snapshot."""
import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import tempfile
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def create_snapshot(root, version, recorded_on=None, view=None):
    if not re.fullmatch(r'\d{8}', version):
        raise ValueError('Version must be a YYYYMMDD identifier')
    datetime.strptime(version, '%Y%m%d')
    recorded_on = recorded_on or datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    date.fromisoformat(recorded_on)
    destination = root/'docs/leaderboards'/version
    if view is not None:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', view):
            raise ValueError('View must be a simple lowercase identifier')
        if not destination.is_dir():
            raise ValueError('A presentation view requires an existing dated snapshot')
        destination = destination/view
    if destination.exists():
        raise FileExistsError('Snapshot already exists; choose a new version')

    payload_bytes = (root/'docs/data/leaderboard.json').read_bytes()
    payload = json.loads(payload_bytes)
    files = {'leaderboard.json': payload_bytes}
    for ext in ('png', 'svg'):
        files['leaderboard.'+ext] = (root/f'docs/assets/leaderboard-portrait.{ext}').read_bytes()
    # Preserve local evidence referenced by the score rows, including archived v1.
    references = {value for value in payload.get('sources', {}).values()
                  if isinstance(value, str) and value.startswith('data/')}
    references |= {r['audit'] for r in payload['rows'] + payload.get('archived_rows', [])
                   if r.get('audit')}
    references |= {'data/lite72-v2-candidate.json', 'data/lite72-candidate-v1.json'}
    docs = (root/'docs').resolve()
    for reference in sorted(references):
        source = (docs/reference).resolve()
        if not reference.startswith('data/') or not source.is_relative_to(docs/'data'):
            raise ValueError('Evidence must be a public docs/data file')
        files[reference] = source.read_bytes()

    lines = (root/'docs/index.md').read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith('| Model | Suite'))
    end = start
    while end < len(lines) and lines[end].startswith('|'):
        end += 1
    table = '\n'.join(lines[start:end])
    docs_prefix = '../' * len(destination.relative_to(root/'docs').parts)
    sort_note = ('Sorted by **CorrectV only**, highest first; VIscore does not affect order.'
                 if payload['display_order'].get('sort_by') == 'correct_v'
                 else 'The display index is not an official benchmark metric.')
    readme = f'''# Leaderboard {version}{' — ' + view if view else ''}

Frozen version label **{version}**; assembled on **{recorded_on}** (Asia/Shanghai).
The version label is not the execution or publication date. Scores are the
existing historical results; this snapshot introduces no reference repairs or
new scientific evaluation rules. Lite rows use the **Lite-72 v2 task selection**.

![Leaderboard {version}](leaderboard.png)

[SVG](leaderboard.svg) · [Score data](leaderboard.json) ·
[Checksums and version metadata](manifest.json) · [Current results]({docs_prefix}index.md)

VIscore uses the separate **0–1 panel** and is conditional on eligible successful
processing runs. Reference coverage is incomplete; treat these historical VI
scores as provisional. {sort_note}
Different samples, tools, judges and recovery budgets are not a controlled ranking.

{table}

† Independent full-benchmark no-tool runs. § Historical Lite-72 T1 agents.
¶ Separate recovery run with extra attempts.
See [methods and limitations]({docs_prefix}lite72-v2-historical.md).

Evidence files in `data/` are frozen public audit exports, not raw submissions
or benchmark input data. Future updates must create a new version folder rather
than overwrite this one.
'''
    files['README.md'] = readme.encode()
    manifest = {
        'schema_version': 1,
        'leaderboard_version': version,
        'presentation_view': view,
        'assembled_on': recorded_on,
        'timezone': 'Asia/Shanghai',
        'version_label_is_execution_or_publication_date': False,
        'benchmark': 'Full-432 plus historical Lite-72 v2 task selection',
        'evaluation_revision': 'historical; no reference repairs applied',
        'layout': 'three percentage series plus separate VIscore 0-1 panel',
        'display_order': payload['display_order'],
        'score_data_sha256': digest(payload_bytes),
        'scores_recalculated': False,
        'files': {name: {'bytes': len(data), 'sha256': digest(data)}
                  for name, data in sorted(files.items())},
    }
    files['manifest.json'] = (json.dumps(manifest, indent=2, ensure_ascii=False)+'\n').encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.snapshot-', dir=destination.parent) as temporary:
        staging = Path(temporary)/version
        staging.mkdir()
        for name, data in files.items():
            path = staging/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        staging.rename(destination)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--recorded-on', help='Actual assembly date, YYYY-MM-DD; defaults to today in Shanghai')
    parser.add_argument('--view', help='Optional presentation revision inside an existing dated version; originals stay unchanged')
    args = parser.parse_args()
    print(create_snapshot(ROOT, args.version, args.recorded_on, args.view))
