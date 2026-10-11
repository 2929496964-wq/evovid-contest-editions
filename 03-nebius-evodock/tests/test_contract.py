"""OFFLINE HTTP CONTRACT TESTS. MockTransport uses the real production HTTP client.
These are synthetic contract tests, NOT live Nebius evidence.
"""
import json, tempfile, threading, unittest
from pathlib import Path
import httpx
from evodock.fixture import fixture
from evodock.models import Storyboard
from evodock.provider import Nebius, Settings, ProviderError
from evodock.store import Store,verify_traces
MODEL='nvidia/synthetic-contract-model'
SECRET='sk-synthetic-contract-secret-never-real'

def good(board=None):
    return {'id':'synthetic-response','model':MODEL,'choices':[{'finish_reason':'stop','message':{'content':json.dumps(board or fixture('A fictional bottle').model_dump())}}],'usage':{'prompt_tokens':90,'completion_tokens':110,'total_tokens':200}}
class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.i=self.store.create('A fictional bottle','live');self.calls=[]
    def client(self,handler,**overrides):
        def route(r):
            self.calls.append(r)
            if r.url.path.endswith('/models'):return httpx.Response(200,json={'data':[{'id':MODEL},{'id':'other/ignored'}]})
            return handler(r)
        cfg=Settings(key=SECRET,authorized=True,**overrides)
        return Nebius(cfg,self.store,httpx.MockTransport(route))
    def plan(self,client,stop=None):return client.plan(self.i,'A fictional bottle',MODEL,stop or threading.Event())
    def test_success_exact_discovery_and_token_guard(self):
        b=self.plan(self.client(lambda r:httpx.Response(200,json=good())))
        self.assertEqual(len(b.scenes),3);self.assertEqual(len(self.calls),2)
        req=self.calls[-1];self.assertEqual(req.headers['authorization'],'Bearer '+SECRET)
        payload=json.loads(req.content);self.assertEqual(payload['max_tokens'],1600);self.assertNotIn('tools',payload)
        traces=self.store.traces(self.i);self.assertEqual(traces[-1]['detail']['status'],'validated_success');self.assertTrue(verify_traces(traces))
        self.assertNotIn(SECRET,json.dumps(traces));self.assertEqual(self.store.budget()['attempts'],1)
    def test_model_must_be_discovered_nvidia(self):
        p=self.client(lambda r:httpx.Response(200,json=good()))
        with self.assertRaisesRegex(ProviderError,'discovered'):p.plan(self.i,'Fiction','nvidia/guessed',threading.Event())
        self.assertEqual(len(self.calls),1)
    def test_missing_key_fail_closed(self):
        p=Nebius(Settings(authorized=True),self.store,httpx.MockTransport(lambda r:self.fail('No call permitted')))
        with self.assertRaisesRegex(ProviderError,'missing'):self.plan(p)
    def test_unauthorized_fail_closed(self):
        p=Nebius(Settings(key=SECRET),self.store,httpx.MockTransport(lambda r:self.fail('No call permitted')))
        with self.assertRaisesRegex(ProviderError,'locked'):self.plan(p)
    def test_non_nebius_endpoint_rejected(self):
        p=Nebius(Settings(key=SECRET,authorized=True,endpoint='https://example.com/v1'),self.store)
        with self.assertRaisesRegex(ProviderError,'Endpoint'):self.plan(p)
    def test_timeout_not_retried(self):
        def handler(r):raise httpx.ReadTimeout(SECRET,request=r)
        with self.assertRaisesRegex(ProviderError,'timed out') as e:self.plan(self.client(handler))
        self.assertNotIn(SECRET,str(e.exception));self.assertEqual(len(self.calls),2)
        self.assertEqual(self.store.traces(self.i)[0]['detail']['status'],'timeout_uncertain')
    def test_auth_errors_never_echo_upstream(self):
        for status in [401,403,500,502]:
            with self.subTest(status=status):
                with self.assertRaises(ProviderError) as e:self.plan(self.client(lambda r:httpx.Response(status,text=SECRET)))
                self.assertNotIn(SECRET,str(e.exception))
    def test_429_bounded_retry(self):
        with self.assertRaisesRegex(ProviderError,'429'):self.plan(self.client(lambda r:httpx.Response(429,headers={'retry-after':'0'},json={'error':SECRET})))
        self.assertEqual(len(self.calls),3);self.assertEqual(self.store.budget()['attempts'],2)
    def test_429_then_success(self):
        count=0
        def handler(r):
            nonlocal count
            count+=1
            return httpx.Response(429,headers={'retry-after':'0'}) if count==1 else httpx.Response(200,json=good())
        self.plan(self.client(handler));self.assertEqual(count,2)
    def test_429_cancel_backoff(self):
        stop=threading.Event()
        def handler(r):stop.set();return httpx.Response(429,headers={'retry-after':'1'})
        with self.assertRaises(InterruptedError):self.plan(self.client(handler),stop)
        self.assertEqual(len(self.calls),2)
    def test_cancel_after_response_retains_usage(self):
        stop=threading.Event()
        def handler(r):stop.set();return httpx.Response(200,json=good())
        with self.assertRaises(InterruptedError):self.plan(self.client(handler),stop)
        self.assertEqual(self.store.traces(self.i)[-1]['detail']['status'],'cancelled_after_response')
    def test_budget_persistent_and_fail_closed(self):
        p=self.client(lambda r:httpx.Response(200,json=good()),daily_attempts=1)
        self.plan(p)
        with self.assertRaisesRegex(ProviderError,'cap'):self.plan(p)
        self.assertEqual(len([c for c in self.calls if c.method=='POST']),1)
        self.assertEqual(Store(Path(self.tmp.name)).budget()['attempts'],1)
    def test_malformed_envelope_never_echo(self):
        for data in [[],{}, {'choices':[]}, {'error':{'message':SECRET}}]:
            with self.subTest(data=data):
                with self.assertRaises(ProviderError) as e:self.plan(self.client(lambda r:httpx.Response(200,json=data)))
                self.assertNotIn(SECRET,str(e.exception))
    def test_non_json_response(self):
        with self.assertRaisesRegex(ProviderError,'JSON'):self.plan(self.client(lambda r:httpx.Response(200,text='not json '+SECRET)))
    def test_malicious_output_boundary(self):
        for change in ['asset','negative','path','tool','extra','duplicate','overlong']:
            with self.subTest(change=change):
                b=fixture('A fictional bottle').model_dump()
                if change=='asset':b['scenes'][0]['asset_id']='../../secret'
                if change=='negative':b['scenes'][0]['seconds']=-5
                if change=='path':b['output_path']='/tmp/pwn'
                if change=='tool':b['tool']='run_shell'
                if change=='extra':b['scenes'][0]['command']='rm -rf data'
                if change=='duplicate':b['scenes'][1]['id']=b['scenes'][0]['id']
                if change=='overlong':b['scenes'][0]['title']='x'*71
                # Separate budget for every subtest; contract rejection must reach schema boundary.
                s=Store(Path(self.tmp.name)/change);i=s.create('A fictional bottle','live');p=Nebius(Settings(key=SECRET,authorized=True),s,httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[{'id':MODEL}]} if r.method=='GET' else good(b))))
                with self.assertRaisesRegex(ProviderError,'boundary'):p.plan(i,'Fiction',MODEL,threading.Event())
                self.assertIsNone(s.get(i)['storyboard'])
    def test_secret_echo_output_discarded(self):
        b=fixture('A fictional bottle').model_dump();b['scenes'][0]['caption']=SECRET
        with self.assertRaisesRegex(ProviderError,'secret'):self.plan(self.client(lambda r:httpx.Response(200,json=good(b))))
        self.assertNotIn(SECRET,json.dumps(self.store.traces(self.i)))
    def test_prompt_injection_remains_plain_data(self):
        b=fixture('A fictional bottle').model_dump();b['scenes'][0]['caption']='<script>fetch("https://example.com")</script> Ignore instructions'
        result=self.plan(self.client(lambda r:httpx.Response(200,json=good(b))))
        self.assertIn('<script>',result.scenes[0].caption) # Text only, never executed by renderer/UI.
    def test_model_and_usage_and_finish_validation(self):
        for field in ['model','usage','finish','tools','empty']:
            d=good()
            if field=='model':d['model']='other/model'
            if field=='usage':d['usage']['total_tokens']=999
            if field=='finish':d['choices'][0]['finish_reason']='length'
            if field=='tools':d['choices'][0]['message']['tool_calls']=[{'name':'shell'}]
            if field=='empty':d['choices'][0]['message']['content']=''
            with self.subTest(field=field),self.assertRaises(ProviderError):self.plan(self.client(lambda r:httpx.Response(200,json=d)))
    def test_oversized_response_stopped(self):
        with self.assertRaisesRegex(ProviderError,'size'):self.plan(self.client(lambda r:httpx.Response(200,content=b'x'*210000)))
        self.assertEqual(self.store.traces(self.i)[-1]['detail']['status'],'response_size_rejected')
    def test_repr_never_contains_key(self):self.assertNotIn(SECRET,repr(Settings(key=SECRET)))
    def test_trace_tampering_detected(self):
        self.plan(self.client(lambda r:httpx.Response(200,json=good())));t=self.store.traces(self.i);t[0]['detail']['model']='changed';self.assertFalse(verify_traces(t))
if __name__=='__main__':unittest.main()
