"""Snapshot integrity and non-overwrite checks; no benchmark execution."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from archive_leaderboard import create_snapshot


ROOT = Path(__file__).resolve().parents[1]


class SnapshotTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root/'docs/data').mkdir(parents=True)
        (root/'docs/assets').mkdir()
        payload = {'sources': {}, 'rows': [], 'display_order': {'sort_by': 'example'}}
        (root/'docs/data/leaderboard.json').write_text(json.dumps(payload))
        for name in ('lite72-v2-candidate.json', 'lite72-candidate-v1.json'):
            (root/'docs/data'/name).write_text('{}')
        for extension in ('png', 'svg'):
            (root/f'docs/assets/leaderboard-portrait.{extension}').write_bytes(b'fixture')
        (root/'docs/index.md').write_text('| Model | Suite |\n|---|---|\n')
        return root

    def test_snapshot_records_real_date_and_identical_score_bytes(self):
        root = self.fixture()
        path = create_snapshot(root, '20261101', '2026-11-13')
        manifest = json.loads((path/'manifest.json').read_text())
        self.assertEqual(manifest['leaderboard_version'], '20261101')
        self.assertEqual(manifest['assembled_on'], '2026-11-13')
        self.assertFalse(manifest['scores_recalculated'])
        self.assertEqual((path/'leaderboard.json').read_bytes(),
                         (root/'docs/data/leaderboard.json').read_bytes())

    def test_existing_snapshot_is_never_overwritten(self):
        root = self.fixture()
        path = create_snapshot(root, '20261101', '2026-11-13')
        before = (path/'manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):
            create_snapshot(root, '20261101', '2026-11-14')
        self.assertEqual((path/'manifest.json').read_bytes(), before)

    def test_invalid_version_and_assembly_date_are_rejected(self):
        root = self.fixture()
        for version in ('../20261101', '20260230', '2026-11-01', 'abcdefgh'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                create_snapshot(root, version, '2026-11-13')
        with self.assertRaises(ValueError):
            create_snapshot(root, '20261101', '2026-02-30')

    def test_missing_input_does_not_leave_partial_snapshot(self):
        root = self.fixture()
        (root/'docs/data/lite72-v2-candidate.json').unlink()
        with self.assertRaises(FileNotFoundError):
            create_snapshot(root, '20261101', '2026-11-13')
        self.assertFalse((root/'docs/leaderboards/20261101').exists())

    def test_audit_cannot_escape_public_data_directory(self):
        root = self.fixture()
        path = root/'docs/data/leaderboard.json'
        payload = json.loads(path.read_text())
        payload['rows'] = [{'audit': 'data/../../private.txt'}]
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, 'public docs/data'):
            create_snapshot(root, '20261101', '2026-11-13')

    def test_frozen_public_snapshot_matches_every_recorded_checksum(self):
        path = ROOT/'docs/leaderboards/20261101'
        manifest = json.loads((path/'manifest.json').read_text())
        self.assertEqual(manifest['leaderboard_version'], '20261101')
        self.assertEqual(manifest['assembled_on'], '2026-11-13')
        for name, expected in manifest['files'].items():
            data = (path/name).read_bytes()
            self.assertEqual(len(data), expected['bytes'], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected['sha256'], name)
        payload = (path/'leaderboard.json').read_bytes()
        self.assertEqual(hashlib.sha256(payload).hexdigest(), manifest['score_data_sha256'])
        self.assertIn('separate VIscore', manifest['layout'])


if __name__ == '__main__':
    unittest.main()
