import unittest,tempfile,sys,json,shutil
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pilot
SOURCE=pilot.ROOT
class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'project';self.root.mkdir()
  for p in ['scripts','prompts','tests']:shutil.copytree(SOURCE/p,self.root/p,ignore=shutil.ignore_patterns('__pycache__'))
  self.patch=patch.object(pilot,'ROOT',self.root);self.patch.start();self.run=pilot.prepare()
 def tearDown(self):self.patch.stop();self.tmp.cleanup()
 def fixture(self,cid='D02_conservar'):
  c=pilot.get_case(self.run,cid)
  o={'decision':'keep','diagnosis':['Suficiente.'],'questions':[],'assumptions':[],'recommended_prompt':c['prompt'],'changes':[],'research_status':'not_needed','sources':[],'validation':'static_review_only','limitations':['fixture']}
  p=self.root/'response.txt';pilot.dump(p,o);return p
 def record(self,v='candidate',origin='fixture',session='test'):
  return pilot.record(self.run,'D02_conservar',v,self.fixture(),origin,'Opus mostrado',session)
 def test_tampered_snapshot_rejected(self):
  (self.run/'candidate.md').write_text('changed')
  with self.assertRaises(ValueError):pilot.verify(self.run)
 def test_sessions_no_rubric_and_outside_project(self):
  with self.assertRaises(ValueError):pilot.sessions(self.run,self.root/'nested')
  dest=pilot.sessions(self.run,Path(self.tmp.name)/'sessions')
  c=pilot.get_case(self.run,'D02_conservar');p=dest/'D02_conservar--candidate'
  text='\n'.join(f.read_text() for f in p.rglob('*') if f.is_file())
  self.assertNotIn(c['rubric'],text);self.assertEqual((p/'CLAUDE.md').read_text(),(self.run/'candidate.md').read_text())
 def test_missing_responses_never_pass(self):
  r=pilot.report(self.run);self.assertEqual(r['selection'],'insufficient_evidence');self.assertFalse(r['variants']['candidate']['criteria_met'])
 def test_fixture_never_counts_as_real_pass(self):
  self.assertTrue(self.record()['pass']);pilot.review(self.run,'D02_conservar','candidate','pass','tester','Fixture only','human')
  r=pilot.report(self.run);row=next(x for x in r['rows'] if x['case']=='D02_conservar' and x['variant']=='candidate');self.assertEqual(row['status'],'fixture');self.assertEqual(r['variants']['candidate']['passed'],0)
 def test_model_review_is_not_human_approval(self):
  self.record(origin='claude_code_session');pilot.review(self.run,'D02_conservar','candidate','pass','Opus','Cumple','model')
  row=next(x for x in pilot.report(self.run)['rows'] if x['case']=='D02_conservar' and x['variant']=='candidate');self.assertEqual(row['status'],'pending_human_review')
 def test_tampered_response_invalidates_review(self):
  self.record();e=pilot.verify(self.run)['records']['D02_conservar--candidate'];(self.run/e['response']).write_text('modified')
  with self.assertRaises(ValueError):pilot.review(self.run,'D02_conservar','candidate','pass','human','ok','human')
 def test_same_session_cannot_compare_variants(self):
  self.record(origin='claude_code_session')
  with self.assertRaises(ValueError):self.record('baseline','claude_code_session')
 def test_wrong_contract_and_fabricated_validation_fail(self):
  c=pilot.get_case(self.run,'D02_conservar');s=pilot.load(self.run/'output.schema.json');o=pilot.load(self.fixture())
  o['validation']='tested_100_times';self.assertFalse(pilot.check(json.dumps(o),c,s)['pass'])
  self.assertFalse(pilot.check('not json',c,s)['pass'])
 def test_replay_has_no_model_provider_or_judge(self):
  self.record();cfg=pilot.load(pilot.replay_config(self.run));self.assertEqual(cfg['providers'],[{'id':'file://./saved-provider.cjs'}]);self.assertNotIn('provider',cfg['defaultTest']['options']);self.assertEqual({x['type'] for x in cfg['defaultTest']['assert']},{'is-json','javascript'})
if __name__=='__main__':unittest.main()
