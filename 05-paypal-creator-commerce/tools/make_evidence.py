"""Exercise the real local HTTP application and save fixture-labeled media.
Run after starting launcher.py. Does not contact PayPal or any model service.
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
base='http://127.0.0.1:'+os.getenv('PORT','8715')
with httpx.Client(base_url=base,timeout=100,trust_env=False) as client:
    boot=client.get('/api/bootstrap');boot.raise_for_status();config=boot.json()
    if config['payment_mode']!='fixture':raise SystemExit('Evidence generator only runs in clearly labeled fixture mode.')
    client.headers.update({'Origin':base,'X-CSRF-Token':config['csrf']})
    def post(path,body={}):
        r=client.post(path,json=body);r.raise_for_status();return r.json()
    project=post('/api/projects',{'brief':'Launch a fictional Northlight coffee brand. A portrait story about small-batch craft and brighter mornings.','planner':'fixture'})
    pid=project['id']
    denied=client.post('/api/projects/'+pid+'/exports',json={})
    assert denied.status_code==403
    preview=post('/api/projects/'+pid+'/preview')
    pre=client.get(preview['url']);pre.raise_for_status();(OUT/'sample-preview-fixture.mp4').write_bytes(pre.content)
    order=post('/api/checkout/orders',{'project_id':pid,'revision':1,'sku':'portrait-hd-export'})
    pending=post('/api/orders/'+order['id']+'/fixture',{'scenario':'pending'});assert pending['status']=='PENDING'
    assert not client.get('/api/projects/'+pid).json()['entitled']
    uncertain=post('/api/orders/'+order['id']+'/fixture',{'scenario':'lost-response'});assert uncertain['status']=='VERIFYING'
    complete=post('/api/orders/'+order['id']+'/reconcile');assert complete['status']=='COMPLETED'
    out=post('/api/projects/'+pid+'/exports')
    media=client.get(out['url']);media.raise_for_status();(OUT/'sample-export-fixture.mp4').write_bytes(media.content)
    source=client.get('/api/projects/'+pid+'/source').json();(OUT/'sample-storyboard.json').write_text(json.dumps(source,indent=2),encoding='utf-8')
    proof=client.get('/api/projects/'+pid+'/evidence').json()
    proof['assertions']={'unpaid_export_rejected':True,'pending_locked':True,'lost_response_recovered_same_order':True,'actual_mp4_bytes':len(media.content),'actual_mp4_sha256':hashlib.sha256(media.content).hexdigest()}
    proof['not_verified']=['Actual PayPal Sandbox transaction','Actual local AI model inference','Browser UI rendering/recording','Windows startup']
    (OUT/'fixture-http-evidence.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Saved real fixture-labeled MP4 and HTTP evidence. No actual PayPal payment or model inference occurred.')
