#!/usr/bin/env python3
"""Validate and bundle a Lite-72 v2-selection run for maintainer-side judging.

No inference, benchmark execution, unpickling, image rendering or code repair.
Raw files are archived byte-for-byte; archives contain an explicit allowlist.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / 'docs/data/lite72-v2-candidate.json'
SELECTION_SHA = 'a9ed93a935b2e984e546fdebbcfef7b0f14879e3b93064db6985e34ef4541f3b'
DATASET_SHA = 'c48528947378e138c8c1df26531f1fd37e96a9226a52659ea838cc543a8e22e2'
UPSTREAM = '707657f8fac4df50a6cf6c2c4671bf6a0258a201'
EXECUTOR_SHA = '2965b529fe74db1a4de9ea49955b324e91e80abbf5eb13c19ac59722fc2e2d89'
REQUIRED = ['run_manifest.json', 'selected_benchmark.json', 'generated_benchmark.json',
            'executed_benchmark.json', 'stage_ledger.json', 'requirements.freeze.txt',
            'execution.log', 'RUN_NOTES.md']
OPTIONAL = ['generation_events.jsonl', 'generation_adapter.py', 'execution_launcher.py']
T1_LIMITS = dict(model_requests_per_stage=20, total_output_tokens_per_stage=32768,
    per_response_output_tokens=8192, candidate_checks_per_stage=3,
    candidate_timeout_seconds=600, stage_wall_seconds=2400)
T1_TOOLS = ['list_inputs', 'read_text', 'write_candidate', 'run_candidate', 'submit']
CONTEXT = ['setup_query', 'setup_gt_code', 'processing_query', 'processing_gt_code',
           'visualization_query', 'visualization_gt_code', 'processing_underspecifications',
           'visualization_underspecifications']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def load(path):
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)


def iter_records(path, chunk_size=8 * 1024 * 1024):
    """Stream a JSON array one record at a time; tolerate upstream NaN values.

    Python's decoder accepts upstream NaN/Infinity without changing the source
    bytes. Only scalar metadata is exported below, using strict JSON output.
    """
    decoder = json.JSONDecoder()
    with path.open(encoding='utf-8') as handle:
        buffer, pos, eof = '', 0, False

        def refill():
            nonlocal buffer, pos, eof
            part = handle.read(chunk_size)
            buffer, pos, eof = buffer[pos:] + part, 0, not part

        def space():
            nonlocal pos
            while True:
                while pos < len(buffer) and buffer[pos].isspace():
                    pos += 1
                if pos < len(buffer) or eof:
                    return
                refill()

        space()
        require(pos < len(buffer) and buffer[pos] == '[', 'Execution JSON must be an array')
        pos += 1
        first = True
        while True:
            space()
            require(pos < len(buffer), 'Truncated execution JSON')
            if buffer[pos] == ']':
                require(first, 'Trailing comma in execution JSON')
                pos += 1
                break
            while True:
                try:
                    record, end = decoder.raw_decode(buffer, pos)
                    break
                except json.JSONDecodeError:
                    require(not eof, 'Malformed/truncated execution JSON')
                    refill()
            require(isinstance(record, dict), 'Every execution record must be an object')
            pos = end
            yield record
            space()
            require(pos < len(buffer), 'Truncated execution JSON')
            if buffer[pos] == ']':
                pos += 1
                break
            require(buffer[pos] == ',', 'Missing execution JSON separator')
            pos += 1
            first = False
        space()
        require(pos == len(buffer) and eof, 'Trailing content after execution JSON')


def by_uid(records, expected, label):
    require(isinstance(records, list), f'{label} must be an array')
    require(all(isinstance(row, dict) and isinstance(row.get('uid'), str) for row in records),
            f'{label}: UID missing')
    result = {row['uid']: row for row in records}
    require(len(result) == len(records) == 72 and set(result) == expected,
            f'{label}: require all 72 unique selected UIDs, with no extras')
    return result


def png(uri, label):
    require(isinstance(uri, str) and uri.startswith('data:image/png;base64,'),
            f'{label}: judge requires an embedded PNG, not a local image path')
    try:
        raw = base64.b64decode(''.join(uri.split(',', 1)[1].split()), validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError(f'{label}: invalid base64') from error
    require(raw.startswith(b'\x89PNG\r\n\x1a\n'), f'{label}: invalid PNG signature')


def validate(run, benchmark):
    require(sha(SELECTION) == SELECTION_SHA, 'Pinned selection manifest changed')
    suite = load(SELECTION)
    expected = {task['uid'] for task in suite['tasks']}
    manifest = load(run / 'run_manifest.json')
    require(isinstance(manifest, dict), 'Run manifest must be an object')
    require('REPLACE' not in json.dumps(manifest), 'Fill all REPLACE placeholders in run_manifest.json')
    require(manifest.get('schema_version') == 1, 'Manifest schema_version must be 1')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', manifest.get('run_id', '')),
            'Use a short, safe run_id without paths or spaces')
    require(manifest.get('suite') == 'lite72-v2-selection-historical-inputs', 'Wrong suite/data track')
    require(manifest.get('selection_sha256') == SELECTION_SHA, 'Wrong selection checksum')
    require(manifest.get('dataset_sha256') == DATASET_SHA, 'Wrong dataset checksum')
    require(manifest.get('upstream_revision') == UPSTREAM, 'Wrong upstream revision')
    require(manifest.get('track') in ['T0', 'T1', 'agent-pilot'], 'Declare T0, T1 or agent-pilot')
    for key in ['model', 'harness', 'generation', 'execution', 'environment']:
        require(isinstance(manifest.get(key), dict) and manifest[key], f'Missing {key} provenance')
    for section, field in [('model', 'requested_id'), ('harness', 'name'), ('harness', 'version')]:
        require(isinstance(manifest[section].get(field), str) and manifest[section][field].strip(),
                f'Missing {section}.{field}')
    require(isinstance(manifest.get('deviations'), list), 'Declare deviations, even if empty')
    require(manifest.get('judge', {}).get('run_by_contributor') is False,
            'Declare this execution submission unjudged; contributor judge runs require separate review')
    require(manifest['execution'].get('executor_sha256') == EXECUTOR_SHA, 'Use the unchanged pinned executor')
    require(type(manifest['execution'].get('exit_code')) is int and manifest['execution']['exit_code'] == 0,
            'Executor did not finish normally; preserve partial files and report the blocker')
    selected = by_uid(load(run / 'selected_benchmark.json'), expected, 'Selected input')
    generated = by_uid(load(run / 'generated_benchmark.json'), expected, 'Generated input')
    require(sha(benchmark) == DATASET_SHA, 'Full source dataset checksum does not match the pinned benchmark')
    source_uids, reference = set(), {}
    for record in iter_records(benchmark):
        uid = record.get('uid')
        require(isinstance(uid, str) and uid not in source_uids, 'Source dataset has invalid/duplicate UID')
        source_uids.add(uid)
        if uid in expected:
            reference[uid] = record
    require(len(source_uids) == 432 and set(reference) == expected, 'Full source dataset coverage differs')
    require(selected == reference, 'Selected records differ from the pinned source dataset')
    missing = []
    for uid, record in generated.items():
        for field, value in reference[uid].items():
            if field not in ['processing_gen_code', 'visualization_gen_code']:
                require(record.get(field) == value, f'{uid}: changed original source field {field}')
        for stage in ['processing', 'visualization']:
            code = record.get(stage + '_gen_code')
            require(isinstance(code, str), f'{uid}: {stage} code must be a string')
            if not code.strip():
                missing.append(dict(uid=uid, stage=stage))
    ledger = load(run / 'stage_ledger.json')
    require(isinstance(ledger, list) and len(ledger) == 144, 'Stage ledger must contain 144 terminal entries')
    seen_stages = set()
    for entry in ledger:
        require(isinstance(entry, dict), 'Every stage ledger entry must be an object')
        key = (entry.get('uid'), entry.get('stage'))
        require(key[0] in expected and key[1] in ['processing', 'visualization'] and key not in seen_stages,
                'Stage ledger has duplicate, unknown or missing stage identities')
        seen_stages.add(key)
        code = generated[key[0]][key[1] + '_gen_code']
        require(entry.get('status') == ('submitted' if code.strip() else 'missing'), 'Stage status/code mismatch')
        require(entry.get('code_sha256') == (hashlib.sha256(code.encode()).hexdigest() if code.strip() else None),
                'Stage ledger must hash exact final normalized submitted code')
        if manifest['track'] == 'T1':
            for field, cap in [('model_requests', 20), ('output_tokens', 32768), ('candidate_checks', 3)]:
                value = entry.get(field)
                require(type(value) is int and 0 <= value <= cap, f'T1 {field} must be known and within {cap}')
            require(isinstance(entry.get('elapsed_seconds'), (int, float))
                    and not isinstance(entry['elapsed_seconds'], bool)
                    and 0 <= entry['elapsed_seconds'] <= 2400, 'T1 elapsed_seconds exceeds limit or is unknown')
    if manifest['track'] == 'T1':
        require(manifest['generation'].get('limits') == T1_LIMITS, 'T1 manifest must declare the frozen limits')
        require(sorted(manifest['generation'].get('tools', [])) == sorted(T1_TOOLS),
                'T1 must declare exactly the five approved tools')
        require(manifest['generation'].get('limits_enforcement') == 'external',
                'Prompt-only limits are agent-pilot, not T1')
        require((run / 'generation_events.jsonl').is_file(), 'T1 requires reviewed generation event evidence')
    executed_uids = set()
    crash, single, multi = 0, 0, 0
    for record in iter_records(run / 'executed_benchmark.json'):
        uid = record.get('uid')
        require(uid in expected and uid not in executed_uids, 'Execution has duplicate or unknown UID')
        executed_uids.add(uid)
        for field in CONTEXT + ['processing_gen_code', 'visualization_gen_code', 'gt_visualization']:
            require(record.get(field) == generated[uid].get(field), f'{uid}: execution changed {field}')
        processing, visualization = record.get('processing_test'), record.get('visualization_test')
        require(isinstance(processing, dict) and type(processing.get('pro_success')) is bool,
                f'{uid}: processing execution result missing')
        require('inspection_results' in processing, f'{uid}: inspection tests missing; do not use --skip-test')
        require(isinstance(visualization, dict) and type(visualization.get('vis_success')) is bool,
                f'{uid}: visualization execution result missing')
        images = visualization.get('gen_vis_list')
        require(isinstance(images, list), f'{uid}: generated image list missing')
        if not visualization['vis_success']:
            crash += 1
        elif len(images) != 1:
            multi += 1
        else:
            png(record.get('gt_visualization'), f'{uid} reference')
            png(images[0], f'{uid} generated')
            single += 1
    require(executed_uids == expected, 'Execution must contain all 72 unique selected UIDs')
    return dict(run_id=manifest['run_id'], track=manifest['track'], workflows=72,
        stage_terminals=144, missing_stages=missing,
        status='needs_missing_submission_accounting' if missing else 'structurally_complete_unjudged',
        visualization_records=dict(crash=crash, plot_count_failure=multi, single_png=single),
        judge_run=False, official_frozen_input_v2_result=False,
        note='Structural validation is not proof of isolation, scientific correctness, privacy or leaderboard eligibility. Missing stages require maintainer accounting; raw blank-cell success flags are not corrected here.')


def package(run, output, reviewed, benchmark):
    require(reviewed, 'Review all included files for secrets/private material, then pass --reviewed')
    run, output = run.resolve(), output.absolute()
    require(not output.exists(), 'Archive already exists; never overwrite a submission')
    for name in REQUIRED + OPTIONAL:
        path = run / name
        require(not path.is_symlink(), f'Refusing symlink: {name}')
        if name in REQUIRED:
            require(path.is_file(), f'Missing required submission file: {name}')
    require(not output.with_name(output.name + '.sha256').exists(), 'Checksum sidecar already exists')
    summary = validate(run, benchmark.resolve())
    files = {name: run / name for name in REQUIRED + OPTIONAL if (run / name).is_file()}
    files['suite_manifest.json'] = SELECTION
    checksums = {name: sha(path) for name, path in files.items()}
    metadata = dict(schema_version=1, created_utc=datetime.now(timezone.utc).isoformat(),
        packager_sha256=sha(Path(__file__)),
        validation=summary, files_sha256=checksums,
        privacy_note='Contributor review acknowledged; this tool is not a secret scanner. Raw execution/code are untrusted evidence, not executable installation instructions.')
    payload = (json.dumps(metadata, indent=2, allow_nan=False) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents overwriting another run. On failure retain
    # the partial archive as evidence; never advertise it as a valid submission.
    with output.open('xb') as destination, tarfile.open(fileobj=destination, mode='w:gz', compresslevel=6) as archive:
        for name, path in files.items():
            info = archive.gettarinfo(str(path), arcname='submission/' + name)
            require(info.isfile(), f'{name} is no longer a regular file')
            info.uid, info.gid, info.uname, info.gname, info.mode = 0, 0, '', '', 0o644
            with path.open('rb') as source:
                archive.addfile(info, source)
            require(sha(path) == checksums[name], f'{name} changed during packaging; archive is incomplete')
        entry = tarfile.TarInfo('submission/submission_manifest.json')
        entry.size, entry.mode = len(payload), 0o644
        archive.addfile(entry, io.BytesIO(payload))
    digest = sha(output)
    sidecar = output.with_name(output.name + '.sha256')
    require(not sidecar.exists(), 'Checksum sidecar already exists')
    with sidecar.open('x') as handle:
        handle.write(f'{digest}  {output.name}\n')
    print(json.dumps(dict(archive=str(output), sha256=digest, **summary), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--benchmark', type=Path, required=True, help='Original full 432-record source JSON; verified but not archived')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reviewed', action='store_true', help='Acknowledge review of all included evidence for credentials/private material')
    args = parser.parse_args()
    try:
        package(args.run_dir, args.output, args.reviewed, args.benchmark)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(2, f'Submission not packaged: {error}\n')
