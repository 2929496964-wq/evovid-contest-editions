"""Loopback-only local application. Never exposes provider credentials to the browser."""
import os, re, threading, time, shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .models import *
from .provider import Nebius, Settings, ProviderError
from .fixture import fixture
from .render import render, package
from .store import Store, Conflict, digest, verify_traces
BASE=Path(__file__).resolve().parent.parent

def create_app(home=None,settings=None,transport=None):
    app=FastAPI(title='EvoDock local storyboard studio',docs_url='/api/docs',redoc_url=None)
    store=Store(home or os.getenv('EVODOCK_DATA_DIR',str(BASE/'data')))
    cfg=settings or Settings.env();provider=Nebius(cfg,store,transport)
    pool=ThreadPoolExecutor(max_workers=2);stops={};lock=threading.RLock()
    app.state.store=store;app.state.provider=provider;app.state.stops=stops
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver','[::1]'])
    @app.middleware('http')
    async def local_boundary(request:Request,call_next):
        if request.method in ('POST','PUT','DELETE','PATCH'):
            origin=request.headers.get('origin')
            if origin and origin != str(request.base_url).rstrip('/'):
                return JSONResponse({'detail':'Cross-origin mutations are blocked.'},status_code=403)
            if request.headers.get('x-evodock-request')!='local-ui':return JSONResponse({'detail':'Missing local request guard.'},status_code=403)
            raw_length=request.headers.get('content-length')
            if raw_length is None:return JSONResponse({'detail':'Content-Length is required.'},status_code=411)
            if not raw_length.isdigit():return JSONResponse({'detail':'Invalid Content-Length.'},status_code=400)
            if int(raw_length)>24000:return JSONResponse({'detail':'Request too large.'},status_code=413)
            body=bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body)>24000:return JSONResponse({'detail':'Request too large.'},status_code=413)
            if len(body)!=int(raw_length):return JSONResponse({'detail':'Content-Length mismatch.'},status_code=400)
            request._body=bytes(body)
        result=await call_next(request)
        result.headers['X-Content-Type-Options']='nosniff';result.headers['Referrer-Policy']='no-referrer'
        result.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; frame-ancestors 'none'; connect-src 'self'"
        result.headers['Cache-Control']='no-store'
        return result
    @app.exception_handler(RequestValidationError)
    async def bad_input(request,exc):return JSONResponse({'detail':'Input validation failed. Check scene IDs, allowed assets, text lengths and duration (2–8 seconds; total ≤36).'},status_code=422)
    @app.exception_handler(Conflict)
    async def conflict(request,exc):return JSONResponse({'detail':str(exc)},status_code=409)
    @app.exception_handler(ProviderError)
    async def provider_error(request,exc):return JSONResponse({'detail':str(exc)},status_code=503)
    def get(i):
        if not re.fullmatch(r'[a-f0-9]{32}',i):raise HTTPException(404,'Project not found.')
        p=store.get(i)
        if not p:raise HTTPException(404,'Project not found.')
        return p
    def safe_text(text):
        if cfg.key and cfg.key in text:raise HTTPException(422,'Credential-like data must not be put in project content.')
    def idle(p):
        if any(j['status'] in ('running','queued') for j in p['jobs']):raise Conflict('Wait for the active job or cancel it before editing.')
    def submit(i,kind,fn):
        j=store.job(i,kind);stop=threading.Event();stops[j]=stop
        def work():
            try:
                if stop.is_set():raise InterruptedError('Cancelled before execution.')
                store.job_set(j,'running');result=fn(stop)
                store.job_set(j,'complete',result=result)
            except InterruptedError as e:store.job_set(j,'cancelled',error=str(e))
            except (ProviderError,Conflict,RuntimeError) as e:store.job_set(j,'failed',error=str(e))
            except Exception:store.job_set(j,'failed',error='Local operation failed. Saved revisions remain available; inspect local configuration and retry.')
            finally:stops.pop(j,None)
        pool.submit(work);return {'project_id':i,'job_id':j}
    def plan_work(i,request,previous=None,instruction='',expected=0):
        def run(stop):
            if request.mode=='live':board=provider.plan(i,request.brief,request.model,stop,previous,instruction)
            else:
                if stop.wait(.25):raise InterruptedError('Fixture planning cancelled.')
                board=fixture(request.brief,previous,instruction)
                store.trace(i,{'source':'DEMO_FIXTURE','status':'deterministic_template','model':None,'usage':None,'input_sha256':digest({'brief':request.brief,'previous':previous,'instruction':instruction}),'output_sha256':digest(board.model_dump())})
            if stop.is_set():raise InterruptedError('Cancelled before saving the planned revision.')
            revision=store.save(i,board.model_dump(),'DEMO_FIXTURE' if request.mode=='fixture' else 'LIVE_NEBIUS',expected,instruction)
            return {'revision':revision}
        return run
    def live_gate(req):
        if req.mode=='live':
            cfg.check()
            if not req.consent_to_transmit:raise HTTPException(422,'Consent is required to send the brief and current storyboard to Nebius.')
            if not req.model:raise HTTPException(422,'Discover and select a NVIDIA model first.')
    @app.get('/api/status')
    def status():
        configured=bool(cfg.key and cfg.authorized and cfg.endpoint in ('https://api.tokenfactory.nebius.com/v1','https://api.tokenfactory.us-central1.nebius.com/v1'))
        return {'app':'EvoDock','version':'0.1.0','live_configured':configured,'endpoint':cfg.endpoint if cfg.endpoint in ('https://api.tokenfactory.nebius.com/v1','https://api.tokenfactory.us-central1.nebius.com/v1') else 'invalid','live_verified':False,'renderer_available':bool(shutil.which('ffmpeg')),'renderer_note':'FFmpeg found on PATH; H.264 encoder required' if shutil.which('ffmpeg') else 'FFmpeg is missing. Install it from https://ffmpeg.org/download.html, add it to PATH, then restart EvoDock. Storyboard editing still works.','status_note':'Live success is evidenced per project only. No account or regional eligibility is inferred.','budget':store.budget(),'limits':{'output_tokens':cfg.max_output,'daily_attempts':cfg.daily_attempts,'daily_reserved_tokens':cfg.daily_tokens},'assets':ASSETS}
    @app.get('/api/models')
    def models():return {'models':provider.discover(),'source':'LIVE_DISCOVERY','endpoint':cfg.endpoint}
    @app.get('/api/projects')
    def projects():return store.list()
    @app.get('/api/projects/{i}')
    def project(i:str):
        p=get(i);p['trace_integrity']=verify_traces(p['traces']);return p
    @app.post('/api/projects')
    def create(req:PlanRequest):
        safe_text(req.brief);live_gate(req)
        i=store.create(req.brief,req.mode)
        return submit(i,'plan',plan_work(i,req))
    @app.post('/api/projects/{i}/retry')
    def retry(i:str,req:PlanRequest):
        p=get(i);idle(p)
        if p['revision']!=0:raise Conflict('This project already has a storyboard; use a revision instead.')
        if req.mode!=p['mode'] or req.brief!=p['brief']:raise HTTPException(422,'A retry must keep the same brief and mode.')
        live_gate(req);return submit(i,'plan',plan_work(i,req))
    @app.post('/api/projects/{i}/revise')
    def revise(i:str,req:RevisionRequest):
        with lock:
            p=get(i);idle(p);safe_text(req.instruction)
            if p['revision']!=req.expected_revision or not p['storyboard']:raise Conflict('Reload the current storyboard before revising.')
            r=PlanRequest(brief=p['brief'],mode=p['mode'],model=req.model,consent_to_transmit=req.consent_to_transmit);live_gate(r)
            return submit(i,'revise',plan_work(i,r,p['storyboard'],req.instruction,p['revision']))
    @app.put('/api/projects/{i}')
    def edit(i:str,req:EditRequest):
        with lock:
            p=get(i);idle(p);safe_text(req.storyboard.model_dump_json())
            rev=store.save(i,req.storyboard.model_dump(),'USER_EDIT',req.expected_revision)
            store.trace(i,{'source':'LOCAL_EDIT','status':'validated','revision':rev,'output_sha256':digest(req.storyboard.model_dump())})
        return {'revision':rev}
    @app.post('/api/projects/{i}/render')
    def start_render(i:str,req:RenderRequest):
        with lock:
            p=get(i);idle(p)
            if not req.confirmed:raise HTTPException(422,'Confirm the local render before execution.')
            if req.expected_revision!=p['revision'] or not p['storyboard']:raise Conflict('Reload the current storyboard before rendering.')
            folder=store.home/i/f'r{p["revision"]}'
            if (folder/'project.zip').exists():return {'project_id':i,'cached':True,'revision':p['revision']}
            def run(stop):
                board=Storyboard.model_validate(p['storyboard'])
                video=render(board,folder,p['mode'],stop)
                store.trace(i,{'source':'LOCAL_RENDER','status':'complete','revision':p['revision'],'output_sha256':__import__('hashlib').sha256(video.read_bytes()).hexdigest(),'board_sha256':digest(p['storyboard']),'seconds':sum(s.seconds for s in board.scenes)})
                result=package(store.get(i),folder)
                return {'revision':p['revision'],'manifest':result}
            return submit(i,'render',run)
    @app.post('/api/jobs/{j}/cancel')
    def cancel(j:str):
        job=store.job_get(j)
        if not job:raise HTTPException(404,'Job not found.')
        stop=stops.get(j)
        if stop:stop.set()
        return {'cancel_requested':bool(stop),'note':'In-flight provider processing may still be billed; results are discarded after cancellation.'}
    @app.get('/api/projects/{i}/files/{revision}/{name}')
    def file(i:str,revision:int,name:str):
        p=get(i)
        if revision<1 or revision>p['revision'] or name not in ('preview.mp4','poster.png','project.zip','storyboard.json','trace.json','manifest.json','captions.srt'):raise HTTPException(404,'File not found.')
        path=store.home/i/f'r{revision}'/name
        if not path.is_file():raise HTTPException(404,'Render this revision first.')
        return FileResponse(path,filename=name if name!='preview.mp4' and name!='poster.png' else None)
    app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
    @app.get('/')
    def index():return FileResponse(BASE/'static'/'index.html')
    return app
