"""Run against an existing local/private server; records actual HTTP/video checks."""
import argparse,json,time,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx,cv2
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8712');p.add_argument('--output',default='evidence/e2e.json');a=p.parse_args()
ROOT=Path(__file__).resolve().parents[1];out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True)
c=httpx.Client(base_url=a.url,timeout=30,trust_env=False)
import os
if os.getenv('VISION_ACCESS_TOKEN'): c.headers['Authorization']='Bearer '+os.environ['VISION_ACCESS_TOKEN']
checks=[]
def check(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),'detail':detail});assert ok,name

def wait(jid,statuses,limit=180):
    end=time.monotonic()+limit
    while time.monotonic()<end:
        j=c.get('/api/jobs/'+jid).json()
        if j['status'] in statuses:return j
        if j['status'] in ['failed','cancelled']:raise AssertionError(j)
        time.sleep(.2)
    raise TimeoutError(j)

try:
    health=c.get('/api/health').json();check('actual OpenCV5',health['opencv']=='5.0.0',health)
    bad=c.post('/api/jobs',content=b'');check('empty upload rejected',bad.status_code==400)
    bad=c.post('/api/jobs',content=b'garbage',headers={'X-Filename':'bad.mp4'});jid=bad.json()['id'];failed=wait(jid,{'failed'});check('bad video fails honestly',failed['status']=='failed',failed.get('error'))
    data=(ROOT/'examples/synthetic-quality-lab.mp4').read_bytes()
    response=c.post('/api/jobs',content=data,headers={'X-Filename':'../../synthetic-quality-lab.mp4'});response.raise_for_status();jid=response.json()['id']
    j=wait(jid,{'review'});check('upload analyzed',j['analysis']['sample_count']>10,jid)
    check('input hash preserved',j['analysis']['input_sha256']==hashlib.sha256(data).hexdigest())
    check('unsafe path rejected',c.get('/api/jobs/not-a-job').status_code==404)
    plan=c.post(f'/api/jobs/{jid}/recommend',json={'target':4,'sharpness_weight':4}).json()
    unapproved=c.post(f'/api/jobs/{jid}/render',json={'approved':False,'clips':plan['clips']});check('unapproved render rejected',unapproved.status_code==400)
    rendered=c.post(f'/api/jobs/{jid}/render',json={'approved':True,'clips':plan['clips']});rendered.raise_for_status()
    duplicate=c.post(f'/api/jobs/{jid}/render',json={'approved':True,'clips':plan['clips']});check('duplicate render rejected',duplicate.status_code==409)
    j=wait(jid,{'complete'});response=c.get(f'/api/jobs/{jid}/media/output');response.raise_for_status()
    mp4=out.parent/'e2e-output.mp4';mp4.write_bytes(response.content)
    cap=cv2.VideoCapture(str(mp4));ok,frame=cap.read();fps=cap.get(cv2.CAP_PROP_FPS);duration=cap.get(cv2.CAP_PROP_FRAME_COUNT)/fps;cap.release()
    check('rendered MP4 decodes',ok and frame.size>0);check('duration within tolerance',abs(duration-4)<.5,duration)
    check('output hash verified',hashlib.sha256(response.content).hexdigest()==j['result']['sha256'])
    check('original still byte-identical',c.get(f'/api/jobs/{jid}/media/original').content==data)
    check('CSV export',c.get(f'/api/jobs/{jid}/metrics.csv').text.startswith('luma,'))
    check('audit ZIP export',c.get(f'/api/jobs/{jid}/bundle').content.startswith(b'PK'))
    check('cross-origin write blocked',c.post('/api/demo',headers={'Origin':'https://evil.example'}).status_code==403)
    check('host rebinding blocked',c.get('/api/health',headers={'Host':'evil.example'}).status_code==400)
    (out.parent/'e2e-job-report.json').write_text(json.dumps(j,indent=2))
finally:
    out.write_text(json.dumps({'checks':checks,'passed':all(x['passed'] for x in checks),'url':a.url,'tested_at':time.time()},indent=2))
print(json.dumps(checks,indent=2))
