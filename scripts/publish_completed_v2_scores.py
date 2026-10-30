#!/usr/bin/env python3
"""Export validated scalar judge outcomes; never publish raw private evidence.

Run after prepare_v2_selection_agent_scores.py for the initial execution audits.
No generation, execution, inference, or GitHub mutation is performed here.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/data'
SNAPSHOT = '2026-10-30'
RECOVERY = 'codex-qwen38-27b-q4-t1-v2-selection-recovery-20261029'
CATEGORIES = {'No Error': 'correct_v', 'Minor Error': 'minor',
              'Major Error': 'major', 'VisFail': 'vis_fail', 'Crash': 'crash'}


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def judge_summary(directory, score_path, selected_uids):
    score = load(score_path)
    assert score['status'] == 'validated' and score['trials'] == 3
    checkpoint_path = directory / 'checkpoint.json'
    assert sha(checkpoint_path) == score['checkpoint_sha256']
    checkpoint = load(checkpoint_path)
    records = list(checkpoint['records'].values())
    assert len(records) == 72 and {r['uid'] for r in records} == selected_uids
    outcomes, counts = {}, Counter()
    for record in records:
        trials = sorted(record['trials'], key=lambda t: t['trial'])
        assert [t['trial'] for t in trials] == [1, 2, 3]
        for trial in trials:
            assert trial['errors'] in CATEGORIES
            assert not trial.get('tool_calls_observed', False)
            if trial.get('llm_called'):
                assert trial['codex_exit_code'] == 0
        outcomes[record['uid']] = [t['errors'] for t in trials]
        counts.update(outcomes[record['uid']])
    assert dict(counts) == score['judge_counts'] and sum(counts.values()) == 216
    for category, metric in CATEGORIES.items():
        assert abs(score['metrics'][metric] - 100 * counts[category] / 216) < 1e-10
    provenance_path = directory / 'provenance.json'
    provenance = load(provenance_path)
    judge = provenance['judge']
    assert judge['model_requested'] == 'gpt-6-astra'
    assert judge['reasoning_effort_requested'] == 'medium'
    assert provenance['codex']['cli_version'] == 'codex-cli 0.153.4'
    if 'adapter_provenance_sha256' in score:
        assert sha(provenance_path) == score['adapter_provenance_sha256']
        assert sha(directory / 'input_provenance.json') == score['input_provenance_sha256']
    summary = dict(status='validated', coverage_workflows=72, trials_per_workflow=3,
        valid_outcomes=216, full_72_metrics_available=True, counts=dict(counts),
        model_requested='gpt-6-astra', reasoning_effort='medium',
        codex_cli_version='0.153.4', python_version='3.10.12', ijson_version='3.5.1',
        immutable_backend_snapshot_available=False, desktop_app_version_current=None,
        checkpoint_sha256=sha(checkpoint_path), scores_sha256=sha(score_path),
        adapter_provenance_sha256=sha(provenance_path),
        input_sha256=provenance['source_snapshot_sha256'],
        completed_utc=checkpoint['updated_utc'],
        aggregation='Counts / (72 workflows × 3 trials); no majority vote.',
        protocol='Original rubric, image order and Crash/VisFail semantics; Codex provider adapter, not upstream Anthropic transport.',
        human_expert_review_included=False)
    return score, outcomes, summary


def attach(audit, score, outcomes, judge):
    for metric in ['processing_no_error', 'visualization_no_error', 'vi_score']:
        assert abs(audit['metrics'][metric] - score['metrics'][metric]) < 1e-10
    audit['metrics'].update({k: score['metrics'][k] for k in CATEGORIES.values()})
    audit['snapshot'] = SNAPSHOT
    audit['result_status'] = 'execution and 216 visualization judge outcomes validated'
    audit['judge'] = judge
    audit['limitations'] = [s for s in audit['limitations'] if not s.startswith('Missing judge metrics')]
    audit['limitations'].append('Automated GPT-6 judging is not human expert validation; same-model bias is possible for GPT-6 generation.')
    for record in audit['records']:
        record['judge_outcomes'] = outcomes[record['uid']]


def export(artifacts):
    manifest_path = DATA / 'lite72-v2-candidate.json'
    selection_hash = sha(manifest_path)
    manifest = load(manifest_path)
    tasks = {r['uid']: r for r in manifest['tasks']}
    assert len(tasks) == 72
    selected_uids = set(tasks)
    runs = artifacts / '.astrovis-data/runs'
    leaderboard = load(DATA / 'leaderboard.json')
    audits = {}
    runtime_hashes = {
        'adapter_sha256': sha(artifacts / 'scripts/judge_qwen_first200_gpt6.py'),
        'prompt_csv_sha256': sha(artifacts / '.astrovis-data/upstream' / manifest['upstream_revision'] / 'vis_evaluation/viseval_prompts.csv'),
        'cli_launcher_sha256': '61b0194f3bb6534439c8d26a3ed57d0805f84b884588b761795323eeb92fcf70',
        'cli_native_sha256': '56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da',
    }
    for model in ['gpt6', 'claude-k3']:
        filename = model + '-v2-selection-audit.json'
        audit = load(DATA / filename)
        directory = runs / 'v2-selection-judges-gpt6-medium-20261027' / model
        score, outcomes, judge = judge_summary(directory, directory / 'scores.json', selected_uids)
        judge.update(runtime_hashes)
        assert audit['selection_sha256'] == score['selection_sha256'] == selection_hash
        attach(audit, score, outcomes, judge)
        audits[model + '-lite72-v2-selection'] = (filename, audit)

    run = runs / RECOVERY
    score, outcomes, judge = judge_summary(run / 'judge-gpt6-medium', run / 'scores.json', selected_uids)
    accounting_path, recovery_path = run / 'execution_accounting.json', run / 'recovery_manifest.json'
    assert sha(accounting_path) == score['execution_accounting_sha256']
    assert sha(recovery_path) == score['recovery_manifest_sha256']
    accounting, recovery = load(accounting_path), load(recovery_path)
    for key, value in runtime_hashes.items():
        assert recovery['judge'][key] == value
    judge.update(runtime_hashes)
    assert score['selection_sha256'] == recovery['selection_sha256'] == selection_hash
    assert score['missing_processing_tasks'] == [17, 52]
    assert score['supplemental_processing_task'] == 51
    rows = accounting['rows']
    assert len(rows) == 72 and {r['uid'] for r in rows} == selected_uids
    records = [dict(uid=r['uid'], index_1based=tasks[r['uid']]['index_1based'],
        selection_task_1based=next(i for i, t in enumerate(manifest['tasks'], 1) if t['uid'] == r['uid']),
        processing_success=r['processing_success'], visualization_success=r['visualization_success'],
        vi_score=r['vi'], missing_processing=r['missing_processing'],
        execution_artifact='recovery_accounted_execution') for r in rows]
    vi = [r['vi_score'] for r in records if r['processing_success'] and r['vi_score'] is not None]
    metrics = dict(workflows=72, processing_successes=sum(r['processing_success'] for r in records),
        visualization_successes=sum(r['visualization_success'] for r in records),
        processing_no_error=100 * sum(r['processing_success'] for r in records) / 72,
        visualization_no_error=100 * sum(r['visualization_success'] for r in records) / 72,
        vi_score=mean(vi), vi_eligible_workflows=len(vi))
    assert {r['selection_task_1based'] for r in records if r['missing_processing']} == {17, 52}
    template = audits['gpt6-lite72-v2-selection'][1]
    audit = dict(snapshot=SNAPSHOT, suite=template['suite'], track='coding-agent T1 — supplemental recovery',
        official_frozen_input_v2_result=False, original_capped_run_result=False,
        selection_manifest='lite72-v2-candidate.json', selection_sha256=selection_hash,
        dataset_sha256=manifest['dataset_sha256'], upstream_revision=manifest['upstream_revision'],
        model=dict(display_name='Codex + Qwen3.8-27B Q4_K_M', harness='Codex CLI',
            cli_version='0.162.1', model_requested='qwen38-27b-q4', reasoning_effort='disabled',
            hf_repository='ggml-org/Qwen3.8-27B-GGUF',
            hf_revision='0669b98607d47046c7c2b3f801011d54a08cfccf',
            weights_sha256='31629f53165ab6a7dad8c9847dcfd1fdf55829dac1e6e748f4a68581b0033d34',
            llama_cpp_build='b10679', llama_cpp_commit='50f068fff',
            transport_adapter='qwen-responses-context-compaction-v5-20261028',
            context_tokens=32768, temperature=0, seed=42),
        run=dict(id=RECOVERY, original_id=Path(recovery['parent_run']).name,
            retry_id=Path(recovery['retry_run']).name, executed_workflows=72),
        stage_limits=template['stage_limits'], tools=template['tools'], image_viewing=False,
        metrics=metrics, records=records,
        recovery=dict(original_missing_processing_tasks=[17, 51, 52],
            fresh_processing_attempts=[51, 52], successful_retry_used=51,
            missing_processing_tasks=[17, 52], missing_processing_uids=accounting['missing_processing_uids'],
            generated_code_manually_repaired=False, original_artifacts_preserved=True,
            policy=accounting['policy']),
        checksums=dict(recovery_manifest_sha256=sha(recovery_path),
            execution_accounting_sha256=sha(accounting_path),
            raw_execution_sha256=accounting['raw_execution_sha256'],
            accounted_execution_sha256=accounting['accounted_execution_sha256'],
            filled_benchmark_sha256=recovery['filled_sha256'],
            original_manifest_sha256=recovery['parent_manifest_sha256'],
            retry_manifest_sha256=recovery['retry_manifest_sha256'],
            task51_processing_sha256=recovery['task51_processing_snapshot']['sha256'],
            judge_runtime=recovery['judge']),
        aggregation='All 72 workflows retained. Missing processing 17/52 count as failures and are not VI eligible; raw blank-cell executor results remain unchanged.',
        limitations=[
            'Historical/live-service inputs, not the released frozen-input v2 suite. External-download timeouts affected execution.',
            'Supplemental recovery uses one fresh bounded attempt for processing tasks 51/52; not an original capped T1 baseline or a directly comparable ranking.',
            'Original task 52 had compaction-adapter faults; the separate retry exhausted its request cap without code. No extra attempts are hidden.',
            'Raw prompts, evidence and notebooks remain local; public hashes do not claim raw artifact availability.'])
    attach(audit, score, outcomes, judge)
    audits['codex-qwen38-lite72-v2-selection-recovery'] = ('codex-qwen38-v2-selection-recovery-audit.json', audit)
    new_id = 'codex-qwen38-lite72-v2-selection-recovery'
    if not any(r['id'] == new_id for r in leaderboard['rows']):
        leaderboard['rows'].append(dict(id=new_id, label='Codex + Qwen3.8\n27B Q4_K_M\n(lite-72 v2 selection)\nhistorical · recovery',
            table_label='Codex + Qwen3.8-27B Q4_K_M (historical v2 selection, recovery)',
            suite='lite-72 v2 task selection · historical inputs · T1 recovery', source='independent-local',
            original_capped_run_result=False))
    for row in leaderboard['rows']:
        if row['id'] not in audits:
            continue
        filename, audit = audits[row['id']]
        write(DATA / filename, audit)
        row.update({key: audit['metrics'][key] for key in leaderboard['metrics']})
        row.update(audit='data/' + filename, judge_status='validated', workflows=72,
                   judge_outcomes=216, official_frozen_input_v2_result=False)
    leaderboard['sources']['independent-local-codex-qwen-v2-recovery'] = 'data/' + audits[new_id][0]
    leaderboard['snapshot'] = SNAPSHOT
    leaderboard['notes'] = [n for n in leaderboard['notes'] if not n.startswith('2026-10-27:')]
    note = '2026-10-30: All three historical-v2-selection agent rows have 216 validated judge outcomes. Codex + Qwen is a separately labelled recovery track: task 51 retry used, missing processing 17/52 counted as failures. Not frozen-input v2 or a common controlled ranking.'
    if note not in leaderboard['notes']:
        leaderboard['notes'].insert(0, note)
    write(DATA / 'leaderboard.json', leaderboard)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-root', required=True, type=Path)
    export(parser.parse_args().artifacts_root.resolve())
