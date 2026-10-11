"""Generate synthetic fixture artifacts through the real API and renderer. No network."""
import hashlib,json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from evodock.app import create_app
from evodock.provider import Settings
BASE=Path(__file__).resolve().parents[1]
def wait(c,i):
    for _ in range(1000):
        p=c.get('/api/projects/'+i).json()
        if p['jobs'][0]['status'] not in ('queued','running'):
            if p['jobs'][0]['status']!='complete':raise RuntimeError(p['jobs'][0]['error'])
            return p
        time.sleep(.05)
    raise RuntimeError('Local sample timed out')
def main():
    c=TestClient(create_app(BASE/'examples'/'sample-data',Settings()));c.headers['X-EvoDock-Request']='local-ui'
    rows=[]
    briefs=['A warm introduction for a fictional reusable bottle. Show curiosity, a detail, and an invitation.','A calm nature journal in three geometric scenes.','A playful space postcard with an orbital opening.']
    for n,brief in enumerate(briefs):
        r=c.post('/api/projects',json={'brief':brief,'mode':'fixture'});r.raise_for_status();i=r.json()['project_id'];p=wait(c,i)
        for instruction in ['Make it shorter','Make the palette warmer']:
            r=c.post('/api/projects/'+i+'/revise',json={'instruction':instruction,'expected_revision':p['revision']});r.raise_for_status();p=wait(c,i)
        (BASE/'examples'/f'fixture-{n+1}.json').write_text(json.dumps(p,ensure_ascii=False,indent=2))
        if n==0:
            r=c.post('/api/projects/'+i+'/render',json={'expected_revision':p['revision'],'confirmed':True});r.raise_for_status();p=wait(c,i)
            for name in ['preview.mp4','poster.png','project.zip','manifest.json','trace.json']:
                data=c.get(f'/api/projects/{i}/files/{p["revision"]}/{name}');data.raise_for_status();(BASE/'examples'/name).write_bytes(data.content)
        rows.append({'project':i,'mode':'DEMO_FIXTURE','brief':brief,'revisions':p['revision'],'provider_calls':0,'trace_integrity':p['trace_integrity']})
    (BASE/'evidence'/'fixture-evaluation.json').write_text(json.dumps({'label':'OFFLINE FIXTURE EVALUATION — NOT LIVE NEBIUS EVIDENCE','cases':rows,'success_count':len(rows),'sample_count':len(briefs),'real_model_calls':0},indent=2))
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
