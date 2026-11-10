"""Offline, synthetic-only tests; never execute submitted code or call models."""
import base64
from contextlib import ExitStack, redirect_stderr, redirect_stdout
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

    def test_new_run_template_defaults_to_versioned_t1(self):
        template = json.loads((bundle.ROOT/'submission/run_manifest.example.json').read_text())
        self.assertEqual(template['track'], 'T1')
        generation = template['generation']
        self.assertEqual(generation['protocol_id'], bundle.T1_PROTOCOL_ID)
        self.assertEqual(generation['limits_enforcement'], 'external')
        self.assertEqual(generation['tools'], bundle.T1_TOOLS)
        self.assertEqual(generation['limits'], bundle.T1_LIMITS)
        prompt = (bundle.ROOT/'LITE72_AGENT_PROMPT.md').read_text()
        self.assertIn('TRACK = T1', prompt)
        self.assertIn('Never silently switch to T0/pilot', prompt)

    def test_missing_track_is_not_inferred_from_new_run_default(self):
        self.manifest.pop('track')
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Declare T0, T1 or agent-pilot'):
            self.validate()

    def test_explicit_alternative_tracks_remain_available(self):
        for track in ['T0', 'agent-pilot']:
            with self.subTest(track=track):
                self.manifest['track'] = track
                self.flush()
                self.assertEqual(self.validate()['track'], track)

    def versioned_t1(self, checks=0):
        self.manifest['track'] = 'T1'
        self.manifest['generation'] = dict(limits_enforcement='external',
            tools=bundle.T1_TOOLS, limits=bundle.T1_LIMITS,
            protocol_id=bundle.T1_PROTOCOL_ID, protocol_sha256=bundle.sha(bundle.T1_PROTOCOL),
            solver_instructions_sha256=bundle.sha(bundle.T1_SOLVER_INSTRUCTIONS))
        for entry in self.ledger:
            entry.update(candidate_checks=checks,
                last_checked_code_sha256=entry['code_sha256'] if checks else None,
                latest_complete_code_sha256=entry['code_sha256'], terminal_reason='submitted')
        (self.run/'generation_events.jsonl').write_text('{"synthetic":true}\n')
        self.flush()

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

    def test_check_only_cli_does_not_write_or_modify_files(self):
        before = {p.name: p.read_bytes() for p in self.run.iterdir()}
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            bundle.main(['--run-dir', str(self.run), '--benchmark', str(self.source), '--check-only'])
        summary = json.loads(stdout.getvalue())
        self.assertEqual(summary['workflows'], 72)
        self.assertEqual(summary['stage_terminals'], 144)
        self.assertFalse(summary['judge_run'])
        self.assertEqual({p.name: p.read_bytes() for p in self.run.iterdir()}, before)
        self.assertFalse(list(self.root.glob('*.tar.gz*')))

    def test_check_only_cli_reports_missing_evidence(self):
        (self.run/'RUN_NOTES.md').unlink()
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            bundle.main(['--run-dir', str(self.run), '--benchmark', str(self.source), '--check-only'])
        self.assertEqual(error.exception.code, 2)
        self.assertIn('Missing required submission file: RUN_NOTES.md', stderr.getvalue())
        self.assertFalse(list(self.root.glob('*.tar.gz*')))

    def test_cli_requires_output_only_for_packaging(self):
        argv = ['--run-dir', str(self.run), '--benchmark', str(self.source)]
        for extra, message in [([], '--output is required'),
                               (['--check-only', '--output', str(self.root/'bad.tar.gz')],
                                'omit --output')]:
            stderr = io.StringIO()
            with self.subTest(extra=extra), redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                bundle.main(argv + extra)
            self.assertEqual(error.exception.code, 2)
            self.assertIn(message, stderr.getvalue())
        self.assertFalse(list(self.root.glob('*.tar.gz*')))

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
        for field, excessive, message in [('model_requests', 21, 'within 20'),
                                          ('output_tokens', 32769, 'within 32768'),
                                          ('candidate_checks', 4, 'within 3'),
                                          ('elapsed_seconds', 2401, 'elapsed_seconds')]:
            original = self.ledger[0][field]
            self.ledger[0][field] = excessive
            self.flush()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, message):
                self.validate()
            self.ledger[0][field] = original

    def test_versioned_t1_and_legacy_declarations_are_distinct(self):
        self.versioned_t1()
        result = self.validate()
        self.assertEqual(result['generation_protocol'], bundle.T1_PROTOCOL_ID)
        self.assertEqual(result['protocol_declaration_check'], 'declared_contract_hashes_checked')
        for field in ['protocol_id', 'protocol_sha256', 'solver_instructions_sha256']:
            self.manifest['generation'].pop(field)
        self.flush()
        result = self.validate()
        self.assertIsNone(result['generation_protocol'])
        self.assertEqual(result['protocol_declaration_check'], 'legacy_unversioned_requires_review')

    def test_versioned_t1_rejects_wrong_policy_id_or_hashes(self):
        self.versioned_t1()
        for field, value, message in [('protocol_id', 'another-policy', 'Unsupported T1'),
                                       ('protocol_sha256', '0'*64, 'protocol checksum'),
                                       ('solver_instructions_sha256', '0'*64, 'solver instructions checksum')]:
            original = self.manifest['generation'][field]
            self.manifest['generation'][field] = value
            self.flush()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, message):
                self.validate()
            self.manifest['generation'][field] = original
        self.manifest['generation'].pop('protocol_id')
        self.flush()
        with self.assertRaisesRegex(ValueError, 'hashes require a protocol_id'):
            self.validate()

    def test_versioned_t1_last_checked_wins_over_unchecked_edit(self):
        self.versioned_t1(checks=1)
        entry = self.ledger[0]
        # An unsubmitted newer edit may exist, but the checked A remains frozen.
        entry['latest_complete_code_sha256'] = '0'*64
        self.flush()
        self.assertEqual(self.validate()['track'], 'T1')
        # Submitting an untested B, even with correct generated/executed hashes,
        # must not replace checked A after the request budget is exhausted.
        code_b = "print('different synthetic candidate; never executed')"
        self.generated[0]['processing_gen_code'] = code_b
        self.executed[0]['processing_gen_code'] = code_b
        entry['code_sha256'] = hashlib.sha256(code_b.encode()).hexdigest()
        entry['latest_complete_code_sha256'] = entry['code_sha256']
        self.flush()
        with self.assertRaisesRegex(ValueError, 'exact last checked candidate'):
            self.validate()

    def test_versioned_t1_zero_checks_and_missing_submission(self):
        self.versioned_t1()
        entry = self.ledger[0]
        original = entry['latest_complete_code_sha256']
        entry['latest_complete_code_sha256'] = '0'*64
        self.flush()
        with self.assertRaisesRegex(ValueError, 'zero checks'):
            self.validate()
        entry['latest_complete_code_sha256'] = original
        entry['last_checked_code_sha256'] = original
        self.flush()
        with self.assertRaisesRegex(ValueError, 'zero checks'):
            self.validate()
        self.generated[0]['processing_gen_code'] = ''
        self.executed[0]['processing_gen_code'] = ''
        entry.update(status='missing', code_sha256=None, last_checked_code_sha256=None,
                     latest_complete_code_sha256=None, terminal_reason='no_complete_candidate')
        self.flush()
        self.assertEqual(self.validate()['status'], 'needs_missing_submission_accounting')

    def test_versioned_t1_requires_freeze_fields_and_valid_terminal_reason(self):
        self.versioned_t1(checks=1)
        entry = self.ledger[0]
        for field in ['last_checked_code_sha256', 'latest_complete_code_sha256', 'terminal_reason']:
            original = entry.pop(field)
            self.flush()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'must record '+field):
                self.validate()
            entry[field] = original
        entry['terminal_reason'] = 'fresh_budget'
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Unknown T1 terminal_reason'):
            self.validate()
        entry['terminal_reason'] = 'candidate_check_limit'
        self.flush()
        with self.assertRaisesRegex(ValueError, 'requires three'):
            self.validate()
        entry['candidate_checks'] = 3
        self.flush()
        self.assertEqual(self.validate()['track'], 'T1')

    def test_versioned_t1_package_includes_declared_policy(self):
        self.versioned_t1(checks=3)
        output = self.root/'versioned-t1.tar.gz'
        with redirect_stdout(io.StringIO()):
            bundle.package(self.run, output, True, self.source)
        with tarfile.open(output) as archive:
            self.assertEqual(archive.extractfile('submission/t1_protocol.json').read(),
                             bundle.T1_PROTOCOL.read_bytes())
            self.assertEqual(archive.extractfile('submission/t1_solver_instructions.txt').read(),
                             bundle.T1_SOLVER_INSTRUCTIONS.read_bytes())
            metadata = json.load(archive.extractfile('submission/submission_manifest.json'))
            self.assertEqual(metadata['files_sha256']['t1_protocol.json'],
                             self.manifest['generation']['protocol_sha256'])

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
