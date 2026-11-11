import unittest, sys, io, json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app
class AppTests(unittest.TestCase):
 def setUp(self): self.c=app.test_client()
 def test_home(self): self.assertEqual(self.c.get('/').status_code,200)
 def test_bad_upload(self): self.assertEqual(self.c.post('/api/scan',data={'image':(io.BytesIO(b'png'),'x.png')}).status_code,400)
 def test_origin(self): self.assertEqual(self.c.post('/api/scan',headers={'Origin':'https://evil.invalid'}).status_code,403)
 def fake(self,severity=None,targets=True):
  def run(args,**kwargs):
   report={'Results':[{'Target':'app.jar','Type':'jar','Vulnerabilities':([{'VulnerabilityID':'TEST-ID','Severity':severity}] if severity else [])}] if targets else []}
   Path(args[args.index('--output')+1]).write_text(json.dumps(report))
   return SimpleNamespace(returncode=0,stderr='')
  return run
 def test_verdicts(self):
  for severity,targets,want in [('CRITICAL',True,'FAIL'),('HIGH',True,'PASS'),('MEDIUM',True,'PASS'),(None,True,'PASS'),(None,False,'INCONCLUSIVE')]:
   with patch('app.subprocess.run',side_effect=self.fake(severity,targets)):
    r=self.c.post('/api/scan',data={'image':(io.BytesIO(b'mocked archive'),'sample.tar')})
    self.assertEqual(r.status_code,200);self.assertEqual(r.json['verdict'],want)
 def test_scanner_error(self):
  with patch('app.subprocess.run',return_value=SimpleNamespace(returncode=1,stderr='invalid archive')):
   r=self.c.post('/api/scan',data={'image':(io.BytesIO(b'bad'),'bad.tar')})
   self.assertEqual(r.status_code,422);self.assertNotIn('verdict',r.json)
if __name__=='__main__': unittest.main()
