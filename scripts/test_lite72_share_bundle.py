"""Synthetic lossless transport tests; no science execution or network."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import lite72_share_bundle as tool


class ShareBundleTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.env=self.root/'env';self.env.mkdir()
        self.audit=self.root/'audit';self.audit.mkdir();archives=[]
        self.selection=self.root/'selection.json'
        self.selection.write_text(json.dumps({'tasks':[dict(notebook=f'n{i%61}.ipynb') for i in range(72)]}))
        self.benchmark=self.root/'source.json';self.benchmark.write_text('[]')
        self.addCleanup(patch.stopall)
        patch.object(tool,'SELECTION_SHA',tool.digest(self.selection)).start()
        patch.object(tool,'DATASET_SHA',tool.digest(self.benchmark)).start()
        for i in range(61):
            p=self.env/f'n{i}'/f'n{i}_comped.tar.gz';p.parent.mkdir()
            with tarfile.open(p,'w:gz') as a:
                m=tarfile.TarInfo('science.fits');m.size=12;m.mode=0o640
                a.addfile(m,io.BytesIO(b'science-data'))
                link=tarfile.TarInfo('alias');link.type=tarfile.SYMTYPE;link.linkname='science.fits';a.addfile(link)
            archives.append(dict(path=f'n{i}/n{i}_comped.tar.gz',notebook=f'n{i}.ipynb',
                sha256=tool.digest(p),bytes=p.stat().st_size))
        tool.save(self.audit/'inventory.json',dict(selection_sha256=tool.SELECTION_SHA,
            dataset_sha256=tool.DATASET_SHA,archives=archives))
        self.work=self.root/'work'
        self.args=argparse.Namespace(work=self.work,audit=self.audit,bench_env=self.env,
            selection=self.selection,benchmark=self.benchmark,compact_niriss=None,
            compact_niriss_validation=None,extra_assets=None)

    def test_dedup_pack_verify_restore_roundtrip(self):
        manifest=tool.stage(self.args)
        self.assertEqual(manifest['original_member_bytes'],61*12)
        self.assertEqual(len(manifest['blobs']),3)  # science + pinned source + selection
        self.assertFalse(manifest['offline_complete'])
        self.assertFalse(manifest['redistribution_review_complete'])
        bundle=tool.pack(self.work,1,1_000_000)
        self.assertEqual(tool.verify(bundle)['blobs_verified'],3)
        restored=self.root/'restored';tool.restore(bundle,restored)
        for i in range(61):
            path=restored/'bench_env'/f'n{i}'/f'n{i}_comped.tar.gz'
            with tarfile.open(path) as a:
                self.assertEqual(a.extractfile('science.fits').read(),b'science-data')
                self.assertEqual(a.getmember('science.fits').mode,0o640)
                self.assertTrue(a.getmember('alias').issym())
        self.assertFalse((restored/'science.fits').exists())
        with self.assertRaisesRegex(ValueError,'already exists'):tool.restore(bundle,restored)

    def test_corrupt_stage_blob_refused(self):
        manifest=tool.stage(self.args)
        key=next(iter(manifest['blobs']))
        (self.work/'blobs'/key).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'Staged blob changed'):
            tool.pack(self.work,1,1_000_000)

    def test_size_limit_is_total_bytes_not_parts(self):
        tool.stage(self.args)
        with self.assertRaisesRegex(ValueError,'exceeds target'):
            tool.pack(self.work,1,1)
        self.assertFalse(Path(str(self.work/'lite72-share.tar.xz')+'.sha256').exists())

    def test_changed_source_refused(self):
        (self.env/'n0'/'n0_comped.tar.gz').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Source archive mismatch'):tool.stage(self.args)

    def test_installer_curation_keeps_expanded_scientific_payload(self):
        m=tool.stage(self.args)
        data=b'science-data';data_key=hashlib.sha256(data).hexdigest()
        source=json.dumps([{'nb_path':'miri_1028_photutils.ipynb',
            'setup_gt_code':'os.path.exists(synphot_folder)'}]).encode()
        source_key=tool.store(io.BytesIO(source),len(source),self.work)
        patch.object(tool,'DATASET_SHA',source_key).start();m['dataset_sha256']=source_key
        m['blobs'][source_key]=len(source)
        m['extras'][0].update(blob=source_key,bytes=len(source))
        def info(name,size):
            t=tarfile.TarInfo(name);t.size=size
            v=t.get_info();v['type']=t.type.decode();v['pax_headers']={}
            return v
        for i,notebook in [(0,'miri_1028_photutils'),(1,'NIRCam_multiband_photometry')]:
            m['notebooks'][i]['path']=f'{notebook}/{notebook}_comped.tar.gz'
            m['notebooks'][i]['members'].append(dict(
                info=info('webbpsf-data/webbpsf-data/cal.fits',len(data)),blob=data_key))
        m['notebooks'][0]['members'].append(dict(info=info('grp/cal.fits',len(data)),blob=data_key))
        targets=[(0,'synphot5.tar.gz','grp/cal.fits'),
                 (0,'webbpsf-data/webbpsf-data-LATEST.tar.gz','webbpsf-data/cal.fits'),
                 (1,'webbpsf-data/webbpsf-data-1.0.0.tar.gz','webbpsf-data/cal.fits')]
        for i,name,nested_name in targets:
            p=self.root/('installer'+str(i)+Path(name).name)
            with tarfile.open(p,'w:gz') as a:
                t=tarfile.TarInfo(nested_name);t.size=len(data);a.addfile(t,io.BytesIO(data))
            with p.open('rb') as f:key=tool.store(f,p.stat().st_size,self.work)
            m['blobs'][key]=p.stat().st_size
            m['notebooks'][i]['members'].append(dict(info=info(name,p.stat().st_size),blob=key))
        tool.save(self.work/'manifest.json',m)
        dest=self.root/'curated';curated=tool.curate_installers(self.work,dest)
        self.assertEqual(len(curated['installer_curation']),3)
        self.assertTrue(all(r['expanded_matches']==1 for r in curated['installer_curation']))
        self.assertIn(data_key,curated['blobs'])
        for i,name,_ in targets:
            self.assertNotIn(name,[a['info']['name'] for a in curated['notebooks'][i]['members']])
            self.assertIn(name,[a['info']['name'] for a in m['notebooks'][i]['members']])
        self.assertEqual(tool.load(self.work/'manifest.json'),m)
        self.assertEqual(tool.verify(tool.pack(dest,1,1_000_000))['workflows'],72)

    def test_unsafe_extra_refused(self):
        m=tool.stage(self.args)
        for name in ['../outside','blobs/replace','manifest.json','/absolute','operator/../outside']:
            m['extras'][0]['name']=name
            with self.assertRaisesRegex(ValueError,'Unsafe extra'):tool.validate_manifest(m)

    def test_unsafe_inner_path_refused(self):
        m=tool.stage(self.args);m['notebooks'][0]['members'][0]['info']['name']='../outside'
        with self.assertRaisesRegex(ValueError,'Unsafe member'):tool.validate_manifest(m)

    def test_wrong_identity_and_missing_notebook_refused(self):
        m=tool.stage(self.args);m['dataset_sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'identity'):tool.validate_manifest(m)
        m['dataset_sha256']=tool.DATASET_SHA;m['notebooks'].pop()
        with self.assertRaisesRegex(ValueError,'coverage'):tool.validate_manifest(m)


if __name__=='__main__':unittest.main()
