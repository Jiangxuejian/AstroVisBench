"""Synthetic offline tests: no scientific inputs, network or model execution."""
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import prepare_lite72_data as tool


class DataBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = self.root/'bench_env'
        self.env.mkdir()
        self.selection = self.root/'selection.json'
        tasks = [dict(uid=str(i), notebook=f'nb{i%61}.ipynb', data_strategy='frozen_file_assets')
                 for i in range(72)]
        self.write(self.selection, dict(tasks=tasks))
        self.benchmark = self.root/'benchmark.json'
        self.write(self.benchmark, [dict(uid=str(i), nb_path=f'nb{i%61}.ipynb',
            setup_gt_code='', processing_gt_code='', visualization_gt_code='') for i in range(432)])
        for i in range(61):
            path=self.env/f'nb{i}'/f'nb{i}_comped.tar.gz'
            path.parent.mkdir()
            self.archive(path, ['science.fits', 'requirements.txt'])
        self.addCleanup(patch.stopall)
        patch.object(tool, 'SELECTION', self.selection).start()
        patch.object(tool, 'SELECTION_SHA', tool.sha(self.selection)).start()
        patch.object(tool, 'DATASET_SHA', tool.sha(self.benchmark)).start()
        self.auditdir=self.root/'audit'

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value))

    @staticmethod
    def archive(path, names):
        with tarfile.open(path, 'w:gz') as archive:
            for name in names:
                info=tarfile.TarInfo(name); info.size=3
                archive.addfile(info, io.BytesIO(b'raw'))

    def audit(self):
        return tool.audit(self.benchmark, self.env, self.auditdir)

    def approve(self):
        review=tool.load(self.auditdir/'review.template.json')
        for entry in review['files']:
            entry.update(source_url='https://example.org/source', license='test-fixture-only',
                         notice='Synthetic fixture', reviewed_by='test',
                         redistribution_approved=True, raw_input_reviewed=True)
        path=self.root/'review.json'
        self.write(path, review)
        return path

    def test_audit_coverage_and_no_implicit_clearance(self):
        result=self.audit()
        self.assertEqual(len(result['archives']),61)
        self.assertEqual(len(result['tasks']),72)
        self.assertFalse(result['release_ready'])
        self.assertFalse(result['offline_ready'])
        self.assertTrue(all(a['license_status']=='UNREVIEWED' for a in result['archives']))
        self.assertNotIn(str(self.root), (self.auditdir/'inventory.json').read_text())
        self.assertFalse((self.env/'nb0'/'science.fits').exists())

    def test_hash_mismatch_stops_before_output(self):
        self.benchmark.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.audit()
        self.assertFalse(self.auditdir.exists())

    def test_header_refresh_retains_evidence_and_resets_reviews(self):
        self.audit()
        path=self.auditdir/'inventory.json';before=tool.load(path)
        before['archives'][0]['flags']={'outdated_rule':1}
        self.write(path,before)
        target=self.root/'refreshed'
        result=tool.refresh_flags(self.auditdir,target)
        self.assertEqual(result['header_review_from_inventory_sha256'],tool.sha(path))
        self.assertEqual(result['archives'][0]['sha256'],before['archives'][0]['sha256'])
        self.assertFalse(result['archives'][0]['flags'])
        self.assertFalse(result['release_ready'])
        self.assertFalse(tool.load(target/'review.template.json')['files'][0]['raw_input_reviewed'])

    def test_member_flags_and_no_extraction(self):
        path=self.env/'nb0'/'nb0_comped.tar.gz'
        self.archive(path, ['../escape', '/absolute', 'solution.html', '.env',
                            'image.png', 'nested.tar.gz', '._data', 'same', './same'])
        result=self.audit()
        flags=result['archives'][0]['flags']
        for key in ['unsafe_path','solution_or_executable_review','possible_secret',
                    'possible_reference_image_review','nested_archive_review',
                    'platform_sidecar','duplicate_member']:
            self.assertIn(key,flags)
        self.assertFalse((self.root/'escape').exists())
        with self.assertRaisesRegex(ValueError,'Unresolved archive flags'):
            tool.package(self.auditdir,self.env,self.approve(),self.root/'bundle.tar.gz')

    def test_links_and_specials_flagged(self):
        for kind in [tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.CHRTYPE,tarfile.FIFOTYPE]:
            member=tarfile.TarInfo('science.fits');member.type=kind
            self.assertIn('link_or_special_file',tool.member_flags(member))
        for name in ['C:/input', 'a\\b', 'a/../b', 'a\nfile']:
            self.assertFalse(tool.safe_name(name))
        for name in ['calibration.fits.gz','sources.csv.gz','spectra.dat.bz2']:
            self.assertEqual(tool.member_flags(tarfile.TarInfo(name)), [])

    def test_unreviewed_package_is_blocked(self):
        self.audit()
        target=self.root/'bundle.tar.gz'
        with self.assertRaisesRegex(ValueError,'review incomplete'):
            tool.package(self.auditdir,self.env,self.auditdir/'review.template.json',target)
        self.assertFalse(target.exists())

    def test_reproducible_allowlisted_package_and_no_overwrite(self):
        self.audit();review=self.approve()
        first,second=self.root/'first.tar.gz',self.root/'second.tar.gz'
        tool.package(self.auditdir,self.env,review,first)
        tool.package(self.auditdir,self.env,review,second)
        self.assertEqual(tool.sha(first),tool.sha(second))
        with tarfile.open(first) as archive:
            self.assertEqual(len(archive.getmembers()),62)
            self.assertTrue(all(m.isfile() for m in archive))
            manifest=json.load(archive.extractfile('manifest.json'))
            self.assertFalse(manifest['offline_ready'])
            self.assertEqual(len(manifest['files']),61)
        self.assertIn(tool.sha(first),Path(str(first)+'.sha256').read_text())
        with self.assertRaisesRegex(ValueError,'already exists'):
            tool.package(self.auditdir,self.env,review,first)

    def test_source_change_and_symlink_rejected(self):
        self.audit();review=self.approve()
        path=self.env/'nb0'/'nb0_comped.tar.gz'
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Source changed'):
            tool.package(self.auditdir,self.env,review,self.root/'bad.tar.gz')
        other=self.root/'original';path.rename(other);path.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'Symlinked source'):
            tool.package(self.auditdir,self.env,review,self.root/'bad.tar.gz')

    def test_missing_archives_reported_not_filled(self):
        (self.env/'nb0'/'nb0_comped.tar.gz').unlink()
        result=self.audit()
        self.assertFalse(result['archives'][0]['available'])
        self.assertIn('missing_archive',result['archives'][0]['flags'])

    def test_review_identity_and_allowlist_cannot_change(self):
        self.audit();review=self.approve()
        inv=self.auditdir/'inventory.json';value=tool.load(inv)
        value['archives'][0]['path']='../outside'
        self.write(inv,value)
        with self.assertRaisesRegex(ValueError,'Review/inventory mismatch'):
            tool.package(self.auditdir,self.env,review,self.root/'bad.tar.gz')
        approval=tool.load(review);approval['inventory_sha256']=tool.sha(inv);self.write(review,approval)
        with self.assertRaisesRegex(ValueError,'Archive allowlist'):
            tool.package(self.auditdir,self.env,review,self.root/'bad.tar.gz')


if __name__=='__main__':
    unittest.main()
