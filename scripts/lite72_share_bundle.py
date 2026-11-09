#!/usr/bin/env python3
"""Private, deduplicated Lite-72 transport: build, verify, restore. Python 3.10+.

Restores upstream-compatible archives, not a solver sandbox. Never executes
supplied code, extracts original paths/links, installs packages or uploads.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile

SELECTION_SHA = 'a9ed93a935b2e984e546fdebbcfef7b0f14879e3b93064db6985e34ef4541f3b'
DATASET_SHA = 'c48528947378e138c8c1df26531f1fd37e96a9226a52659ea838cc543a8e22e2'
MAX_BYTES = 10_000_000_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, indent=2)+'\n'); tmp.replace(path)


def safe(name):
    return (isinstance(name,str) and bool(name) and not name.startswith('/')
        and '\\' not in name and ':' not in name and '..' not in name.split('/')
        and not any(ord(c)<32 for c in name))


def store(stream, size, work):
    h=hashlib.sha256(); total=0; tmp=work/'incoming'
    with tmp.open('xb') as dest:
        while True:
            block=stream.read(4*1024**2)
            if not block: break
            h.update(block); dest.write(block); total+=len(block)
    require(total==size, 'Truncated source member')
    key=h.hexdigest(); target=work/'blobs'/key
    if target.exists(): tmp.unlink()
    else: tmp.replace(target)
    return key


def stage(args):
    work=args.work;work.mkdir(parents=True,exist_ok=False);(work/'blobs').mkdir()
    save(work/'status.json',dict(stage='staging',pid=os.getpid()))
    inventory=load(args.audit/'inventory.json')
    require(inventory['selection_sha256']==SELECTION_SHA and
            inventory['dataset_sha256']==DATASET_SHA, 'Wrong audit identity')
    require(digest(args.selection)==SELECTION_SHA and digest(args.benchmark)==DATASET_SHA,
            'Wrong pinned benchmark or selection')
    selection=load(args.selection)
    expected={f"{Path(t['notebook']).stem}/{Path(t['notebook']).stem}_comped.tar.gz" for t in selection['tasks']}
    require(len(expected)==61 and {a['path'] for a in inventory['archives']}==expected,
            'Expected all 61 selected notebook archives')
    manifest=dict(schema_version=1,kind='operator-only-historical-input-transport',
        selection_sha256=SELECTION_SHA,dataset_sha256=DATASET_SHA,workflows=72,stages=144,
        offline_complete=False,redistribution_review_complete=False,
        notice='Original solution-like files may be present. Operator only; NEVER mount the bundle or restored whole environments in T1 solver sessions.',
        compact_niriss=False,notebooks=[],extras=[],blobs={})
    projection=None
    if args.compact_niriss:
        projection=load(args.compact_niriss/'manifest.json')
        validation=load(args.compact_niriss_validation/'status.json')
        require(validation.get('stage')=='validated' and validation.get('passed')==2
                and validation.get('image_repeatability') is True, 'Missing two-pass NIRISS validation')
        manifest['compact_niriss']=True
        manifest['niriss_projection']=dict(source_sha256=projection['source_archive_sha256'],
            projected_sha256=projection['projected_archive_sha256'],
            rule=projection['rule'],validation_sha256=digest(args.compact_niriss_validation/'status.json'),
            note='All 70 SCI image planes and scientific primary metadata retained; unused HDUs and existing generated CSV omitted. FITS CHECKSUM/DATASUM cards removed; new file SHA256s recorded in projection evidence. Not byte-identical to historical full-HDU inputs.')
    for i,entry in enumerate(inventory['archives'],1):
        path=args.bench_env/entry['path'];provided_sha=entry['sha256'];provided_bytes=entry['bytes']
        if projection and entry['notebook']=='00_niriss_mast_query_data_setup.ipynb':
            require(projection['source_archive_sha256']==entry['sha256'],'NIRISS source mismatch')
            path=args.compact_niriss/'bench_env'/entry['path']
            provided_sha=projection['projected_archive_sha256'];provided_bytes=projection['projected_archive_bytes']
        require(safe(entry['path']) and not path.is_symlink() and not path.parent.is_symlink(),'Unsafe source')
        require(path.stat().st_size==provided_bytes and digest(path)==provided_sha,'Source archive mismatch')
        save(work/'status.json',dict(stage='staging',pid=os.getpid(),notebooks_done=i-1,
            current_notebook=entry['notebook'],unique_blobs=len(manifest['blobs'])))
        notebook=dict(path=entry['path'],source_sha256=entry['sha256'],provided_sha256=provided_sha,members=[])
        with tarfile.open(path,'r|gz') as source:
            for member in source:
                require(safe(member.name),'Unsafe source member path')
                require(member.isfile() or member.isdir() or member.issym() or member.islnk(),'Special source member')
                data=member.get_info();data['type']=member.type.decode('ascii');data['pax_headers']=member.pax_headers
                item=dict(info=data)
                if member.isfile():
                    with source.extractfile(member) as raw:
                        key=store(raw,member.size,work)
                    item['blob']=key;manifest['blobs'][key]=member.size
                notebook['members'].append(item)
        manifest['notebooks'].append(notebook)
        save(work/'manifest.partial.json',manifest)
    extra=[('operator/astrovisbench_queries.json',args.benchmark,DATASET_SHA,None),
           ('operator/lite72-v2-candidate.json',args.selection,SELECTION_SHA,None)]
    if args.extra_assets:
        for item in load(args.extra_assets):
            extra.append((item['name'],Path(item['path']),item['sha256'],item.get('url')))
    for name,path,expected_sha,url in extra:
        require(safe(name),'Unsafe extra asset name')
        with path.open('rb') as raw: key=store(raw,path.stat().st_size,work)
        require(key==expected_sha,'Extra asset checksum mismatch')
        manifest['blobs'][key]=path.stat().st_size
        manifest['extras'].append(dict(name=name,blob=key,bytes=path.stat().st_size,url=url))
    manifest['unique_blob_bytes']=sum(manifest['blobs'].values())
    manifest['original_member_bytes']=sum(m['info']['size'] for n in manifest['notebooks']
        for m in n['members'] if 'blob' in m)
    save(work/'manifest.json',manifest)
    save(work/'status.json',dict(stage='staged',pid=os.getpid(),notebooks_done=61,
        unique_blobs=len(manifest['blobs']),unique_blob_bytes=manifest['unique_blob_bytes']))
    return manifest


README='''# Lite-72 operator data transport — private sharing candidate

This is a historical-input convenience bundle, NOT a complete offline benchmark
or licence-cleared public release. Some tasks still use live scientific services.
It contains all 61 selected notebook environments plus the pinned benchmark and
specified scientific download assets. Original HTML, plots and helper scripts
may be present: keep the entire bundle and environments OUTSIDE solver sandboxes.
Use audited per-stage input allowlists for coding-agent evaluations.

Identical regular-file payloads are stored once by SHA256. No pixels are cropped,
resampled, rounded or converted. See manifest.json for any explicitly declared
NIRISS projection; it is a different archive, not silently the original full-HDU
input. Historical scores are unchanged and do not certify these restored inputs.
If installer_curation is present, unused compressed installer copies were omitted:
expanded scientific calibration files are unchanged, and readable unique notices
are retained under operator/. One original synphot installer was truncated; this
is disclosed, not silently repaired. No task is dropped to meet the size limit.

The standalone lite72_share_bundle.py uses Python 3.10+ standard library:
    python lite72_share_bundle.py verify lite72-share.tar.xz
    python lite72_share_bundle.py restore lite72-share.tar.xz NEW_DIRECTORY

Restore verifies every blob, then rebuilds bench_env/<notebook>/*_comped.tar.gz
with unchanged regular-file bytes and recorded member metadata. Gzip/tar byte
hashes differ from the originals and are recorded separately. Original paths or
links are never extracted onto the host by this tool. The original evaluator
can subsequently consume the reconstructed archives inside an unprivileged
sandbox. Additional assets under downloads/ are NOT automatically installed in
Astropy caches; operators must configure recorded URLs/cache policy consistently.
Do not silently edit model/reference code to redirect downloads.

Check the external .sha256 before verification. A transport round trip proves
payload integrity, NOT scientific equivalence, T1 isolation or redistribution
permission. No models, packages, credentials, execution caches or model answers
are included (pretrained scientific CNN input weights are task data, not LLMs).
Keep upstream attribution and resolve component licences before redistribution.
'''


def pack(work,threads,max_bytes):
    manifest=load(work/'manifest.json');output=work/'lite72-share.tar.xz'
    require(not output.exists(),'Archive already exists')
    save(work/'status.json',dict(stage='compressing',pid=os.getpid(),blobs_done=0))
    with output.open('xb') as dest:
        proc=subprocess.Popen(['xz',f'-T{threads}','-6','-c'],stdin=subprocess.PIPE,stdout=dest)
        try:
            with tarfile.open(fileobj=proc.stdin,mode='w|') as archive:
                for name,data in [('manifest.json',(json.dumps(manifest,indent=2)+'\n').encode()),
                                  ('README.md',README.encode()),
                                  ('lite72_share_bundle.py',Path(__file__).read_bytes())]:
                    info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644
                    archive.addfile(info,io.BytesIO(data))
                for index,(key,size) in enumerate(manifest['blobs'].items(),1):
                    require(digest(work/'blobs'/key)==key,'Staged blob changed')
                    info=tarfile.TarInfo('blobs/'+key);info.size=size;info.mode=0o644
                    with (work/'blobs'/key).open('rb') as raw: archive.addfile(info,raw)
                    save(work/'status.json',dict(stage='compressing',pid=os.getpid(),
                        blobs_done=index,blobs_total=len(manifest['blobs']),output_bytes=output.stat().st_size))
            proc.stdin.close();require(proc.wait()==0,'xz compression failed')
        except BaseException:
            proc.kill();proc.wait()
            try:proc.stdin.close()
            except OSError:pass
            raise
    size=output.stat().st_size
    require(size<=max_bytes,f'Compressed bundle exceeds target: {size} > {max_bytes}; NOT ready')
    verified=verify(output)
    checksum=digest(output)
    Path(str(output)+'.sha256').write_text(f'{checksum}  {output.name}\n')
    save(work/'status.json',dict(stage='verified',pid=os.getpid(),output_bytes=size,
        max_bytes=max_bytes,sha256=checksum,**verified))
    return output


def validate_manifest(manifest):
    require(manifest.get('schema_version')==1 and manifest.get('selection_sha256')==SELECTION_SHA
        and manifest.get('dataset_sha256')==DATASET_SHA,'Wrong bundle identity')
    require(manifest.get('workflows')==72 and len(manifest['notebooks'])==61,'Wrong coverage')
    paths=set()
    for n in manifest['notebooks']:
        require(safe(n['path']) and len(PurePosixPath(n['path']).parts)==2 and
            n['path'].endswith('_comped.tar.gz') and n['path'] not in paths,'Unsafe/duplicate notebook path')
        paths.add(n['path'])
        for m in n['members']:
            require(safe(m['info']['name']),'Unsafe member path')
            if 'blob' in m:
                require(manifest['blobs'].get(m['blob'])==m['info']['size'],'Member/blob mismatch')
    extra_names=set()
    for e in manifest['extras']:
        require(safe(e['name']) and e['name'].startswith(('operator/','downloads/'))
            and e['name'] not in extra_names and manifest['blobs'].get(e['blob'])==e['bytes'],'Unsafe extra asset')
        extra_names.add(e['name'])
    require(all(re.fullmatch('[0-9a-f]{64}',k) and isinstance(v,int) and v>=0
        for k,v in manifest['blobs'].items()),'Invalid blob table')


def curate_installers(work, output):
    """Omit unused installer containers, retaining all readable unique contents.

    Expanded calibration directories remain unchanged. This does not remove
    scientific arrays; unexpanded files/notices are retained operator-side.
    """
    m=load(work/'manifest.json');validate_manifest(m)
    output.mkdir(parents=True,exist_ok=False);(output/'blobs').mkdir()
    targets=[('miri_1028_photutils','synphot5.tar.gz'),
             ('miri_1028_photutils','webbpsf-data/webbpsf-data-LATEST.tar.gz'),
             ('NIRCam_multiband_photometry','webbpsf-data/webbpsf-data-1.0.0.tar.gz')]
    source=json.loads((work/'blobs'/DATASET_SHA).read_text())
    m['installer_curation']=[]
    for notebook,path in targets:
        n=next(n for n in m['notebooks'] if n['path'].split('/')[0]==notebook)
        files={str(PurePosixPath(x['info']['name'])):x for x in n['members']}
        item=files[path];key=item['blob'];prefix=str(PurePosixPath(path).parent)
        records=[r for r in source if r['nb_path']==notebook+'.ipynb']
        # In the pinned setup, installed data directories suppress download and
        # extraction; the task uses these existing data, not installer bytes.
        setup='\n'.join(r['setup_gt_code'] for r in records)
        if 'synphot5' in path:
            require('os.path.exists(synphot_folder)' in setup and
                    any(x.startswith('grp/') for x in files),'Expanded synphot data absent')
        else:
            require(any(x.startswith('webbpsf-data/webbpsf-data/') for x in files),
                    'Expanded WebbPSF data absent')
        review=dict(notebook=notebook,path=path,original_sha256=key,
            original_bytes=m['blobs'][key],expanded_matches=0,retained_unique_files=[],error=None)
        try:
            with tarfile.open(work/'blobs'/key,'r|gz') as archive:
                for member in archive:
                    if not member.isfile():continue
                    require(safe(member.name),'Unsafe nested member')
                    with archive.extractfile(member) as raw:
                        nested=store(raw,member.size,output)
                    names=[str(PurePosixPath(member.name)),
                           str(PurePosixPath(prefix)/member.name)]
                    matches=[files[name] for name in names if name in files]
                    if any(x.get('blob')==nested for x in matches):
                        review['expanded_matches']+=1
                        # Do not store duplicate nested data in the new package.
                    else:
                        name=f'operator/installer-contents/{notebook}/{PurePosixPath(path).name}/{member.name}'
                        m['extras'].append(dict(name=name,blob=nested,bytes=member.size,url=None))
                        m['blobs'][nested]=member.size
                        review['retained_unique_files'].append(dict(name=member.name,sha256=nested,bytes=member.size))
        except (tarfile.TarError,EOFError,OSError) as error:
            require(path=='synphot5.tar.gz','Unexpected corrupt WebbPSF installer')
            review['error']=f'{type(error).__name__}: {error}'
            # Preserve the exact unreadable tail's already-expanded full input
            # when present; do not describe the damaged installer as validated.
            require(str(PurePosixPath(member.name)) in files,'Damaged member has no expanded counterpart')
            if (output/'incoming').exists():
                (output/'incoming').rename(output/'truncated-installer-fragment.private')
        require(review['expanded_matches']>0,'No expanded calibration match found')
        n['members'].remove(item);m['installer_curation'].append(review)
    used={a['blob'] for n in m['notebooks'] for a in n['members'] if 'blob' in a}
    used.update(e['blob'] for e in m['extras'])
    m['blobs']={k:v for k,v in m['blobs'].items() if k in used}
    for key in m['blobs']:
        target=output/'blobs'/key
        if not target.exists():os.link(work/'blobs'/key,target)
    m['unique_blob_bytes']=sum(m['blobs'].values())
    m['original_member_bytes']=sum(a['info']['size'] for n in m['notebooks'] for a in n['members'] if 'blob' in a)
    m['curated_from_manifest_sha256']=digest(work/'manifest.json')
    if m.get('compact_niriss'):
        m['niriss_projection']['note']='All 70 SCI arrays and scientific primary metadata retained; unused HDUs, FITS CHECKSUM/DATASUM cards and an existing generated CSV omitted. New file SHA256s recorded. Not byte-identical to historical full-HDU inputs.'
    m['curation_notice']='Three unused compressed installers omitted; expanded calibration files unchanged. All readable unique installer files/notices retained under operator/. One original synphot installer is truncated; unreadable fragment is not a usable input.'
    validate_manifest(m);save(output/'manifest.json',m)
    save(output/'installer-review.json',m['installer_curation'])
    save(output/'status.json',dict(stage='staged',pid=os.getpid(),unique_blob_bytes=m['unique_blob_bytes']))
    return m


def verify(bundle, destination=None):
    manifest=None;seen=set()
    with tarfile.open(bundle,'r|xz') as archive:
        for member in archive:
            require(member.isfile() and member.name not in seen,'Non-regular/duplicate outer member')
            seen.add(member.name)
            if member.name=='manifest.json':
                require(manifest is None and len(seen)==1 and member.size<16*1024**2,'Invalid manifest')
                manifest=json.load(archive.extractfile(member));validate_manifest(manifest)
                if destination: save(destination/'manifest.json',manifest)
                continue
            require(manifest is not None,'Manifest must be first')
            if member.name in {'README.md','lite72_share_bundle.py'}:
                require(member.size<1024**2,'Oversized helper')
                continue
            require(member.name.startswith('blobs/'),'Unexpected outer file')
            key=member.name.removeprefix('blobs/')
            require(key in manifest['blobs'] and member.size==manifest['blobs'][key],'Unknown blob')
            with archive.extractfile(member) as raw:
                if destination:
                    found=store(raw,member.size,destination)
                else:
                    h=hashlib.sha256()
                    for block in iter(lambda:raw.read(4*1024**2),b''):h.update(block)
                    found=h.hexdigest()
            require(found==key,'Blob checksum mismatch')
    require(manifest is not None and {'blobs/'+k for k in manifest['blobs']}<=seen,'Missing blobs')
    return dict(notebooks=61,workflows=72,blobs_verified=len(manifest['blobs']),offline_complete=False)


def restore(bundle, output):
    require(not output.exists(),'Restore directory already exists')
    output.mkdir(parents=True);(output/'blobs').mkdir()
    verify(bundle,output)
    manifest=load(output/'manifest.json');restored=[]
    for notebook in manifest['notebooks']:
        path=output/'bench_env'/notebook['path'];path.parent.mkdir(parents=True)
        with tarfile.open(path,'w:gz',compresslevel=1) as archive:
            for member in notebook['members']:
                values=dict(member['info']);headers=values.pop('pax_headers',{})
                info=tarfile.TarInfo(values.pop('name'));values['type']=values['type'].encode('ascii')
                for key,value in values.items():setattr(info,key,value)
                info.pax_headers=headers
                if 'blob' in member:
                    with (output/'blobs'/member['blob']).open('rb') as raw:archive.addfile(info,raw)
                else:archive.addfile(info)
        restored.append(dict(path=notebook['path'],sha256=digest(path)))
    for extra in manifest['extras']:
        path=output/extra['name'];path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/'blobs'/extra['blob'],path)
    save(output/'restored_archives.json',restored)
    return restored


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    build=sub.add_parser('build')
    for key in ['audit','bench-env','selection','benchmark','work']:
        build.add_argument('--'+key,type=Path,required=True)
    build.add_argument('--compact-niriss',type=Path)
    build.add_argument('--compact-niriss-validation',type=Path)
    build.add_argument('--extra-assets',type=Path)
    build.add_argument('--threads',type=int,default=6)
    build.add_argument('--max-bytes',type=int,default=MAX_BYTES)
    resume=sub.add_parser('pack');resume.add_argument('work',type=Path)
    resume.add_argument('--threads',type=int,default=6);resume.add_argument('--max-bytes',type=int,default=MAX_BYTES)
    check=sub.add_parser('verify');check.add_argument('bundle',type=Path)
    curate=sub.add_parser('curate-installers');curate.add_argument('work',type=Path);curate.add_argument('output',type=Path)
    unpack=sub.add_parser('restore');unpack.add_argument('bundle',type=Path);unpack.add_argument('output',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='build':stage(args);print(pack(args.work,args.threads,args.max_bytes))
        elif args.command=='pack':print(pack(args.work,args.threads,args.max_bytes))
        elif args.command=='verify':print(json.dumps(verify(args.bundle)))
        elif args.command=='curate-installers':
            m=curate_installers(args.work,args.output);print(json.dumps(m['installer_curation']))
        else:print(f'Restored {len(restore(args.bundle,args.output))} notebook archives')
    except BaseException as error:
        if hasattr(args,'work') and args.work.is_dir():
            save(args.work/'status.json',dict(stage='failed',error=str(error),pid=os.getpid()))
        raise


if __name__=='__main__':main()
