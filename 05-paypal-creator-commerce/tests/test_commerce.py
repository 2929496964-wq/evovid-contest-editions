"""Executable offline contract/security tests. These do not claim a live Sandbox test."""
import concurrent.futures, copy, json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from commerce.app import create_app, COOKIE
from commerce.config import Settings, ROOT, SANDBOX_API
from commerce.paypal import PayPalSandbox, FixturePayments, PaymentUnavailable
from commerce.planner import plan

ORIGIN='http://127.0.0.1:8715'
class CommerceCase(unittest.TestCase):
    def setUp(self):
        (ROOT/'test-output').mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'test-output')
        self.settings=Settings(data_dir=Path(self.tmp.name))
        self.app=create_app(self.settings);self.client=TestClient(self.app,base_url=ORIGIN)
        self.bootstrap(self.client)
    def tearDown(self):self.client.close();self.tmp.cleanup()
    def bootstrap(self,c):
        b=c.get('/api/bootstrap');self.assertEqual(b.status_code,200)
        c.headers.update({'Origin':ORIGIN,'X-CSRF-Token':b.json()['csrf']})
    def new(self,c=None):
        r=(c or self.client).post('/api/projects',json={'brief':'A fictional Northlight coffee brand launch.', 'planner':'fixture'})
        self.assertEqual(r.status_code,200,r.text);return r.json()
    def checkout(self,p,c=None):
        r=(c or self.client).post('/api/checkout/orders',json={'project_id':p['id'],'revision':p['current_revision'],'sku':'portrait-hd-export'})
        self.assertEqual(r.status_code,200,r.text);return r.json()
    def fixture(self,o,scenario='completed',c=None):
        return (c or self.client).post('/api/orders/'+o['id']+'/fixture',json={'scenario':scenario})
    def entitled(self,p):return self.client.get('/api/projects/'+p['id']).json()['entitled']

    def test_default_is_honestly_labeled_fixture(self):
        b=self.client.get('/api/bootstrap').json()
        self.assertEqual(b['payment_mode'],'fixture');self.assertIn('非PayPal真实支付',b['payment_label']);self.assertFalse(b['submission_ready'])
        p=self.new();self.assertFalse(p['provenance']['online_model_call'])

    def test_no_client_price_or_paid_flags(self):
        p=self.new()
        for extra in [{'amount':'0.01'},{'currency':'EUR'},{'paid':True},{'paypal_id':'FAKE'}]:
            r=self.client.post('/api/checkout/orders',json={'project_id':p['id'],'revision':1,**extra});self.assertEqual(r.status_code,422)
        o=self.checkout(p);self.assertEqual(o['amount'],'4.99');self.assertEqual(o['currency'],'USD')
        self.assertEqual(self.client.post('/api/projects/'+p['id']+'/exports',json={}).status_code,403)
        self.assertEqual(self.client.get('/api/media/'+p['id']+'/export?revision=1').status_code,403)
        self.client.get('/?checkout='+o['id']+'&result=return&paid=true')
        self.assertFalse(self.entitled(p))

    def test_cancel_does_not_unlock_and_same_order_resumes(self):
        p=self.new();o=self.checkout(p)
        self.assertEqual(self.client.post('/api/orders/'+o['id']+'/cancel',json={}).json()['status'],'CANCELED')
        self.assertFalse(self.entitled(p));self.assertEqual(self.checkout(p)['id'],o['id'])
        self.fixture(o);self.assertTrue(self.entitled(p))

    def test_pending_declined_and_mismatches_never_unlock(self):
        for scenario in ['pending','declined','wrong-amount','wrong-currency','wrong-merchant','wrong-order','wrong-reference']:
            with self.subTest(scenario=scenario):
                p=self.new();o=self.checkout(p);r=self.fixture(o,scenario)
                self.assertEqual(r.status_code,200,r.text);self.assertFalse(self.entitled(p))
                self.assertIn(r.json()['status'],['PENDING','DECLINED','REJECTED'])
                self.assertEqual(self.client.post('/api/projects/'+p['id']+'/exports',json={}).status_code,403)

    def test_response_loss_refresh_recovers_same_order(self):
        p=self.new();o=self.checkout(p)
        self.assertEqual(self.fixture(o,'lost-response').json()['status'],'VERIFYING');self.assertFalse(self.entitled(p))
        self.assertEqual(self.client.post('/api/orders/'+o['id']+'/cancel',json={}).status_code,409)
        r=self.client.post('/api/orders/'+o['id']+'/reconcile',json={});self.assertEqual(r.json()['status'],'COMPLETED');self.assertTrue(self.entitled(p))
        self.assertEqual(self.checkout(p)['id'],o['id'])

    def test_duplicate_and_concurrent_clicks_unique_ledger(self):
        p=self.new()
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            orders=list(pool.map(lambda _:self.checkout(p),range(8)))
        self.assertEqual(len({x['id'] for x in orders}),1);o=orders[0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda _:self.fixture(o),range(8)))
        self.assertTrue(all(x.status_code==200 for x in results))
        with self.app.state.store.connection() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM captures').fetchone()[0],1)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM entitlements').fetchone()[0],1)

    def test_cross_session_and_cross_project_rights(self):
        p=self.new();o=self.checkout(p);self.fixture(o);p2=self.new()
        self.assertEqual(self.client.post('/api/projects/'+p2['id']+'/exports',json={}).status_code,403)
        stranger=TestClient(self.app,base_url=ORIGIN);self.bootstrap(stranger)
        for path,method,body in [('/api/projects/'+p['id'],'GET',None),('/api/projects/'+p['id']+'/source','GET',None),('/api/projects/'+p['id']+'/evidence','GET',None),('/api/orders/'+o['id']+'/fixture','POST',{'scenario':'completed'}),('/api/orders/'+o['id']+'/reconcile','POST',{}),('/api/projects/'+p['id']+'/exports','POST',{}),('/api/checkout/orders','POST',{'project_id':p['id'],'revision':1})]:
            r=stranger.request(method,path,json=body) if body is not None else stranger.get(path)
            self.assertEqual(r.status_code,404,path)
        stranger.close()

    def test_restart_preserves_project_and_entitlement(self):
        p=self.new();o=self.checkout(p);self.fixture(o);token=self.client.cookies.get(COOKIE)
        restarted=TestClient(create_app(self.settings),base_url=ORIGIN);restarted.cookies.set(COOKIE,token)
        self.bootstrap(restarted);r=restarted.get('/api/projects/'+p['id']).json()
        self.assertTrue(r['entitled']);self.assertEqual(r['order']['id'],o['id']);restarted.close()

    def test_fixture_entitlement_does_not_unlock_sandbox(self):
        p=self.new();o=self.checkout(p);self.fixture(o)
        config=Settings(data_dir=Path(self.tmp.name),payment_mode='sandbox',paypal_client_id='TEST-ID',paypal_secret='TEST-SECRET',paypal_merchant_id='TEST-MERCHANT')
        sandbox=TestClient(create_app(config),base_url=ORIGIN);sandbox.cookies.set(COOKIE,self.client.cookies.get(COOKIE));self.bootstrap(sandbox)
        self.assertFalse(sandbox.get('/api/projects/'+p['id']).json()['entitled'])
        self.assertEqual(sandbox.post('/api/projects/'+p['id']+'/exports',json={}).status_code,403)
        self.assertEqual(sandbox.post('/api/orders/'+o['id']+'/fixture',json={'scenario':'completed'}).status_code,404)
        self.assertEqual(sandbox.get('/api/orders/'+o['id']).status_code,404);sandbox.close()

    def test_revision_binding_and_stale_write(self):
        p=self.new();o=self.checkout(p)
        update={'expected_revision':1,'board':p['board']}
        self.assertEqual(self.client.put('/api/projects/'+p['id'],json=update).status_code,409)
        self.fixture(o);update['board']['scenes'][0]['title']='A new creative direction'
        r=self.client.put('/api/projects/'+p['id'],json=update);self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['current_revision'],2);self.assertFalse(r.json()['entitled'])
        self.assertEqual(self.client.put('/api/projects/'+p['id'],json=update).status_code,409)
        self.assertEqual(self.client.post('/api/checkout/orders',json={'project_id':p['id'],'revision':1}).status_code,409)

    def test_csrf_host_limits_and_path_protection(self):
        self.assertEqual(self.client.post('/api/projects',json={'brief':'Fictional test brief'},headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/projects',json={'brief':'Fictional test brief'},headers={'X-CSRF-Token':'wrong'}).status_code,403)
        self.assertEqual(self.client.get('/',headers={'Host':'evil.example'}).status_code,400)
        self.assertEqual(self.client.post('/api/projects',json={'brief':'x'*40000}).status_code,413)
        self.assertEqual(self.client.post('/api/projects',json={'brief':'x'*1201}).status_code,422)
        self.assertIn(self.client.get('/static/../commerce/config.py').status_code,[404,400])
        self.assertEqual(self.client.get('/data/commerce.sqlite3').status_code,404)

    def test_import_validates_schema_and_never_imports_rights(self):
        p=self.new();o=self.checkout(p);self.fixture(o)
        exported=self.client.get('/api/projects/'+p['id']+'/source').json()
        r=self.client.post('/api/projects/import',json=exported);self.assertEqual(r.status_code,200);self.assertFalse(r.json()['entitled'])
        exported['paid']=True;self.assertEqual(self.client.post('/api/projects/import',json=exported).status_code,422)
        exported.pop('paid');exported['board']['scenes'][0]['seconds']=999
        self.assertEqual(self.client.post('/api/projects/import',json=exported).status_code,422)

    def test_failed_export_keeps_entitlement(self):
        p=self.new();o=self.checkout(p);self.fixture(o)
        with patch('commerce.app.render',side_effect=RuntimeError('synthetic encoding failure')):
            self.assertEqual(self.client.post('/api/projects/'+p['id']+'/exports',json={}).status_code,503)
        self.assertTrue(self.entitled(p));self.assertEqual(self.checkout(p)['id'],o['id'])

    def test_real_mp4_preview_and_export(self):
        p=self.new();o=self.checkout(p)
        pre=self.client.post('/api/projects/'+p['id']+'/preview',json={});self.assertEqual(pre.status_code,200,pre.text)
        self.assertGreater(len(self.client.get(pre.json()['url']).content),10000)
        self.fixture(o);out=self.client.post('/api/projects/'+p['id']+'/exports',json={});self.assertEqual(out.status_code,200,out.text)
        video=self.client.get(out.json()['url']);self.assertEqual(video.status_code,200);self.assertIn(b'ftyp',video.content[:32]);self.assertGreater(len(video.content),10000)
        if shutil.which('ffprobe'):
            path=next((Path(self.tmp.name)/'exports').glob('*.mp4'))
            info=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-print_format','json','-show_streams',str(path)]))['streams'][0]
            self.assertEqual((info['width'],info['height']),(720,1280));self.assertEqual(info['codec_name'],'h264')

class SandboxLifecycleTests(CommerceCase):
    def setUp(self):
        super().setUp()
        self.settings=Settings(data_dir=Path(self.tmp.name),payment_mode='sandbox',paypal_client_id='TEST-ID',paypal_secret='TEST-SECRET',paypal_merchant_id='TEST-MERCHANT')
        class FakeSandbox:
            mode='sandbox'
            def __init__(self):self.remote={};self.capture_calls=0;self.lose_response=False
            def close(self):pass
            def create(self,o):
                response=FixturePayments.response({**o,'paypal_id':'SANDBOX-MOCK-'+o['id']},'completed')
                response['status']='APPROVED';response['purchase_units'][0].pop('payments')
                self.remote[o['id']]=response
                return response['id'],'https://www.sandbox.paypal.com/checkoutnow?token='+response['id']
            def get(self,o):return copy.deepcopy(self.remote[o['id']])
            def capture(self,o):
                self.capture_calls+=1
                self.remote[o['id']]=FixturePayments.response(o,'completed')
                if self.lose_response:raise PaymentUnavailable('Synthetic capture response lost.')
                return self.remote[o['id']]
        self.fake=FakeSandbox();self.app=create_app(self.settings,self.fake)
        self.client.close();self.client=TestClient(self.app,base_url=ORIGIN);self.bootstrap(self.client)

    def test_existing_pending_capture_is_never_recaptured(self):
        p=self.new();o=self.checkout(p);self.fake.remote[o['id']]=FixturePayments.response({**o,'merchant':'TEST-MERCHANT'},'pending')
        for _ in range(3):
            r=self.client.post('/api/orders/'+o['id']+'/capture',json={});self.assertEqual(r.json()['status'],'PENDING')
        self.assertEqual(self.fake.capture_calls,0);self.assertFalse(self.entitled(p))

    def test_approved_alone_never_unlocks(self):
        p=self.new();o=self.checkout(p)
        r=self.client.post('/api/orders/'+o['id']+'/reconcile',json={})
        self.assertEqual(r.json()['status'],'APPROVED');self.assertFalse(self.entitled(p));self.assertEqual(self.fake.capture_calls,0)

    def test_mismatch_is_rejected_before_capture(self):
        p=self.new();o=self.checkout(p)
        self.fake.remote[o['id']]['purchase_units'][0]['amount']['value']='0.01'
        r=self.client.post('/api/orders/'+o['id']+'/capture',json={})
        self.assertEqual(r.json()['status'],'REJECTED');self.assertEqual(self.fake.capture_calls,0);self.assertFalse(self.entitled(p))

    def test_sandbox_response_loss_reconciles_without_double_capture(self):
        p=self.new();o=self.checkout(p);self.fake.lose_response=True
        r=self.client.post('/api/orders/'+o['id']+'/capture',json={});self.assertEqual(r.json()['status'],'VERIFYING')
        self.assertFalse(self.entitled(p));self.assertEqual(self.fake.capture_calls,1)
        r=self.client.post('/api/orders/'+o['id']+'/capture',json={});self.assertEqual(r.json()['status'],'COMPLETED')
        self.assertTrue(self.entitled(p));self.assertEqual(self.fake.capture_calls,1)

    def test_concurrent_sandbox_capture_is_single(self):
        p=self.new();o=self.checkout(p)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results=list(pool.map(lambda _:self.client.post('/api/orders/'+o['id']+'/capture',json={}),range(6)))
        self.assertTrue(all(r.json()['status']=='COMPLETED' for r in results));self.assertEqual(self.fake.capture_calls,1)

# Do not inherit the fixture-mode cases into the Sandbox-specific suite.
for name in list(CommerceCase.__dict__):
    if name.startswith('test_') and name not in SandboxLifecycleTests.__dict__:
        setattr(SandboxLifecycleTests,name,None)

class AdapterTests(unittest.TestCase):
    def test_local_ai_real_http_contract_no_silent_fallback(self):
        settings=Settings(ai_model='local-test-model')
        sample={'title':'Changed by the model','scenes':[{'title':'From a real response','caption':'One','seconds':2,'accent':'cyan'},{'title':'A second model shot','caption':'Two','seconds':2,'accent':'lime'}]}
        requests=[]
        def route(request):
            requests.append(request);return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(sample)}}]})
        client=httpx.Client(transport=httpx.MockTransport(route))
        board,proof=plan('An original fictional launch story','local-ai',settings,client)
        self.assertEqual(board.title,'Changed by the model');self.assertTrue(proof['online_model_call']);self.assertEqual(requests[0].url.path,'/v1/chat/completions')
        bad=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(500)))
        with self.assertRaises(ValueError):plan('Test prompt','local-ai',settings,bad)
        malformed=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[{'message':{'content':'{"title":"Wrong","scenes":[]}'}}]})))
        with self.assertRaises(ValueError):plan('Test prompt','local-ai',settings,malformed)

    def test_production_and_remote_ai_are_forbidden(self):
        for mode in ['live','production','paypal']:
            with self.assertRaises(ValueError):Settings(payment_mode=mode)
        with self.assertRaises(ValueError):Settings(payment_mode='sandbox')
        with self.assertRaises(ValueError):Settings(ai_url='https://remote-provider.example/v1')
        with patch.dict(os.environ,{'PAYPAL_BASE_URL':'https://api-m.paypal.com'}):
            with self.assertRaises(ValueError):Settings()

    def test_paypal_adapter_sandbox_only_keys_and_merchant(self):
        settings=Settings(payment_mode='sandbox',paypal_client_id='test-id',paypal_secret='test-secret',paypal_merchant_id='TEST-MERCHANT')
        calls=[]
        def route(r):
            calls.append(r)
            if r.url.path=='/v1/oauth2/token':return httpx.Response(200,json={'access_token':'TEST-TOKEN','expires_in':1000})
            if r.url.path=='/v2/checkout/orders':return httpx.Response(201,json={'id':'TEST-ORDER','links':[{'rel':'payer-action','href':'https://www.sandbox.paypal.com/checkoutnow?token=TEST-ORDER'}]})
            return httpx.Response(200,json={'id':'TEST-ORDER','status':'COMPLETED'})
        adapter=PayPalSandbox(settings,httpx.Client(transport=httpx.MockTransport(route)))
        order={'id':'a'*32,'merchant':'TEST-MERCHANT','amount':'4.99','currency':'USD','create_key':'create-uuid','capture_key':'capture-uuid','paypal_id':'TEST-ORDER'}
        self.assertEqual(adapter.create(order)[0],'TEST-ORDER');adapter.get(order);adapter.capture(order)
        self.assertTrue(all(str(r.url).startswith(SANDBOX_API+'/') for r in calls))
        payload=json.loads(calls[1].content);self.assertEqual(payload['purchase_units'][0]['amount']['value'],'4.99')
        self.assertEqual(payload['purchase_units'][0]['payee']['merchant_id'],'TEST-MERCHANT')
        self.assertEqual(calls[1].headers['PayPal-Request-Id'],'create-uuid');self.assertEqual(calls[-1].headers['PayPal-Request-Id'],'capture-uuid')
        self.assertNotIn('test-secret',calls[1].content.decode())

    def test_paypal_adapter_refuses_live_approval_url(self):
        settings=Settings(payment_mode='sandbox',paypal_client_id='test-id',paypal_secret='test-secret',paypal_merchant_id='TEST-MERCHANT')
        def route(r):
            return httpx.Response(200,json={'access_token':'TEST','expires_in':1000}) if r.url.path.endswith('/token') else httpx.Response(201,json={'id':'TEST','links':[{'rel':'approve','href':'https://www.paypal.com/checkoutnow?token=TEST'}]})
        adapter=PayPalSandbox(settings,httpx.Client(transport=httpx.MockTransport(route)))
        with self.assertRaises(PaymentUnavailable):adapter.create({'id':'a'*32,'merchant':'TEST','amount':'4.99','currency':'USD','create_key':'create-key'})

if __name__=='__main__':unittest.main(verbosity=2)
