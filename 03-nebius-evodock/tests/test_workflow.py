"""Local workflow tests with actual SQLite, API and FFmpeg. Never calls Nebius."""
import json,tempfile,time,unittest,zipfile,hashlib,threading,shutil
from pathlib import Path
from fastapi.testclient import TestClient
from evodock.app import create_app
from evodock.provider import Settings
from evodock.fixture import fixture
from evodock.models import Storyboard
from evodock.render import render
class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.app=create_app(self.tmp.name,Settings());self.c=TestClient(self.app);self.c.headers['X-EvoDock-Request']='local-ui'
    def wait(self,i):
        for _ in range(200):
            p=self.c.get('/api/projects/'+i).json()
            if p['jobs'] and p['jobs'][0]['status'] not in ('queued','running'):return p
            time.sleep(.05)
        self.fail('Job did not finish')
    def create(self):
        r=self.c.post('/api/projects',json={'brief':'A fictional garden postcard'});self.assertEqual(r.status_code,200,r.text)
        return self.wait(r.json()['project_id'])
    def test_persistent_edit_revise_restore(self):
        p=self.create();i=p['id'];b=p['storyboard'];b['scenes'][0]['title']='An edited beginning'
        r=self.c.put('/api/projects/'+i,json={'storyboard':b,'expected_revision':1});self.assertEqual(r.status_code,200)
        r=self.c.post('/api/projects/'+i+'/revise',json={'instruction':'Make it shorter','expected_revision':2});self.assertEqual(r.status_code,200)
        p=self.wait(i);self.assertEqual(p['revision'],3);self.assertEqual(p['storyboard']['scenes'][0]['seconds'],3);self.assertEqual(p['storyboard']['scenes'][0]['title'],'An edited beginning')
        c2=TestClient(create_app(self.tmp.name,Settings()));self.assertEqual(c2.get('/api/projects/'+i).json()['revision'],3)
        self.assertEqual(self.c.put('/api/projects/'+i,json={'storyboard':b,'expected_revision':1}).status_code,409)
    def test_cancel_no_silent_completion_then_retry(self):
        r=self.c.post('/api/projects',json={'brief':'A fictional space postcard'}).json();self.c.post('/api/jobs/'+r['job_id']+'/cancel',json={});p=self.wait(r['project_id']);self.assertEqual(p['jobs'][0]['status'],'cancelled');self.assertEqual(p['revision'],0)
        retry=self.c.post('/api/projects/'+p['id']+'/retry',json={'brief':p['brief'],'mode':'fixture'});self.assertEqual(retry.status_code,200);self.assertEqual(self.wait(p['id'])['revision'],1)
    def test_live_fail_closed_preserves_existing(self):
        p=self.create();r=self.c.post('/api/projects',json={'brief':'Synthetic live brief','mode':'live','model':'nvidia/fake','consent_to_transmit':True});self.assertEqual(r.status_code,503);self.assertEqual(self.c.get('/api/projects/'+p['id']).json()['revision'],1)
    def test_invalid_output_and_html_boundary(self):
        p=self.create();b=p['storyboard'];b['output_path']='../../evil';self.assertEqual(self.c.put('/api/projects/'+p['id'],json={'storyboard':b,'expected_revision':1}).status_code,422)
        self.assertEqual(self.c.get('/api/projects/not-valid').status_code,404);self.assertEqual(self.c.get('/api/projects/'+p['id']+'/files/1/secret.txt').status_code,404)
        page=self.c.get('/');self.assertIn("script-src 'self'",page.headers['content-security-policy'])
    def test_mutation_guard_and_origin(self):
        self.assertEqual(self.c.post('/api/projects',json={'brief':'Fiction'},headers={'X-EvoDock-Request':'bad'}).status_code,403)
        self.assertEqual(self.c.post('/api/projects',json={'brief':'Fiction'},headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.c.post('/api/projects',content='x'*25000).status_code,413)
        self.assertEqual(self.c.post('/api/projects',content='{}',headers={'Content-Length':'broken'}).status_code,400)
    def test_missing_ffmpeg_reported_upfront(self):
        from unittest.mock import patch
        with patch('evodock.app.shutil.which',return_value=None):
            status=self.c.get('/api/status').json()
            self.assertFalse(status['renderer_available']);self.assertIn('https://ffmpeg.org/download.html',status['renderer_note'])
        self.assertEqual(self.c.get('/api/status').json()['renderer_available'],bool(shutil.which('ffmpeg')))
    def test_duplicate_job_blocked(self):
        r=self.c.post('/api/projects',json={'brief':'A fictional opening'}).json()
        retry=self.c.post('/api/projects/'+r['project_id']+'/retry',json={'brief':'A fictional opening','mode':'fixture'});self.assertEqual(retry.status_code,409);self.wait(r['project_id'])
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg not installed')
    def test_real_render_manifest_and_idempotency(self):
        p=self.create();i=p['id'];url='/api/projects/'+i+'/render'
        self.assertEqual(self.c.post(url,json={'expected_revision':1}).status_code,422)
        self.assertEqual(self.c.post(url,json={'expected_revision':1,'confirmed':True}).status_code,200)
        p=self.wait(i);self.assertEqual(p['jobs'][0]['status'],'complete',p['jobs'][0]);folder=Path(self.tmp.name)/i/'r1'
        self.assertGreater((folder/'preview.mp4').stat().st_size,1000)
        with zipfile.ZipFile(folder/'project.zip') as z:
            manifest=json.loads(z.read('manifest.json'))
            for name,h in manifest['files'].items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),h)
            self.assertEqual(manifest['mode'],'fixture');self.assertIn('DEMO FIXTURE',z.read('README.txt').decode())
        r=self.c.post(url,json={'expected_revision':1,'confirmed':True});self.assertTrue(r.json()['cached'])
        response=self.c.get('/api/projects/'+i+'/files/1/preview.mp4',headers={'Range':'bytes=0-31'});self.assertEqual(response.status_code,206)
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg not installed')
    def test_cancelled_render_has_no_final_file(self):
        stop=threading.Event();stop.set();out=Path(self.tmp.name)/'render'
        with self.assertRaises(InterruptedError):render(fixture('Fictional art'),out,'fixture',stop)
        self.assertFalse((out/'preview.mp4').exists())
if __name__=='__main__':unittest.main()
