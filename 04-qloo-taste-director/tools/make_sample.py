"""Reproduce a genuine DEMO API project and real silent motion-graphic MP4.
No live key or Qloo network call is used. Run from this project's root.
"""
from pathlib import Path
import json, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from taste.server import create_app
from taste.qloo import Qloo

root = Path(__file__).resolve().parent.parent
out = root / 'samples'
out.mkdir(exist_ok=True)

def wait(client, i):
    deadline = time.monotonic()+90
    while time.monotonic() < deadline:
        row = client.get('/api/jobs/'+i).json()
        if row['status'] not in ('queued','running'):
            if row['status'] != 'complete': raise RuntimeError(row['error'])
            return row
        time.sleep(.05)
    raise RuntimeError('Operation did not complete within sample-generation limit.')

with tempfile.TemporaryDirectory(dir=root/'evidence') as home:
    with TestClient(create_app(home, provider=Qloo()), base_url='http://127.0.0.1') as client:
        headers={'X-Taste-Client':'1'}
        client.get('/api/state')
        def post(path,data):
            response=client.post(path,json=data,headers=headers)
            response.raise_for_status()
            return response.json()
        def create(title,rid,parent=None):
            candidate=post('/api/search',{'query':title,'category':'movie','mode':'demo','public_reference':True})['candidates'][0]
            payload={'entity_ids':[candidate['id']],'mode':'demo','goal':'Find a little wonder in an ordinary day','duration':16,'aspect':'16:9','pace':'balanced','budget':'phone-only','parent_id':parent,'request_id':rid}
            return wait(client,post('/api/plans',payload)['id'])
        first=create('Spirited Away','sample-plan-001')
        changed=create('Interstellar','sample-plan-002',first['id'])
        (out/'demo-project.json').write_bytes(client.get('/api/projects/'+first['id']+'/export/json').content)
        (out/'demo-brief.md').write_bytes(client.get('/api/projects/'+first['id']+'/export/md').content)
        (out/'demo-replanned-project.json').write_bytes(client.get('/api/projects/'+changed['id']+'/export/json').content)
        video=wait(client,post('/api/projects/'+first['id']+'/render',{'version':1,'request_id':'sample-render-001'})['id'])
        (out/'demo-storyboard.mp4').write_bytes(client.get(video['result']['url']).content)
        report={'source':'DEMO synthetic fixtures, not Qloo live evidence','actual_qloo_calls':0,'workflow':'Application search → explicit candidate → plan → export; feedback replan','first_theme':first['result']['briefs'][0]['theme'],'replanned_theme':changed['result']['briefs'][0]['theme'],'video':video['result'],'plan_events':first['events'],'render_events':video['events']}
        (out/'sample-manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({'result':'complete','mode':'DEMO','actual_qloo_calls':0,'first_theme':report['first_theme'],'replanned_theme':report['replanned_theme'],'video':video['result']},indent=2))
