"""Single-process private video workstation; restart-safe records, bounded workers."""
from __future__ import annotations
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import RLock, Event
import csv, io, json, os, re, secrets, shutil, time, uuid, zipfile
from functools import wraps
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .core import analyze, recommend, render, validate_plan, version_evidence

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.getenv('VISION_DATA_DIR',str(ROOT/'runtime'))).resolve()
DATA.mkdir(parents=True,exist_ok=True)
MAX_BYTES=150*1024*1024
MAX_JOBS=30
LOCK=RLock(); STOPS={}; WORKER=ThreadPoolExecutor(max_workers=1,thread_name_prefix='vision')
TOKEN=os.getenv('VISION_ACCESS_TOKEN','')
REMOTE=os.getenv('VISION_EXECUTION_ENV','local')!='local'
if REMOTE and len(TOKEN)<24: raise RuntimeError('Remote execution requires VISION_ACCESS_TOKEN of at least 24 characters.')


def folder(jid):
    if not re.fullmatch('[a-f0-9]{32}',jid): raise HTTPException(404,'Unknown job')
    p=DATA/jid
    if not (p/'job.json').is_file(): raise HTTPException(404,'Unknown job')
    return p


def read(jid):
    with LOCK: return json.loads((folder(jid)/'job.json').read_text())


def write(jid, **updates):
    with LOCK:
        p=DATA/jid; old=json.loads((p/'job.json').read_text()) if (p/'job.json').exists() else {}
        old.update(updates); old['updated_at']=time.time()
        temp=p/'job.tmp'; temp.write_text(json.dumps(old,indent=2)); temp.replace(p/'job.json')
        return old


def log(jid,event,**data):
    with LOCK:
        with (DATA/jid/'events.jsonl').open('a') as f: f.write(json.dumps({'time':time.time(),'event':event,**data})+'\n')


def recover():
    for p in DATA.glob('*/job.json'):
        try:
            j=json.loads(p.read_text())
            if j['status'] in ['uploading','queued','analyzing','rendering','cancelling']:
                write(j['id'],status='interrupted',error='Server stopped during this operation. Original and prior outputs are retained. Retry explicitly.')
                log(j['id'],'restart_interrupted')
        except (ValueError,KeyError): pass


@asynccontextmanager
async def lifespan(app):
    version_evidence(); recover()
    yield
    for stop in STOPS.values(): stop.set()
    WORKER.shutdown(wait=True,cancel_futures=True)

