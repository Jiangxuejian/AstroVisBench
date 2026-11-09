#!/usr/bin/env python3
"""Audit original Lite-72 archives; package only explicitly reviewed inputs.

No extraction, scientific execution, model calls, downloads or uploads. A
historical-input bundle is NOT the unreleased offline/frozen-data benchmark.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
from urllib.parse import urlsplit

from package_lite72_submission import (
    DATASET_SHA, SELECTION, SELECTION_SHA, UPSTREAM, load, require, sha,
)


def save(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)


def safe_name(name):
    return (isinstance(name, str) and bool(name) and not name.startswith('/')
            and not any(ord(c) < 32 for c in name) and '\\' not in name
            and ':' not in name and '..' not in name.split('/'))


def member_flags(member):
    """Conservative name/type heuristics, NOT a content or licence clearance."""
    flags = []
    if not safe_name(member.name):
        flags.append('unsafe_path')
    if not (member.isfile() or member.isdir()):
        flags.append('link_or_special_file')
    path = PurePosixPath(member.name)
    lower = member.name.lower()
    if path.suffix.lower() in {'.ipynb', '.html', '.htm', '.py', '.pyc', '.sh',
                               '.pkl', '.pickle', '.joblib'}:
        flags.append('solution_or_executable_review')
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.svg', '.pdf'}:
        flags.append('possible_reference_image_review')
    if any(part.lower() in {'.env', '.ssh', '.aws', '.git', 'id_rsa', 'id_ed25519'}
           for part in path.parts) or re.search(r'credential|cookie|access.?token', lower):
        flags.append('possible_secret')
    if any(part == '__MACOSX' or part.startswith('._') for part in path.parts):
        flags.append('platform_sidecar')
    # A gzip-compressed FITS/CSV is a native scientific file, not a tar/zip
    # container. Do not suggest discarding necessary calibration inputs.
    native_compressed = any(lower.endswith(ext + compression)
        for ext in ('.fits', '.fit', '.fts', '.csv', '.tsv', '.txt', '.dat', '.vot', '.xml')
        for compression in ('.gz', '.bz2', '.xz'))
    if not native_compressed and path.suffix.lower() in {'.zip', '.gz', '.tgz', '.tar', '.bz2', '.xz', '.7z'}:
        flags.append('nested_archive_review')
    return flags


def scan_archive(path):
    before = path.stat()
    digest = sha(path)
    members, names = [], set()
    with tarfile.open(path, 'r|gz') as archive:
        for member in archive:
            flags = member_flags(member)
            normalized = str(PurePosixPath(member.name))
            if normalized in names:
                flags.append('duplicate_member')
            names.add(normalized)
            members.append(dict(name=member.name, bytes=member.size,
                kind='file' if member.isfile() else 'directory' if member.isdir() else 'special',
                flags=flags))
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ino) ==
            (after.st_size, after.st_mtime_ns, after.st_ino), 'Archive changed during audit')
    return dict(bytes=before.st_size, sha256=digest, members=members,
        flags=dict(Counter(flag for member in members for flag in member['flags'])),
        uncompressed_member_bytes=sum(m['bytes'] for m in members if m['kind'] == 'file'))


def network_signals(record):
    code = '\n'.join(record.get(k, '') for k in
                     ['setup_gt_code', 'processing_gt_code', 'visualization_gt_code'])
    hosts = sorted({urlsplit(url).hostname for url in
        re.findall(r'https?://[^\s\x27\x22<>]+', code) if urlsplit(url).hostname})
    calls = [s for s in ['qc.query', 'queryClient', 'astroquery', 'requests.',
             'urlretrieve', 'download_file', 'SparclClient', 'mastQuery'] if s in code]
    return dict(hosts=hosts, code_markers=calls,
                note='Static hints only; absence does not prove network independence.')


def audit(benchmark, bench_env, output, readiness=None):
    require(sha(SELECTION) == SELECTION_SHA, 'Selection checksum mismatch')
    require(sha(benchmark) == DATASET_SHA, 'Full source checksum mismatch')
    suite, source = load(SELECTION), load(benchmark)
    require(len(source) == len({r['uid'] for r in source}) == 432, 'Invalid full source coverage')
    by_uid = {r['uid']: r for r in source}
    tasks = suite['tasks']
    require(len(tasks) == len({t['uid'] for t in tasks}) == 72, 'Invalid selection coverage')
    output.mkdir(parents=True, exist_ok=False)
    archives, task_rows = {}, []
    for index, task in enumerate(tasks, 1):
        record = by_uid[task['uid']]
        require(record['nb_path'] == task['notebook'], 'Notebook/source identity mismatch')
        notebook = task['notebook']
        require(safe_name(notebook) and PurePosixPath(notebook).name == notebook,
                'Unsafe notebook path')
        name = Path(notebook).stem
        relative = f'{name}/{name}_comped.tar.gz'
        if relative not in archives:
            save(output / 'status.json', dict(stage='auditing', workflows_seen=index,
                 archives_scanned=len(archives), current_notebook=notebook))
            path = bench_env / relative
            require(not path.is_symlink() and not path.parent.is_symlink(), 'Symlinked archive')
            if path.is_file():
                entry = scan_archive(path)
                entry['available'] = True
            else:
                entry = dict(available=False, bytes=0, sha256=None, flags={'missing_archive':1}, members=[])
            entry.update(path=relative, notebook=notebook, license_status='UNREVIEWED')
            archives[relative] = entry
        task_rows.append(dict(uid=task['uid'], notebook=notebook, archive=relative,
                              strategy=task['data_strategy'], network_hints=network_signals(record)))
    prior = load(readiness) if readiness else {}
    result = dict(schema_version=1, suite='lite72-v2-selection-historical-inputs',
        selection_sha256=SELECTION_SHA, dataset_sha256=DATASET_SHA, upstream_revision=UPSTREAM,
        release_ready=False, offline_ready=False, workflows=72, stages=144,
        archive_bytes=sum(a['bytes'] for a in archives.values()),
        strategies=dict(Counter(t['strategy'] for t in task_rows)),
        audit_scope='Member names/types/sizes and archive hashes; no content/secret/rights clearance.',
        recorded_reference_validated_tasks=prior.get('reference_validated_tasks'),
        readiness_evidence_sha256=sha(readiness) if readiness else None,
        known_additional_assets=prior.get('verified_assets', []),
        archives=list(archives.values()), tasks=task_rows)
    # Retain evidence identity without exporting private workstation locations.
    for asset in result['known_additional_assets']:
        asset.pop('path', None)
    write_reports(result, output)
    return result


def write_reports(result, output):
    archives = {a['path']: a for a in result['archives']}
    save(output / 'inventory.json', result)
    review = dict(schema_version=1, inventory_sha256=sha(output / 'inventory.json'),
        note='Fill each licence/source/notice and reviewer; never approve an unresolved flagged archive.',
        files=[dict(path=a['path'], sha256=a['sha256'], source_url='', license='',
                    notice='', reviewed_by='', redistribution_approved=False,
                    raw_input_reviewed=False) for a in archives.values()],
        additional_asset_reviews=[dict(asset=a['asset'], sha256=a['sha256'],
            source_url='', license='', notice='', reviewed_by='', redistribution_approved=False)
            for a in result['known_additional_assets']])
    save(output / 'review.template.json', review)
    rows = ['# Lite-72 data release audit', '', '**PRIVATE CANDIDATE — NOT RELEASE READY.**', '',
        f"72 workflows; {len(archives)} original archives; {result['archive_bytes']/1024**3:.2f} GiB compressed.",
        f"Recorded offline reference validation: {result['recorded_reference_validated_tasks']}/72 (not rerun here).", '',
        'No source-file licences are cleared by this audit. Static flags require human review.',
        'A complete archive set does not include every runtime download or catalogue response.', '',
        '| Notebook | Archive MiB | Review flags |', '|---|---:|---|']
    for a in archives.values():
        flags = ', '.join(f'{k}: {v}' for k,v in sorted(a['flags'].items())) or 'No name/type flags; content review still required'
        rows.append(f"| {a['notebook']} | {a['bytes']/1024**2:.2f} | {flags} |")
    rows += ['', '## Remaining release gates', '',
        '1. Review file-level rights, attribution and raw-input content; isolate solutions/evaluation assets.',
        '2. Resolve external downloads and all catalogue contracts; freeze source rows, not reference query answers.',
        '3. Validate all 72 references offline in a clean environment; retain original tasks and evaluator.',
        '4. Build reviewed bundles, verify hashes and test fresh extraction/paths.',
        '5. Maintainer approves ScienceDB metadata, licences and publication; no upload performed.', '']
    (output / 'REPORT.md').write_text('\n'.join(rows))
    save(output / 'status.json', dict(stage='audit_complete', release_ready=False,
         archives_scanned=len(archives), workflows=72, archive_bytes=result['archive_bytes']))


def refresh_flags(audit_dir, output):
    """Reclassify recorded headers only; retain full-scan hashes as evidence."""
    result = load(audit_dir/'inventory.json')
    require(result.get('selection_sha256') == SELECTION_SHA and
            result.get('dataset_sha256') == DATASET_SHA, 'Wrong suite identity')
    require(load(audit_dir/'status.json').get('stage') == 'audit_complete', 'Incomplete audit')
    result['header_review_from_inventory_sha256'] = sha(audit_dir/'inventory.json')
    result['header_review_note'] = 'Flags recomputed from recorded names/types; source files NOT rescanned.'
    result['release_ready'] = result['offline_ready'] = False
    for entry in result['archives']:
        seen = set()
        for member in entry['members']:
            info = tarfile.TarInfo(member['name'])
            info.type = {'file':tarfile.REGTYPE, 'directory':tarfile.DIRTYPE,
                         'special':tarfile.SYMTYPE}[member['kind']]
            flags = member_flags(info)
            normalized = str(PurePosixPath(member['name']))
            if normalized in seen:
                flags.append('duplicate_member')
            seen.add(normalized)
            member['flags'] = flags
        entry['flags'] = dict(Counter(f for m in entry['members'] for f in m['flags']))
        if not entry['available']:
            entry['flags']['missing_archive'] = 1
        entry['license_status'] = 'UNREVIEWED'
    output.mkdir(parents=True, exist_ok=False)
    write_reports(result, output)
    return result


def package(audit_dir, bench_env, review_path, output):
    """Gate a historical raw-archive bundle; never silently certify frozen v2."""
    require(not output.exists() and not Path(str(output)+'.sha256').exists(), 'Output already exists')
    inventory, review = load(audit_dir/'inventory.json'), load(review_path)
    require(review.get('inventory_sha256') == sha(audit_dir/'inventory.json'), 'Review/inventory mismatch')
    require(inventory.get('selection_sha256') == SELECTION_SHA and
            inventory.get('dataset_sha256') == DATASET_SHA, 'Wrong suite identity')
    expected = {a['path']: a for a in inventory['archives']}
    require(sha(SELECTION) == SELECTION_SHA, 'Pinned selection changed')
    selected_paths = {f"{Path(t['notebook']).stem}/{Path(t['notebook']).stem}_comped.tar.gz"
                      for t in load(SELECTION)['tasks']}
    require(set(expected) == selected_paths and len(inventory['archives']) == len(expected),
            'Archive allowlist differs from the pinned selection')
    files = review.get('files', [])
    require(len(files) == len(expected) and {f['path'] for f in files} == set(expected), 'Review coverage mismatch')
    require(inventory.get('workflows') == 72 and len(expected) == 61, 'Incomplete original archive set')
    for entry in files:
        a = expected[entry['path']]
        require(a['available'] and not a['flags'], f"Unresolved archive flags: {a['path']}")
        require(entry.get('redistribution_approved') is True and entry.get('raw_input_reviewed') is True,
                f"Rights/content review incomplete: {a['path']}")
        require(all(isinstance(entry.get(k), str) and entry[k].strip() for k in
                    ['source_url', 'license', 'notice', 'reviewed_by']), 'Missing rights evidence')
        require(safe_name(a['path']) and entry.get('sha256') == a['sha256'], 'Unsafe or changed file identity')
        src = bench_env/a['path']
        require(not src.is_symlink() and not src.parent.is_symlink(), 'Symlinked source')
        require(sha(src) == a['sha256'], 'Source changed since audit')
    manifest = dict(schema_version=1, suite=inventory['suite'], offline_ready=False,
        selection_sha256=SELECTION_SHA, dataset_sha256=DATASET_SHA,
        notice='Reviewed historical archives only; external runtime data may still be required. NOT frozen-input v2.',
        inventory_sha256=sha(audit_dir/'inventory.json'), review_sha256=sha(review_path),
        files=[dict(path='bench_env/'+a['path'], bytes=a['bytes'], sha256=a['sha256'])
               for a in sorted(expected.values(), key=lambda a:a['path'])])
    # Fixed gzip/tar metadata makes repeat builds byte-identical. Inputs are
    # already gzip files, so avoid expensive, ineffective recompression.
    with output.open('xb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0, compresslevel=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w|') as archive:
            for item in manifest['files']:
                info = tarfile.TarInfo(item['path']); info.size=item['bytes']; info.mode=0o644
                with (bench_env/item['path'].removeprefix('bench_env/')).open('rb') as src:
                    digest = hashlib.sha256()
                    class CheckedReader:
                        def read(self, size):
                            block=src.read(size); digest.update(block); return block
                    archive.addfile(info, CheckedReader())
                require(digest.hexdigest() == item['sha256'], 'Source changed during packaging')
            data=(json.dumps(manifest, indent=2)+'\n').encode()
            info=tarfile.TarInfo('manifest.json'); info.size=len(data); info.mode=0o644
            archive.addfile(info, io.BytesIO(data))
    checksum=sha(output)
    with Path(str(output)+'.sha256').open('x') as sidecar:
        sidecar.write(f'{checksum}  {output.name}\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command', required=True)
    inspect=sub.add_parser('audit')
    inspect.add_argument('--benchmark', type=Path, required=True)
    inspect.add_argument('--bench-env', type=Path, required=True)
    inspect.add_argument('--output', type=Path, required=True)
    inspect.add_argument('--readiness', type=Path)
    refresh=sub.add_parser('refresh-flags', help='Reclassify a completed inventory without rereading payloads')
    refresh.add_argument('--audit-dir', type=Path, required=True)
    refresh.add_argument('--output', type=Path, required=True)
    build=sub.add_parser('package-reviewed')
    build.add_argument('--audit-dir', type=Path, required=True)
    build.add_argument('--bench-env', type=Path, required=True)
    build.add_argument('--review', type=Path, required=True)
    build.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    try:
        if args.command == 'audit':
            result=audit(args.benchmark, args.bench_env, args.output, args.readiness)
            print(f"Audited {len(result['archives'])} archives; NOT release ready. See {args.output/'REPORT.md'}")
        elif args.command == 'refresh-flags':
            refresh_flags(args.audit_dir, args.output)
            print(f'Reclassified recorded headers; no source rescan; NOT release ready. See {args.output}')
        else:
            package(args.audit_dir, args.bench_env, args.review, args.output)
            print(f'Wrote {args.output} and checksum; historical inputs, not offline v2.')
    except (ValueError, OSError, tarfile.TarError) as error:
        parser.exit(1, f'STOP: {error}\n')


if __name__ == '__main__':
    main()
