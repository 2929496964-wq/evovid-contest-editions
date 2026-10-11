import json, tempfile, threading, time, unittest
from pathlib import Path
from uuid import UUID
import httpx
from fastapi.testclient import TestClient
from taste.qloo import Qloo, ProviderError
from taste.server import create_app
from taste.store import Store
from taste.models import Search

EID = 'f0d354aa-ba7e-49d2-8aba-9a8250f5c852'
def entity(name='Public film'):
    return {'entity_id': EID, 'name': name, 'subtype': 'urn:entity:movie', 'properties': {'release_year': 2022}, 'query': {'affinity': 0.0}}
class ProviderContracts(unittest.TestCase):
    def test_real_adapter_request_contract_without_live_network(self):
        seen, trace = [], []
        def handler(request):
            seen.append(request)
            self.assertEqual(request.url.host, 'hackathon.api.qloo.com')
            self.assertEqual(request.headers['X-Api-Key'], 'SYNTHETIC_TEST_KEY')
            self.assertEqual(request.headers['Accept'], 'application/json')
            if request.url.path == '/search': return httpx.Response(200, json={'results': [entity()]})
            if request.url.params['filter.type'] == 'urn:tag':
                return httpx.Response(200, json={'success': True, 'results': {'tags': [{'tag_id':'urn:tag:keyword:media:memory', 'name':'Memory'}]}})
            return httpx.Response(200, json={'success': True, 'results': {'entities': [entity()]}, 'query': {'explainability': {'warning': 'not available'}}})
        q = Qloo('SYNTHETIC_TEST_KEY', httpx.MockTransport(handler))
        self.assertEqual(q.search('Public film', 'movie', 'live', trace.append)[0]['id'], EID)
        result = q.insights([EID], 'live', trace.append)
        self.assertEqual(result['entities'][0]['affinity'], 0.0)
        self.assertEqual(result['source'], 'contract_mock')
        self.assertIn('explainability', ' '.join(result['warnings']))
        self.assertEqual(dict(seen[0].url.params), {'query':'Public film','types':'urn:entity:movie','take':'5'})
        self.assertEqual(dict(seen[1].url.params), {'signal.interests.entities':EID,'take':'5','filter.type':'urn:entity:movie','feature.explainability':'true'})
        self.assertEqual(seen[2].url.params['filter.tag.types'], 'urn:tag:keyword:media')
        self.assertEqual(seen[2].url.params['filter.parents.types'], 'urn:entity:movie,urn:entity:tv_show')
        self.assertNotIn('SYNTHETIC_TEST_KEY', json.dumps(trace))
        self.assertFalse(any(t.get('actual_http_call') for t in trace))
    def test_missing_key_never_calls_transport(self):
        q = Qloo('', httpx.MockTransport(lambda r: self.fail('network must not be reached')))
        with self.assertRaises(ProviderError) as caught: q.search('Moonlight', 'movie', 'live')
        self.assertEqual(caught.exception.code, 'missing_key')
    def test_auth_rate_failure_no_retry_or_fallback(self):
        for status,code in [(401,'authentication'),(403,'authentication'),(429,'rate_limited'),(500,'upstream'),(302,'upstream')]:
            calls=[]
            q=Qloo('SYNTHETIC_TEST_KEY',httpx.MockTransport(lambda r:(calls.append(r) or httpx.Response(status,text='SYNTHETIC_TEST_KEY'))))
            with self.assertRaises(ProviderError) as caught:q.search('Moonlight','movie','live')
            self.assertEqual(caught.exception.code,code)
            self.assertEqual(len(calls),1)
            self.assertNotIn('SYNTHETIC_TEST_KEY',str(caught.exception))
    def test_timeout_and_bad_schema(self):
        def timeout(r): raise httpx.ReadTimeout('SYNTHETIC_TEST_KEY',request=r)
        for handler, code in [(timeout,'timeout'),(lambda r:httpx.Response(200,json={'wrong':'data'}),'schema'),(lambda r:httpx.Response(200,text='not json'),'schema')]:
            with self.assertRaises(ProviderError) as caught:Qloo('SYNTHETIC_TEST_KEY',httpx.MockTransport(handler)).search('Moonlight','movie','live')
            self.assertEqual(caught.exception.code,code)
            self.assertNotIn('SYNTHETIC_TEST_KEY',str(caught.exception))
    def test_empty_search_does_not_fabricate_entity(self):
        for status in (200,404):
            q=Qloo('SYNTHETIC_TEST_KEY',httpx.MockTransport(lambda r:httpx.Response(status,json={'results':[]})))
            self.assertEqual(q.search('Unfound','movie','live'),[])
    def test_demo_feedback_is_input_dependent(self):
        q=Qloo()
        first=q.insights([str(UUID(int=1))],'demo')
        second=q.insights([str(UUID(int=4))],'demo')
        self.assertNotEqual(first['tags'],second['tags'])
        self.assertTrue(all(x['affinity'] is None for x in first['entities']))
    def test_public_input_gate(self):
        for query in ['person@example.com','https://private.example', '555 123 1234', '<script>']:
            with self.assertRaises(ValueError):Search(query=query,public_reference=True)

