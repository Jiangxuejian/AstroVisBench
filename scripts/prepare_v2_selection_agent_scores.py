#!/usr/bin/env python3
"""Export sanitized historical v2-selection agent scores, never frozen-v2 claims.

Requires the operator's local artifact directory; publishes compact scalar
records and checksums, not raw prompts, credentials, host paths or notebooks.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/data'
MODELS = {
    'gpt6': ('codex-gpt6-astra-medium-t1-v2-selection-supplement7-20261026',
             'codex-gpt6-astra-medium-t1-lite72-20261015-v2',
             'GPT-6 Astra medium + Codex', 'gpt6-v2-selection-audit.json'),
    'claude-k3': ('claude-code-k3-t1-v2-selection-supplement7-20261026',
                  'claude-code-k3-t1-lite-20261004',
                  'Claude Code + Kimi K3', 'claude-k3-v2-selection-audit.json'),
}

def load(path):
    return json.loads(Path(path).read_text())

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(8*1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()

def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def export(artifacts):
    # This first-stage exporter must not silently erase completed judge scores.
    existing=load(OUT/'leaderboard.json')
    if any('v2-selection' in r['id'] and r.get('judge_status')=='validated'
           for r in existing['rows']):
        raise RuntimeError('Completed scores already published; use publish_completed_v2_scores.py, not the execution-only exporter.')
    selected_path=artifacts/'results/lite72-v2-candidate/manifest.json'
    selected=load(selected_path)
    selected_hash=sha(selected_path)
    tasks={r['uid']:r for r in selected['tasks']}
    assert len(tasks)==72
    # Exact original bytes keep the published manifest's checksum reproducible.
    (OUT/'lite72-v2-candidate.json').write_bytes(selected_path.read_bytes())
    leaderboard=load(OUT/'leaderboard.json')
    for model,(run_id,baseline_id,label,filename) in MODELS.items():
        run=artifacts/'.astrovis-data/runs'/run_id
        baseline=artifacts/'.astrovis-data/runs'/baseline_id
        report_path=run/'historical_v2_selection_coverage.json'
        report=load(report_path)
        assert report['selection_sha256']==selected_hash
        assert report['official_frozen_input_v2_result'] is False
        rows=report['records']
        assert len(rows)==len({r['uid'] for r in rows})==72
        assert {r['uid'] for r in rows}==set(tasks)
        vi=[r['vi_score'] for r in rows if r['processing_success'] and r['vi_score'] is not None]
        metrics=dict(workflows=72,
            processing_successes=sum(r['processing_success'] for r in rows),
            visualization_successes=sum(r['visualization_success'] for r in rows),
            processing_no_error=100*sum(r['processing_success'] for r in rows)/72,
            visualization_no_error=100*sum(r['visualization_success'] for r in rows)/72,
            vi_score=statistics.mean(vi),vi_eligible_workflows=len(vi),
            correct_v=None,vis_fail=None,minor=None,major=None)
        for key in ['processing_no_error','visualization_no_error','vi_score']:
            assert abs(metrics[key]-report[key])<1e-12
        artifacts_by_path={}
        execution_sources=[]
        for entry in report['execution_sources']:
            path=Path(entry['path'])
            assert sha(path)==entry['sha256'], 'Execution artifact changed'
            kind='baseline_execution' if baseline_id in path.parts else 'supplement_execution'
            artifacts_by_path[str(path)]=kind
            execution_sources.append(dict(id=kind,sha256=entry['sha256']))
        origins=Counter(artifacts_by_path[r['execution_source']] for r in rows)
        assert origins=={'baseline_execution':65,'supplement_execution':7}
        compact=[dict(uid=r['uid'],index_1based=tasks[r['uid']]['index_1based'],
            processing_success=r['processing_success'],visualization_success=r['visualization_success'],
            vi_score=r['vi_score'],execution_artifact=artifacts_by_path[r['execution_source']])
            for r in sorted(rows,key=lambda r:tasks[r['uid']]['index_1based'])]
        model_meta=dict(display_name=label,tool_profile='T1',
            model_requested='gpt-6-astra' if model=='gpt6' else 'k3',
            reasoning_effort='medium' if model=='gpt6' else 'low target',
            immutable_backend_snapshot_available=False,
            harness='Codex CLI' if model=='gpt6' else 'Claude Code',
            baseline_cli_versions=['0.162.1'] if model=='gpt6' else ['2.1.285','2.1.289'],
            supplement_cli_version='0.162.1' if model=='gpt6' else '2.1.285')
        checksums=dict(coverage_report_sha256=sha(report_path),
            baseline_generation_sha256=sha(baseline/'filled_benchmark.json'),
            baseline_execution_manifest_sha256=sha(baseline/'execution_manifest_t1.json'),
            supplement_generation_sha256=sha(run/'filled_benchmark.json'),
            supplement_run_manifest_sha256=sha(run/'manifest.json'),
            supplement_execution_manifest_sha256=sha(run/'execution_manifest_t1.json'))
        recovery=None
        if model=='claude-k3':
            recovery=dict(original_outer_exit_code=-11,
                completed_records_preserved=3,missing_records_recovered=4,
                method='One unchanged upstream executor process per unfinished record.',
                native_thread_overrides_applied=False,generated_code_changed=False,
                recovered_output_sha256=load(run/'execution-recovery-20261027/status.json')['output_sha256'])
        audit=dict(snapshot='2026-10-27',suite='Lite-72 v2 task selection — historical inputs',
            result_status='generation and execution complete; visualization judging incomplete',
            official_frozen_input_v2_result=False,track='coding-agent T1',
            selection_manifest='lite72-v2-candidate.json',selection_sha256=selected_hash,
            dataset_sha256=selected['dataset_sha256'],upstream_revision=selected['upstream_revision'],
            model=model_meta,run=dict(baseline_id=baseline_id,supplement_id=run_id,
                baseline_records=65,supplement_records=7,executed_workflows=72),
            stage_limits=dict(logical_model_requests=20,total_output_tokens=32768,
                per_response_output_tokens=8192,candidate_checks=3,feedback_corrections=2,
                candidate_timeout_seconds=600,wall_clock_seconds=2400,subagents=0,human_hints=0),
            tools=['list_inputs','read_text','write_candidate','run_candidate','submit'],
            image_viewing=False,metrics=metrics,
            judge=dict(new_trials_run=0,coverage_workflows=0 if model=='gpt6' else 65,
                full_72_metrics_available=False,
                note='Original 65 overlapping judgments are retained but not extrapolated to 72.' if model=='claude-k3'
                     else 'Human review and/or automated visualization judging remains separate.'),
            execution_sources=execution_sources,checksums=checksums,recovery=recovery,
            records=compact,
            aggregation='Execution percentages use all 72 UIDs, including crashes; VIscore uses successful processing with nonempty inspections.',
            limitations=[
                'Historical inputs, not the new frozen-file/SQLite data distribution. No official frozen-input v2 score is claimed.',
                '65 immutable baseline executions plus seven supplements, never best-of outcomes. Live network availability and run dates differ.',
                'Hosted aliases cannot establish immutable model weights. Tool-enabled T1 results are not no-tool model results.',
                'Claude baseline has recorded CLI version drift (2.1.285/2.1.289); the supplement is pinned to 2.1.285.',
                'Missing judge metrics are null, not zero. Raw execution artifacts remain local; their public availability is not claimed.'])
        write(OUT/filename,audit)
        row=dict(id=model+'-lite72-v2-selection',
            label=('GPT-6 Astra medium\n+ Codex' if model=='gpt6' else 'Claude Code\n+ Kimi K3')+'\n(lite-72 v2 selection)\nhistorical · T1',
            table_label=label+' (historical v2 selection, T1)',
            suite='lite-72 v2 task selection · historical inputs · T1',
            source='independent-local',audit='data/'+filename,
            official_frozen_input_v2_result=False,workflows=72,judge_status='pending',
            **{k:metrics[k] for k in leaderboard['metrics']})
        leaderboard['rows']=[r for r in leaderboard['rows'] if r['id']!=row['id']]+[row]
        leaderboard['sources']['independent-local-'+model+'-v2-selection']='data/'+filename
    leaderboard['suite']='AstroVisBench Full-432 + Lite-72 v1 + historical v2-selection snapshot'
    leaderboard['snapshot']='2026-10-27'
    note='2026-10-27: Added GPT-6 + Codex and Claude Code + K3 T1 execution metrics for all 72 v2-selected UIDs. Historical inputs only; not frozen-input v2 results. New judge metrics pending/null; old v1 rows retained.'
    if note not in leaderboard['notes']:leaderboard['notes'].insert(0,note)
    for row in leaderboard['rows']:
        if row['id']=='claude-code-k3-lite72':row['label']='Claude Code\n+ Kimi K3\n(lite-72 subset v1)'
    write(OUT/'leaderboard.json',leaderboard)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-root',type=Path,required=True)
    export(parser.parse_args().artifacts_root.resolve())
