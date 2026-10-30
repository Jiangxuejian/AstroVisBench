"""Offline, synthetic-only tests; never execute submitted code or call models."""
import base64
from contextlib import ExitStack, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import package_lite72_submission as bundle

PNG = 'data:image/png;base64,' + base64.b64encode(
    base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aB1cAAAAASUVORK5CYII=')).decode()


def dump(path, value):
    path.write_text(json.dumps(value) + '\n')


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'run'
        self.run.mkdir()
        self.source = self.root / 'original.json'
        records = [dict(uid=f'uid-{i:03}', gt_visualization=PNG,
                        processing_gen_code='', visualization_gen_code='',
                        **{key:f'{key}-{i}' for key in bundle.CONTEXT}) for i in range(432)]
        dump(self.source, records)
        self.selected = copy.deepcopy(records[:72])
        self.selection = self.root / 'selection.json'
        dump(self.selection, dict(tasks=[dict(uid=r['uid']) for r in self.selected]))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(bundle, 'SELECTION', self.selection))
        self.stack.enter_context(patch.object(bundle, 'SELECTION_SHA', bundle.sha(self.selection)))
        self.stack.enter_context(patch.object(bundle, 'DATASET_SHA', bundle.sha(self.source)))
        self.manifest = dict(schema_version=1, run_id='synthetic-t0',
            suite='lite72-v2-selection-historical-inputs', track='T0',
            selection_sha256=bundle.SELECTION_SHA, dataset_sha256=bundle.DATASET_SHA,
            upstream_revision=bundle.UPSTREAM, model=dict(requested_id='synthetic'),
            harness=dict(name='synthetic-test', version='1'), generation=dict(tools=[]),
            execution=dict(executor_sha256=bundle.EXECUTOR_SHA, exit_code=0),
            environment=dict(python='synthetic-fixture'), deviations=[],
            judge=dict(run_by_contributor=False))
        self.generated = copy.deepcopy(self.selected)
        self.ledger = []
        for row in self.generated:
            for stage in ['processing', 'visualization']:
                code = "print('synthetic fixture, never executed')"
                row[stage+'_gen_code'] = code
                self.ledger.append(dict(uid=row['uid'], stage=stage, status='submitted',
                    code_sha256=hashlib.sha256(code.encode()).hexdigest(),
                    model_requests=1, output_tokens=10, candidate_checks=0, elapsed_seconds=1.0))
        self.executed = copy.deepcopy(self.generated)
        for row in self.executed:
            row['processing_test'] = dict(pro_success=True, inspection_results={}, pro_output=[])
            row['visualization_test'] = dict(vis_success=True, gen_vis_list=[PNG], vis_output=[])
        for name in ['requirements.freeze.txt', 'execution.log', 'RUN_NOTES.md']:
            (self.run/name).write_text('Synthetic fixture; no real benchmark execution.\n')
        self.flush()

    def flush(self):
        for name, value in [('run_manifest.json', self.manifest), ('selected_benchmark.json', self.selected),
                            ('generated_benchmark.json', self.generated), ('stage_ledger.json', self.ledger),
                            ('executed_benchmark.json', self.executed)]:
            dump(self.run/name, value)

    def validate(self):
        return bundle.validate(self.run, self.source)

    def test_complete_package_and_allowlist(self):
        (self.run/'.env').write_text('SYNTHETIC_SECRET=do-not-package')
        (self.run/'cache').mkdir()
        (self.run/'cache/private.txt').write_text('must not be included')
        original = (self.run/'executed_benchmark.json').read_bytes()
        output = self.root/'submission.tar.gz'
        with redirect_stdout(io.StringIO()):
            bundle.package(self.run, output, True, self.source)
        self.assertEqual((self.run/'executed_benchmark.json').read_bytes(), original)
        with tarfile.open(output) as archive:
            names = set(archive.getnames())
            self.assertEqual(names, {'submission/'+name for name in bundle.REQUIRED}
                             | {'submission/suite_manifest.json', 'submission/submission_manifest.json'})
            self.assertTrue(all(m.isfile() and m.uid == m.gid == 0 for m in archive.getmembers()))
            self.assertEqual(archive.extractfile('submission/executed_benchmark.json').read(), original)
            metadata = json.load(archive.extractfile('submission/submission_manifest.json'))
            for name, digest in metadata['files_sha256'].items():
                self.assertEqual(hashlib.sha256(archive.extractfile('submission/'+name).read()).hexdigest(), digest)
            self.assertEqual(metadata['validation']['status'], 'structurally_complete_unjudged')
            self.assertFalse(metadata['validation']['judge_run'])
        self.assertEqual(output.with_name(output.name+'.sha256').read_text().split()[0], bundle.sha(output))
        with self.assertRaisesRegex(ValueError, 'already exists'):
            bundle.package(self.run, output, True, self.source)

    def test_source_hash_and_context_identity(self):
        self.source.write_text(self.source.read_text()+' ')
        with self.assertRaisesRegex(ValueError, 'source dataset checksum'):
            self.validate()

    def test_refuse_reference_or_candidate_repair(self):
        for key in ['processing_gen_code', 'visualization_gen_code', 'processing_gt_code', 'gt_visualization']:
            saved = self.executed[0][key]
            self.executed[0][key] = 'modified'
            self.flush()
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, 'execution changed'):
                self.validate()
            self.executed[0][key] = saved

    def test_missing_stage_is_flagged_not_successfully_repaired(self):
        self.generated[0]['processing_gen_code'] = ''
        self.executed[0]['processing_gen_code'] = ''
        self.ledger[0].update(status='missing', code_sha256=None)
        self.flush()
        summary = self.validate()
        self.assertEqual(summary['status'], 'needs_missing_submission_accounting')
        self.assertEqual(summary['missing_stages'], [dict(uid='uid-000', stage='processing')])
        self.assertTrue(json.loads((self.run/'executed_benchmark.json').read_text())[0]['processing_test']['pro_success'])

    def test_t1_enforcement_limits_and_evidence(self):
        self.manifest['track'] = 'T1'
        self.manifest['generation'] = dict(limits_enforcement='external', tools=bundle.T1_TOOLS, limits=bundle.T1_LIMITS)
        (self.run/'generation_events.jsonl').write_text('{"synthetic":true}\n')
        self.flush()
        self.assertEqual(self.validate()['track'], 'T1')
        self.manifest['generation']['limits_enforcement'] = 'prompt_only'
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Prompt-only'):
            self.validate()
        self.manifest['generation']['limits_enforcement'] = 'external'
        self.ledger[0]['model_requests'] = 21
        self.flush()
        with self.assertRaisesRegex(ValueError, 'within 20'):
            self.validate()

    def test_duplicate_and_incomplete_execution(self):
        self.executed[-1] = copy.deepcopy(self.executed[0])
        self.flush()
        with self.assertRaisesRegex(ValueError, 'duplicate or unknown'):
            self.validate()
        self.executed.pop()
        self.flush()
        with self.assertRaisesRegex(ValueError, 'all 72'):
            self.validate()

    def test_required_inspection_and_embedded_png(self):
        self.executed[0]['processing_test'].pop('inspection_results')
        self.flush()
        with self.assertRaisesRegex(ValueError, 'skip-test'):
            self.validate()
        self.executed[0]['processing_test']['inspection_results'] = {}
        self.executed[0]['visualization_test']['gen_vis_list'] = ['/home/someone/plot.png']
        self.flush()
        with self.assertRaisesRegex(ValueError, 'embedded PNG'):
            self.validate()

    def test_crash_and_plot_count_failures_not_dropped(self):
        self.executed[0]['visualization_test'] = dict(vis_success=False, gen_vis_list=[])
        self.executed[1]['visualization_test'] = dict(vis_success=True, gen_vis_list=[])
        self.executed[2]['visualization_test'] = dict(vis_success=True, gen_vis_list=[PNG, PNG])
        self.flush()
        self.assertEqual(self.validate()['visualization_records'], dict(crash=1, plot_count_failure=2, single_png=69))

    def test_raw_nonfinite_values_accepted_without_rewriting(self):
        self.executed[0]['unused_diagnostic'] = float('nan')
        self.flush()
        original = (self.run/'executed_benchmark.json').read_bytes()
        self.assertIn(b'NaN', original)
        self.assertEqual(self.validate()['workflows'], 72)
        self.assertEqual((self.run/'executed_benchmark.json').read_bytes(), original)

    def test_no_symlinks_or_unreviewed_packaging(self):
        output = self.root/'result.tar.gz'
        with self.assertRaisesRegex(ValueError, 'Review all included files'):
            bundle.package(self.run, output, False, self.source)
        (self.run/'generation_adapter.py').symlink_to(self.root/'nonexistent')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            bundle.package(self.run, output, True, self.source)
        self.assertFalse(output.exists())

    def test_streaming_json_boundaries_and_malformed_input(self):
        path = self.root/'stream.json'
        path.write_text('[ {"a": "unicode λ \\"quoted\\""}, {"b": NaN} ]\n')
        rows = list(bundle.iter_records(path, chunk_size=3))
        self.assertEqual(len(rows), 2)
        self.assertIn('unicode λ', rows[0]['a'])
        for invalid in ['[{},]', '[{}', '[{}]junk', '{}', '[1]']:
            path.write_text(invalid)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                list(bundle.iter_records(path, chunk_size=2))


if __name__ == '__main__':
    unittest.main()
