"""Export small audited evidence files for the draft Pages content; no network calls."""
from pathlib import Path
import csv
import hashlib
import io
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/lite72-candidate-v1'
OUT = ROOT / 'docs/data'
RUN = ROOT / '.astrovis-data/runs/qwen38-original-20260916'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    scores = json.loads((SOURCE/'qwen_scores.json').read_text())
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    assert scores['selection_sha256'] == sha(SOURCE/'manifest.json')
    assert len(manifest['tasks']) == len({t['uid'] for t in manifest['tasks']}) == 72
    model = json.loads((RUN/'manifest.json').read_text())
    assert model['dataset_sha256'] == manifest['dataset_sha256']
    assert model['model_lock']['selector'] == 'Q4_K_M'
    provenances = [json.loads(p.read_text()) for p in sorted(
        (RUN/'full-judge-gpt6-astra-medium-20260919').glob('batch_*/provenance.json'))]
    assert len(provenances) == len(scores['judge_sources']) == 10
    assert all(p['judge']['model_requested'] == 'gpt-6-astra' and
               p['judge']['reasoning_effort_requested'] == 'medium' and
               p['judge']['trials_requested'] == 3 for p in provenances)
    page = (ROOT/'docs/index.md').read_text()
    for scope in ('full', 'lite'):
        entry = scores[scope]
        for key in ('processing_no_error', 'visualization_no_error', 'correct_v', 'vis_fail'):
            assert f"{entry[key]:.2f}%" in page, (scope, key)
        assert f"{entry['vi_score']:.3f}" in page
    assert scores['full']['n'] == 432 and scores['lite']['n'] == 72
    OUT.mkdir(parents=True, exist_ok=True)
    # The selection manifest contains UIDs and classification metadata, not task prompts.
    write('lite72-candidate-v1.json', manifest)
    csv_text = (SOURCE/'selected_tasks.csv').read_text()
    assert len(list(csv.DictReader(io.StringIO(csv_text)))) == 72
    (OUT/'lite72-qwen-tasks.csv').write_text(csv_text)
    write('qwen38-audit.json', {
        'content_snapshot': '2026-09-30',
        'model': {'display_name': 'Qwen3.8-27B Q4_K_M',
                  'repository': model['model_lock']['repo'],
                  'weight_revision': model['model_lock']['revision'],
                  'quantization': 'Q4_K_M'},
        'upstream_revision': model['upstream_revision'],
        'dataset_sha256': manifest['dataset_sha256'],
        'judge': {'model_requested': 'gpt-6-astra', 'reasoning_effort_requested': 'medium',
                  'trials': 3, 'backend_snapshot': 'not established by these provenance files',
                  'cli_versions': sorted({p['codex']['cli_version'] for p in provenances}),
                  'desktop_version_supplied_by_user': '26.908.70816'},
        'aggregation': scores['judge_aggregation'],
        'full': scores['full'], 'lite_candidate': scores['lite'],
        'by_provisional_notebook_family': scores['by_domain'],
        'execution_sha256': scores['execution_sha256'],
        'selection_sha256': scores['selection_sha256'],
        'judge_checkpoint_checksums': [
            {'batch': Path(s['path']).parent.name, 'sha256': s['sha256']}
            for s in scores['judge_sources']],
        'limitations': manifest['limitations'],
        'raw_artifacts': 'Retained locally; no public raw-artifact archive linked in this draft.',
    })
    print('Prepared three public data files; verified task counts, provenance, and displayed score values.')


if __name__ == '__main__':
    main()