app=FastAPI(title='EvoVid Vision Director',version='1.0.0',lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver']+os.getenv('VISION_ALLOWED_HOSTS','').split(','))


@app.middleware('http')
async def private_boundary(request, call_next):
    # Reject cross-origin writes and DNS-rebinding hosts. No permissive CORS.
    if request.method not in ['GET','HEAD','OPTIONS']:
        origin=request.headers.get('origin')
        if origin and origin!=str(request.base_url).rstrip('/'):
            return JSONResponse({'detail':'Cross-origin requests are not allowed.'},status_code=403)
        length=request.headers.get('content-length','0')
        try:
            if int(length)>MAX_BYTES: return JSONResponse({'detail':'Upload exceeds 150 MB.'},status_code=413)
        except ValueError: return JSONResponse({'detail':'Invalid content length.'},status_code=400)
    if TOKEN and request.url.path.startswith('/api/') and request.url.path not in ['/api/health','/api/session']:
        supplied=request.headers.get('authorization','').removeprefix('Bearer ') or request.cookies.get('vision_session','')
        if not secrets.compare_digest(supplied,TOKEN): return JSONResponse({'detail':'Enter the access token to unlock this workstation.'},status_code=401)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'"
    return response


@app.get('/api/health')
def health():
    return {'ok':True,'opencv':version_evidence()['opencv'],'mode':os.getenv('VISION_EXECUTION_ENV','local'),
            'auth_required':bool(TOKEN),'aws_verified':False,'max_mb':150,'max_seconds':180}


@app.post('/api/session')
async def session(request:Request):
    value=(await request.json()).get('token','')
    if not TOKEN or not isinstance(value,str) or not secrets.compare_digest(value,TOKEN): raise HTTPException(401,'Invalid access token.')
    r=JSONResponse({'ok':True}); r.set_cookie('vision_session',TOKEN,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=3600)
    return r


@app.delete('/api/session')
def logout():
    r=JSONResponse({'ok':True}); r.delete_cookie('vision_session'); return r


@app.get('/api/jobs')
def jobs():
    items=[]
    for p in DATA.glob('*/job.json'):
        try:
            j=json.loads(p.read_text()); items.append({k:j.get(k) for k in ['id','name','status','created_at','updated_at','progress','error','synthetic']})
        except ValueError: continue
    return sorted(items,key=lambda j:j['created_at'],reverse=True)


def locked(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        with LOCK: return fn(*args,**kwargs)
    return wrapper


@locked
def begin_analysis(jid):
    if jid in STOPS: raise HTTPException(409,"Operation already active.")
    ev=Event(); STOPS[jid]=ev
    write(jid,status='queued',progress=0,error=None); log(jid,'analysis_queued')
    def task():
        try:
            if ev.is_set(): raise InterruptedError('Cancelled before analysis.')
            write(jid,status='analyzing')
            result=analyze(DATA/jid/'original.media',DATA/jid,ev.is_set,lambda n:write(jid,progress=n))
            if ev.is_set(): raise InterruptedError('Cancelled by user.')
            (DATA/jid/'analysis.json').write_text(json.dumps(result,indent=2))
            plan=recommend(result,min(10,result['duration']))
            write(jid,status='review',progress=100,analysis=result,proposal=plan)
            log(jid,'analysis_finished',input_sha256=result['input_sha256'],opencv=result['versions']['opencv'])
        except Exception as e:
            write(jid,status='cancelled' if isinstance(e,InterruptedError) else 'failed',error=str(e)); log(jid,'analysis_failed',error=str(e))
        finally:
            with LOCK: STOPS.pop(jid,None)
    WORKER.submit(task)


@app.post('/api/jobs')
async def upload(request:Request):
    if len(list(DATA.glob('*/job.json')))>=MAX_JOBS: raise HTTPException(409,'30-job local storage cap reached. Archive or move runtime jobs while the server is stopped.')
    if shutil.disk_usage(DATA).free<2*1024**3: raise HTTPException(507,'At least 2 GB free disk space is required.')
    # User filenames are labels only, never paths.
    name=request.headers.get('x-filename','upload.mp4')[:120]
    name=re.sub(r'[\x00-\x1f<>]','_',name)
    jid=uuid.uuid4().hex; p=DATA/jid; p.mkdir(mode=0o700)
    write(jid,id=jid,name=name,created_at=time.time(),status='uploading',progress=0,synthetic=None,provenance='User upload; source provenance unverified',attempts=[])
    size=0
    try:
        with (p/'original.media').open('wb') as f:
            async for chunk in request.stream():
                size+=len(chunk)
                if size>MAX_BYTES: raise HTTPException(413,'Upload exceeds 150 MB. Partial upload retained for diagnosis.')
                f.write(chunk)
        if size==0: raise HTTPException(400,'Empty upload. Choose a video file.')
        write(jid,bytes=size); log(jid,'uploaded',bytes=size)
        begin_analysis(jid)
    except Exception as e:
        write(jid,status='failed',error=str(getattr(e,'detail',e))); raise
    return {'id':jid}


@app.post('/api/demo')
def demo():
    sample=ROOT/'examples'/'synthetic-quality-lab.mp4'
    if not sample.exists(): raise HTTPException(409,'Generate demos first: python tools/make_examples.py')
    if len(jobs())>=MAX_JOBS: raise HTTPException(409,'30-job cap reached.')
    jid=uuid.uuid4().hex; p=DATA/jid; p.mkdir(mode=0o700)
    shutil.copyfile(sample,p/'original.media')
    write(jid,id=jid,name='SYNTHETIC • Quality lab',created_at=time.time(),status='queued',progress=0,synthetic=True,attempts=[])
    log(jid,'synthetic_demo_loaded'); begin_analysis(jid); return {'id':jid}


@app.get('/api/jobs/{jid}')
def job(jid:str): return read(jid)


@app.post('/api/jobs/{jid}/recommend')
async def proposal(jid:str, request:Request):
    j=read(jid)
    if j['status'] in ['queued','analyzing','rendering','cancelling']: raise HTTPException(409,'Wait for the current operation.')
    if 'analysis' not in j: raise HTTPException(409,'Complete analysis first.')
    try:
        body=await request.json(); target=float(body.get('target',10)); weight=float(body.get('sharpness_weight',1))
        if not .1<=target<=180 or not 0<=weight<=4: raise ValueError('Target: 0.1–180 seconds. Sharpness weight: 0–4.')
        plan=recommend(j['analysis'],target,weight)
    except (ValueError,TypeError) as e: raise HTTPException(400,str(e))
    write(jid,proposal=plan); log(jid,'proposal_revised',target=target,sharpness_weight=weight); return plan


@app.post('/api/jobs/{jid}/render')
async def start_render(jid:str, request:Request):
    body=await request.json()
    return _start_render(jid,body)


@locked
def _start_render(jid,body):
    j=read(jid)
    if jid in STOPS or j['status'] in ['queued','analyzing','rendering','cancelling']: raise HTTPException(409,'An operation is already running.')
    if 'analysis' not in j: raise HTTPException(409,'Complete analysis first.')
    if len(j.get('attempts',[]))>=10: raise HTTPException(409,'10-render cap per job reached. Create a new job after archiving.')
    try: plan=validate_plan(body,j['analysis'])
    except (ValueError,TypeError,KeyError) as e: raise HTTPException(400,str(e))
    attempt=f"attempt-{len(j.get('attempts',[]))+1:03d}"; ev=Event(); STOPS[jid]=ev
    write(jid,status='rendering',progress=0,error=None,approved_plan=plan,active_attempt=attempt,
          attempts=j.get('attempts',[])+[{'id':attempt,'started_at':time.time()}])
    log(jid,'human_approved_render',attempt=attempt,plan=plan)
    def task():
        try:
            result=render(DATA/jid/'original.media',plan,j['analysis'],DATA/jid/attempt,ev.is_set,lambda n:write(jid,progress=n))
            if ev.is_set(): raise InterruptedError('Cancelled by user.')
            result['attempt']=attempt
            write(jid,status='complete',progress=100,result=result)
            log(jid,'render_finished',attempt=attempt,output_sha256=result['sha256'])
        except Exception as e:
            write(jid,status='cancelled' if isinstance(e,InterruptedError) else 'failed',error=str(e)); log(jid,'render_failed',attempt=attempt,error=str(e))
        finally:
            with LOCK: STOPS.pop(jid,None)
    WORKER.submit(task); return {'id':jid,'attempt':attempt}


@app.post('/api/jobs/{jid}/cancel')
@locked
def cancel(jid:str):
    j=read(jid)
    ev=STOPS.get(jid)
    if ev is not None and j['status'] in ['queued','analyzing','rendering','cancelling']:
        ev.set(); write(jid,status='cancelling'); log(jid,'cancel_requested')
    return {'ok':True}


@app.post('/api/jobs/{jid}/retry')
def retry(jid:str):
    j=read(jid)
    if jid in STOPS: raise HTTPException(409,'Operation already active.')
    if j['status'] not in ['failed','cancelled','interrupted']: raise HTTPException(409,'Retry is available after failure, cancellation or restart.')
    if (folder(jid)/'original.media').stat().st_size==0: raise HTTPException(400,'Original file is empty. Upload a new video.')
    begin_analysis(jid); return {'id':jid}


@app.get('/api/jobs/{jid}/media/{which}')
def media(jid:str,which:str):
    j=read(jid)
    if which=='original': return FileResponse(folder(jid)/'original.media',media_type='video/mp4',filename=None)
    if which=='output' and j.get('result'): return FileResponse(folder(jid)/j['result']['attempt']/'output.mp4',media_type='video/mp4',filename='vision-director.mp4')
    raise HTTPException(404,'Output not available yet.')


@app.get('/api/jobs/{jid}/thumbnail/{index}')
def thumb(jid:str,index:int):
    if index<0 or index>720: raise HTTPException(404)
    p=folder(jid)/f'frame-{index:04d}.jpg'
    if not p.is_file(): raise HTTPException(404)
    return FileResponse(p,media_type='image/jpeg')


@app.get('/api/jobs/{jid}/report')
def report(jid:str):
    j=read(jid)
    return Response(json.dumps(j,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="vision-report-{jid[:8]}.json"'})


@app.get('/api/jobs/{jid}/metrics.csv')
def metric_csv(jid:str):
    samples=read(jid).get('analysis',{}).get('samples',[])
    out=io.StringIO()
    if samples:
        w=csv.DictWriter(out,fieldnames=list(samples[0]));w.writeheader();w.writerows(samples)
    return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="vision-metrics.csv"'})


@app.get('/api/jobs/{jid}/logs')
def logs(jid:str):
    p=folder(jid); content=(p/'events.jsonl').read_text() if (p/'events.jsonl').exists() else ''
    for logfile in sorted(p.glob('attempt-*/ffmpeg.log')): content+='\n'+logfile.parent.name+'\n'+logfile.read_text(errors='replace')[-30000:]
    return Response(content,media_type='text/plain')


@app.get('/api/jobs/{jid}/bundle')
def bundle(jid:str):
    p=folder(jid); target=p/'report.zip'
    with LOCK, zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for f in [p/'job.json',p/'analysis.json',p/'events.jsonl']+list(p.glob('attempt-*/approved-plan.json'))+list(p.glob('attempt-*/ffmpeg.log')):
            if f.is_file(): z.write(f,f.relative_to(p))
        z.writestr('README.txt','Audit bundle. Original/output videos are separate downloads to avoid accidental media sharing. Synthetic flag is in job.json. AWS execution is not yet verified.\n')
    return FileResponse(target,media_type='application/zip',filename=f'vision-audit-{jid[:8]}.zip')

app.mount('/',StaticFiles(directory=ROOT/'static',html=True),name='ui')
