"""Validate public scalar provenance, null judge scores and linked content."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from statistics import mean
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/data'


class PublicationTests(unittest.TestCase):
    def test_complete_selection_and_metric_denominators(self):
        manifest=DATA/'lite72-v2-candidate.json'
        digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.assertEqual(digest,'a9ed93a935b2e984e546fdebbcfef7b0f14879e3b93064db6985e34ef4541f3b')
        uids={r['uid'] for r in json.loads(manifest.read_text())['tasks']}
        for name,processing,visualization,eligible in [
                ('gpt6-v2-selection-audit.json',48,60,40),
                ('claude-k3-v2-selection-audit.json',44,62,33)]:
            audit=json.loads((DATA/name).read_text())
            self.assertEqual(audit['selection_sha256'],digest)
            self.assertFalse(audit['official_frozen_input_v2_result'])
            rows=audit['records']
            self.assertEqual(len(rows),72)
            self.assertEqual({r['uid'] for r in rows},uids)
            self.assertEqual(sum(r['processing_success'] for r in rows),processing)
            self.assertEqual(sum(r['visualization_success'] for r in rows),visualization)
            vi=[r['vi_score'] for r in rows if r['processing_success'] and r['vi_score'] is not None]
            self.assertEqual(len(vi),eligible)
            self.assertAlmostEqual(mean(vi),audit['metrics']['vi_score'])
            self.assertEqual(Counter(r['execution_artifact'] for r in rows),
                             {'baseline_execution':65,'supplement_execution':7})

    def test_new_chart_rows_match_audits_and_do_not_invent_judgments(self):
        leaderboard=json.loads((DATA/'leaderboard.json').read_text())
        self.assertEqual(len({r['id'] for r in leaderboard['rows']}),len(leaderboard['rows']))
        for row in leaderboard['rows']:
            if 'v2-selection' not in row['id']:continue
            audit=json.loads((ROOT/'docs'/row['audit']).read_text())
            for metric in leaderboard['metrics']:
                self.assertEqual(row[metric],audit['metrics'][metric])
            for metric in ['correct_v','vis_fail','minor','major']:
                self.assertIsNone(row[metric])
            self.assertEqual(row['judge_status'],'pending')
        qwen=next(r for r in leaderboard['rows'] if r['id']=='qwen38-27b-q4-k-m')
        self.assertEqual(qwen['label'].splitlines()[1],'27B Q4_K_M')

    def test_sanitized_exports_and_local_links(self):
        for name in ['gpt6-v2-selection-audit.json','claude-k3-v2-selection-audit.json','lite72-v2-candidate.json']:
            text=(DATA/name).read_text()
            for forbidden in ['/mnt/','/home/','Bearer ','Authorization','access_token','refresh_token']:
                self.assertNotIn(forbidden,text)
        for name in ['README.md','LITE72_RUN_GUIDE.md','docs/index.md','docs/lite72-v2-historical.md','docs/execution-fairness.md']:
            path=ROOT/name
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                if re.match(r'\w+://',target) or target.startswith('#'):continue
                target=target.split('#',1)[0]
                self.assertTrue((path.parent/target).exists(),f'{name}: {target}')


if __name__=='__main__':unittest.main()
