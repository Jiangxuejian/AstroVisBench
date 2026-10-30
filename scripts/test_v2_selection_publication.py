"""Validate public scalar provenance, completed judge coverage and linked content."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
from statistics import mean
import unittest
import xml.etree.ElementTree as ET

from leaderboard_order import GROUPS, group_id, ordered_rows
from order_leaderboard import reorder_markdown

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/data'


class PublicationTests(unittest.TestCase):
    def test_display_order_and_table_match(self):
        leaderboard=json.loads((DATA/'leaderboard.json').read_text())
        rows=leaderboard['rows']
        self.assertEqual(rows,ordered_rows(rows))
        self.assertEqual([r['id'] for r in rows],[
            'gpt6-lite72-v2-selection','claude-k3-lite72-v2-selection',
            'kimi-k3','gemini-2.5-pro','o3-mini','qwen-2.5','llama-4-maverick',
            'claude-sonnet-3.7','claude-opus-4.0','gpt-4o','qwq',
            'qwen38-27b-q4-k-m',
            'codex-qwen38-lite72-v2-selection-recovery'])
        self.assertEqual([g['id'] for g in leaderboard['display_order']['groups']],
                         [g[0] for g in GROUPS if g[0]!='lite-v1-t1'])
        self.assertEqual(leaderboard['display_order']['sort_by'],'correct_v')
        self.assertEqual([r['correct_v'] for r in rows],sorted([r['correct_v'] for r in rows],reverse=True))
        archived=leaderboard['archived_rows']
        self.assertEqual([r['id'] for r in archived],['claude-code-k3-lite72'])
        self.assertAlmostEqual(archived[0]['correct_v'],18.51851851851852)
        self.assertEqual(group_id(archived[0]),'lite-v1-t1')
        text=(ROOT/'docs/index.md').read_text()
        self.assertEqual(text,reorder_markdown(text,list(reversed(rows)),rows))
        self.assertEqual(group_id(rows[-1]),'historical-v2-recovery')

    def test_portrait_assets_and_compatibility_aliases(self):
        assets=ROOT/'docs/assets'
        png=(assets/'leaderboard-portrait.png').read_bytes()
        self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
        width,height=struct.unpack('>II',png[16:24])
        self.assertGreater(height,width)
        svg=ET.parse(assets/'leaderboard-portrait.svg').getroot()
        self.assertGreater(float(svg.attrib['height'].removesuffix('pt')),
                           float(svg.attrib['width'].removesuffix('pt')))
        for extension in ['svg','png']:
            self.assertEqual((assets/f'leaderboard-portrait.{extension}').read_bytes(),
                             (assets/f'leaderboard-full.{extension}').read_bytes())

    def test_sort_ties_and_missing_metrics(self):
        rows=[dict(id=id,source='published-reference',correct_v=value)
              for id,value in [('missing',None),('b',10),('a',10),('c',20)]]
        self.assertEqual([r['id'] for r in ordered_rows(rows)],['c','a','b','missing'])
        legacy=dict(id='claude-code-k3-lite72',source='independent-local',correct_v=99)
        self.assertEqual([r['id'] for r in ordered_rows(rows+[legacy])],['c','a','b','missing'])
        with self.assertRaises(ValueError):
            group_id(dict(id='unknown',source='independent-local'))

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

    def test_new_chart_rows_match_audits_and_judge_counts(self):
        leaderboard=json.loads((DATA/'leaderboard.json').read_text())
        self.assertEqual(len({r['id'] for r in leaderboard['rows']}),len(leaderboard['rows']))
        for row in leaderboard['rows']:
            if 'v2-selection' not in row['id']:continue
            audit=json.loads((ROOT/'docs'/row['audit']).read_text())
            for metric in leaderboard['metrics']:
                self.assertEqual(row[metric],audit['metrics'][metric])
            self.assertEqual(row['judge_status'],'validated')
            counts=Counter(outcome for r in audit['records'] for outcome in r['judge_outcomes'])
            self.assertEqual(sum(counts.values()),216)
            self.assertTrue(all(len(r['judge_outcomes'])==3 for r in audit['records']))
            self.assertEqual(dict(counts),audit['judge']['counts'])
            for category,metric in [('No Error','correct_v'),('Minor Error','minor'),
                                    ('Major Error','major'),('VisFail','vis_fail'),('Crash','crash')]:
                self.assertAlmostEqual(100*counts[category]/216,audit['metrics'][metric])
            self.assertAlmostEqual(audit['metrics']['crash'],100-audit['metrics']['visualization_no_error'])
            self.assertEqual(audit['judge']['valid_outcomes'],216)
            self.assertEqual(audit['judge']['codex_cli_version'],'0.153.4')
            self.assertFalse(audit['judge']['human_expert_review_included'])
        qwen=next(r for r in leaderboard['rows'] if r['id']=='qwen38-27b-q4-k-m')
        self.assertEqual(qwen['label'].splitlines()[1],'27B Q4_K_M')

    def test_sanitized_exports_and_local_links(self):
        for name in ['gpt6-v2-selection-audit.json','claude-k3-v2-selection-audit.json',
                     'codex-qwen38-v2-selection-recovery-audit.json','lite72-v2-candidate.json']:
            text=(DATA/name).read_text()
            for forbidden in ['/mnt/','/home/','Bearer ','Authorization','access_token','refresh_token']:
                self.assertNotIn(forbidden,text)
        for name in ['README.md','LITE72_RUN_GUIDE.md','docs/index.md','docs/lite72-v2-historical.md','docs/execution-fairness.md']:
            path=ROOT/name
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                if re.match(r'\w+://',target) or target.startswith('#'):continue
                target=target.split('#',1)[0]
                self.assertTrue((path.parent/target).exists(),f'{name}: {target}')

    def test_recovery_is_separate_and_missing_submissions_are_failures(self):
        audit=json.loads((DATA/'codex-qwen38-v2-selection-recovery-audit.json').read_text())
        self.assertFalse(audit['original_capped_run_result'])
        self.assertFalse(audit['official_frozen_input_v2_result'])
        manifest=json.loads((DATA/'lite72-v2-candidate.json').read_text())
        self.assertEqual({r['uid'] for r in audit['records']},{r['uid'] for r in manifest['tasks']})
        self.assertEqual(len(audit['records']),72)
        self.assertEqual(audit['recovery']['fresh_processing_attempts'],[51,52])
        self.assertEqual(audit['recovery']['successful_retry_used'],51)
        missing=[r for r in audit['records'] if r['missing_processing']]
        self.assertEqual({r['selection_task_1based'] for r in missing},{17,52})
        self.assertTrue(all(not r['processing_success'] and r['vi_score'] is None for r in missing))
        self.assertEqual(sum(r['processing_success'] for r in audit['records']),25)
        self.assertEqual(sum(r['visualization_success'] for r in audit['records']),39)
        vi=[r['vi_score'] for r in audit['records'] if r['processing_success'] and r['vi_score'] is not None]
        self.assertEqual(len(vi),19)
        self.assertAlmostEqual(mean(vi),audit['metrics']['vi_score'])

    def test_markdown_table_matches_leaderboard_data(self):
        text=(ROOT/'docs/index.md').read_text()
        leaderboard=json.loads((DATA/'leaderboard.json').read_text())
        for row in leaderboard['rows']:
            if 'v2-selection' not in row['id']:continue
            name=row['table_label'].split(' (',1)[0]
            line=next(line for line in text.splitlines() if line.startswith('| '+name) and 'historical inputs' in line)
            cells=[c.strip() for c in line.split('|')[1:-1]]
            for index,key in enumerate(['processing_no_error','vi_score','visualization_no_error','correct_v','vis_fail','minor','major'],2):
                decimals=4 if key=='vi_score' else 2
                suffix='' if key=='vi_score' else '%'
                self.assertEqual(cells[index],f'{row[key]:.{decimals}f}{suffix}')


if __name__=='__main__':unittest.main()