class AppFlow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent.parent/'evidence')
        self.app=create_app(self.tmp.name,provider=Qloo())
        self.client=TestClient(self.app,base_url='http://127.0.0.1')
        self.client.__enter__()
        self.headers={'X-Taste-Client':'1'}
        self.client.get('/api/state')
    def tearDown(self):
        self.client.__exit__(None,None,None)
        self.tmp.cleanup()
    def post(self,path,data):return self.client.post(path,json=data,headers=self.headers)
    def reference(self,title):
        r=self.post('/api/search',{'query':title,'category':'movie','mode':'demo','public_reference':True})
        self.assertEqual(r.status_code,200,r.text)
        return r.json()['candidates'][0]['id']
    def plan(self,title='Spirited Away',rid='request001',parent=None):
        eid=self.reference(title)
        data={'entity_ids':[eid],'mode':'demo','goal':'An original ordinary day','duration':12,'aspect':'16:9','pace':'balanced','budget':'phone-only','request_id':rid,'parent_id':parent}
        r=self.post('/api/plans',data)
        self.assertEqual(r.status_code,202,r.text)
        i=r.json()['id']
        return self.wait(i),data
    def wait(self,i):
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            result=self.client.get('/api/jobs/'+i).json()
            if result['status'] not in ('queued','running'):return result
            time.sleep(.03)
        self.fail('Job did not terminate.')
    def test_plan_edit_replan_export_and_idempotence(self):
        job,data=self.plan()
        self.assertEqual(job['status'],'complete',job)
        doc=job['result'];self.assertEqual(len(doc['briefs']),3);self.assertEqual(len(doc['scenes']),4)
        duplicate=self.post('/api/plans',data);self.assertTrue(duplicate.json()['deduplicated']);self.assertEqual(duplicate.json()['id'],job['id'])
        data['goal']='Different input'
        conflict=self.post('/api/plans',data);self.assertEqual(conflict.status_code,409)
        edit={k:doc[k] for k in ('version','brief_index','title','scenes')};edit['title']='Edited original film'
        saved=self.client.patch('/api/projects/'+job['id'],json=edit,headers=self.headers)
        self.assertEqual(saved.status_code,200);self.assertEqual(saved.json()['version'],2)
        stale=self.client.patch('/api/projects/'+job['id'],json=edit,headers=self.headers);self.assertEqual(stale.status_code,409)
        for fmt in ('json','md'):
            exported=self.client.get('/api/projects/'+job['id']+'/export/'+fmt)
            self.assertEqual(exported.status_code,200);self.assertIn('Edited original film',exported.text)
        newer,_=self.plan('Interstellar','request002',job['id']);self.assertEqual(newer['status'],'complete')
        self.assertTrue(newer['result']['comparison']['reference_changed'])
        self.assertNotEqual(newer['result']['evidence']['tags'],doc['evidence']['tags'])
    def test_missing_live_key_returns_closed_error(self):
        r=self.post('/api/search',{'query':'Moonlight','category':'movie','mode':'live','public_reference':True})
        self.assertEqual(r.status_code,503);self.assertFalse(r.json()['fixture_fallback'])
    def test_no_fabricated_candidate_and_no_extra_profile_fields(self):
        r=self.post('/api/plans',{'entity_ids':[str(UUID(int=999))],'request_id':'request111'})
        self.assertEqual(r.status_code,422)
        r=self.post('/api/search',{'query':'Moonlight','category':'movie','mode':'demo','public_reference':True,'email':'private@example.org'})
        self.assertEqual(r.status_code,422)
    def test_origin_body_and_host_boundaries(self):
        self.assertEqual(self.client.post('/api/search',json={}).status_code,403)
        self.assertEqual(self.client.post('/api/search',json={},headers={**self.headers,'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/search',content='x'*70000,headers=self.headers).status_code,413)
        self.assertEqual(self.client.get('/api/state',headers={'Host':'evil.example'}).status_code,400)
        self.assertEqual(self.client.get('/api/exports/not-a-uuid.mp4').status_code,404)
    def test_sessions_cannot_read_other_projects(self):
        job,_=self.plan()
        with TestClient(self.app,base_url='http://127.0.0.1') as stranger:
            self.assertEqual(stranger.get('/api/jobs/'+job['id']).status_code,404)
            self.assertEqual(stranger.get('/api/projects/'+job['id']+'/export/json').status_code,404)
    def test_output_contains_no_server_secret(self):
        self.app.state.provider.key='DO_NOT_LEAK_TEST_SENTINEL'
        job,_=self.plan()
        for path in ['/api/state','/api/jobs/'+job['id'],'/api/projects/'+job['id']+'/export/json','/static/app.js']:
            self.assertNotIn('DO_NOT_LEAK_TEST_SENTINEL',self.client.get(path).text)
    def test_real_motion_render(self):
        job,_=self.plan()
        response=self.post('/api/projects/'+job['id']+'/render',{'version':1,'request_id':'render001'})
        self.assertEqual(response.status_code,202,response.text)
        output=self.wait(response.json()['id'])
        self.assertEqual(output['status'],'complete',output)
        video=self.client.get(output['result']['url'])
        self.assertGreater(len(video.content),10000)
        self.assertIn(b'ftyp',video.content[:32])
        self.assertEqual(output['result']['seconds'],12)
    def test_actual_render_cancellation_removes_partial_file(self):
        from taste.render import render
        job,_=self.plan()
        target=Path(self.tmp.name)/'cancelled-video.mp4'
        calls=[0]
        def stop():
            calls[0]+=1
            return calls[0]>8
        with self.assertRaises(InterruptedError):render(job['result'],target,stop=stop)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_suffix('.partial.mp4').exists())

    def test_cancel_plan_and_explicit_retry(self):
        provider = self.app.state.provider
        original = provider.insights
        started = threading.Event()
        def delayed(ids, mode, emit, stop):
            started.set()
            deadline = time.monotonic()+5
            while not stop() and time.monotonic()<deadline: time.sleep(.01)
            if stop(): raise InterruptedError('Cancelled')
            return original(ids, mode, emit, stop)
        provider.insights = delayed
        eid=self.reference('Spirited Away')
        payload={'entity_ids':[eid], 'request_id':'cancel-plan-001'}
        response=self.post('/api/plans',payload)
        self.assertEqual(response.status_code,202)
        self.assertTrue(started.wait(2))
        i=response.json()['id']
        self.assertEqual(self.post('/api/jobs/'+i+'/cancel',{}).status_code,200)
        self.assertEqual(self.wait(i)['status'],'cancelled')
        self.assertIsNone(self.client.get('/api/jobs/'+i).json()['result'])
        provider.insights=original
        payload['request_id']='cancel-retry-002'
        retry=self.post('/api/plans',payload)
        self.assertEqual(self.wait(retry.json()['id'])['status'],'complete')

    def test_mode_isolation_blocks_demo_ids_in_live(self):
        eid=self.reference('Spirited Away')
        self.app.state.provider.key='SYNTHETIC_TEST_KEY'
        r=self.post('/api/plans',{'entity_ids':[eid], 'mode':'live','request_id':'mode-isolation-01'})
        self.assertEqual(r.status_code,422)
        self.assertIn('Search and explicitly choose',r.text)

    def test_restart_marks_incomplete_as_interrupted(self):
        store=self.app.state.store
        owner=store.session(None)
        i,_=store.create(owner,'plan',{'request_id':'recovery01'})
        store.update(i,'running')
        reopened=Store(self.tmp.name)
        self.assertEqual(reopened.get(i)['status'],'interrupted')

if __name__=='__main__':unittest.main(verbosity=2)
