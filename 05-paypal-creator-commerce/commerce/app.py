"""Local creator-commerce API. All rights are derived from verified server evidence."""
import hashlib, json, secrets, sqlite3, uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .config import Settings, ROOT
from .store import Store
from .models import NewProject, EditProject, ImportProject, Checkout, FixtureAction, Board
from .planner import plan
from .paypal import PayPalSandbox, FixturePayments, PaymentRejected, PaymentUnavailable, verify_completion, verify_order_identity
from .render import render

PRICE='4.99';CURRENCY='USD';SKU='portrait-hd-export'
COOKIE='evovid_creator_session'

def now():return datetime.now(timezone.utc).isoformat()
def uid():return uuid.uuid4().hex
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def pack(value):return json.dumps(value,ensure_ascii=False,sort_keys=True)
def fail(status,message):raise HTTPException(status,message)

def create_app(settings=None, payment_adapter=None, ai_client=None):
    settings=settings or Settings.from_env()
    settings.data_dir.mkdir(parents=True,exist_ok=True)
    store=Store(settings.data_dir/'commerce.sqlite3')
    payments=payment_adapter or (PayPalSandbox(settings) if settings.payment_mode=='sandbox' else FixturePayments())
    if payments.mode!=settings.payment_mode:raise ValueError('Payment adapter and ledger mode must match.')
    @asynccontextmanager
    async def lifespan(app):
        yield
        payments.close()
    app=FastAPI(title='EvoVid Creator Commerce · Sandbox only',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
    app.state.store=store;app.state.settings=settings;app.state.payments=payments
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost'])
    port=urlparse(settings.origin).port or 80
    origins={f'http://127.0.0.1:{port}',f'http://localhost:{port}'}
    if port==80:origins|={'http://127.0.0.1','http://localhost'}

    @app.middleware('http')
    async def guard(request,call_next):
        # No CORS. Origin + per-session CSRF token guard even localhost requests.
        if request.url.path.startswith('/api/'):
            cookie=request.cookies.get(COOKIE,'')
            with store.connection() as c:
                session=c.execute('SELECT * FROM sessions WHERE id=?',(digest(cookie),)).fetchone() if cookie else None
            request.state.session=dict(session) if session else None
            if request.url.path!='/api/bootstrap' and session is None:return JSONResponse({'detail':'Session missing. Reload the app.'},401)
            if request.method in ('POST','PUT','PATCH','DELETE'):
                if request.headers.get('origin') not in origins:return JSONResponse({'detail':'Untrusted request origin.'},403)
                if not session or not secrets.compare_digest(request.headers.get('x-csrf-token',''),session['csrf']):return JSONResponse({'detail':'Invalid CSRF token. Reload the app.'},403)
                if not request.headers.get('content-type','').startswith('application/json'):return JSONResponse({'detail':'JSON request required.'},415)
                body=b''
                async for part in request.stream():
                    body+=part
                    if len(body)>32768:return JSONResponse({'detail':'Request too large (32 KiB maximum).'},413)
                request._body=body
        response=await call_next(request)
        response.headers.update({'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            'Cache-Control':'no-store'})
        return response

    def owner(request):return request.state.session['id']
    def project(c,pid,who):
        p=c.execute('SELECT * FROM projects WHERE id=? AND owner=?',(pid,who)).fetchone()
        if not p:fail(404,'Project not found in this browser session.')
        return dict(p)
    def order(c,oid,who):
        o=c.execute('SELECT * FROM orders WHERE id=? AND owner=? AND mode=?',(oid,who,settings.payment_mode)).fetchone()
        if not o:fail(404,'Order not found for this session and payment mode.')
        return dict(o)
    def revision(c,pid,rev):
        r=c.execute('SELECT * FROM revisions WHERE project=? AND revision=?',(pid,rev)).fetchone()
        if not r:fail(404,'Project revision not found.')
        return dict(r)
    def entitled(c,pid,rev):return c.execute('SELECT * FROM entitlements WHERE project=? AND revision=? AND mode=?',(pid,rev,settings.payment_mode)).fetchone()
    def public_order(o):
        if not o:return None
        return {k:o[k] for k in ('id','project','revision','mode','sku','amount','currency','status','paypal_id','approval_url','capture_id','error','created')}
    def audit(c,action,pid=None,oid=None,detail=''):
        c.execute('INSERT INTO audit(action,project,order_id,detail,created) VALUES(?,?,?,?,?)',(action,pid,oid,detail,now()))
    def view(c,p):
        r=revision(c,p['id'],p['current_revision']);o=c.execute('SELECT * FROM orders WHERE project=? AND revision=? AND mode=?',(p['id'],p['current_revision'],settings.payment_mode)).fetchone()
        return {**{k:p[k] for k in ('id','title','brief','current_revision','created')},'board':json.loads(r['board']),'provenance':json.loads(r['provenance']),
            'checksum':r['checksum'],'order':public_order(o),'entitled':bool(entitled(c,p['id'],p['current_revision']))}
    def save_project(who,brief,board,provenance):
        pid=uid();body=pack(board.model_dump())
        with store.connection() as c:
            c.execute('INSERT INTO projects VALUES(?,?,?,?,?,?)',(pid,who,board.title,brief,1,now()))
            c.execute('INSERT INTO revisions VALUES(?,?,?,?,?)',(pid,1,body,pack(provenance),digest(body)))
            audit(c,'PROJECT_CREATED',pid,detail=provenance['provider'])
            return view(c,project(c,pid,who))
    def apply_result(o,response):
        try:cid,status=verify_completion(o,response)
        except PaymentRejected as exc:
            with store.connection() as c:
                c.execute('UPDATE orders SET status=?,error=? WHERE id=?',('REJECTED',str(exc),o['id']))
                audit(c,'PAYMENT_REJECTED',o['project'],o['id'],str(exc))
            return
        with store.connection() as c:
            if cid:
                existing=c.execute('SELECT order_id FROM captures WHERE id=?',(cid,)).fetchone()
                if existing and existing['order_id']!=o['id']:fail(409,'Capture has already been assigned to another order.')
                c.execute('INSERT OR IGNORE INTO captures VALUES(?,?,?,?,?,?)',(cid,o['id'],o['amount'],o['currency'],o['mode'],now()))
                c.execute('INSERT OR IGNORE INTO entitlements VALUES(?,?,?,?,?,?)',(o['project'],o['revision'],o['mode'],o['id'],cid,now()))
                c.execute('UPDATE orders SET status=?,capture_id=?,error=NULL WHERE id=?',(status,cid,o['id']))
                audit(c,'ENTITLEMENT_VERIFIED',o['project'],o['id'],f'{o["mode"]}: capture {cid}; {o["currency"]} {o["amount"]}')
            else:c.execute('UPDATE orders SET status=?,error=NULL WHERE id=?',(status,o['id']))
    def mark_uncertain(o,message):
        with store.connection() as c:
            c.execute('UPDATE orders SET status=?,error=? WHERE id=?',('VERIFYING',message,o['id']))
            audit(c,'PAYMENT_UNCERTAIN',o['project'],o['id'],message)
    def latest_order(oid,who):
        with store.connection() as c:return public_order(order(c,oid,who))

    @app.get('/api/bootstrap')
    def bootstrap(request:Request):
        token=None;s=request.state.session
        if not s:
            token=secrets.token_urlsafe(32);s={'id':digest(token),'csrf':secrets.token_urlsafe(32)}
            with store.connection() as c:c.execute('INSERT INTO sessions VALUES(?,?,?)',(s['id'],s['csrf'],now()))
        result=JSONResponse({'csrf':s['csrf'],'payment_mode':settings.payment_mode,'payment_label':'TEST FIXTURE，非PayPal真实支付' if settings.payment_mode=='fixture' else 'PAYPAL SANDBOX · TEST MONEY ONLY',
            'ai_configured':bool(settings.ai_model),'ai_model':settings.ai_model or None,'price':{'sku':SKU,'amount':PRICE,'currency':CURRENCY},
            'submission_ready':False,'notice':'Real local AI and an actual PayPal Sandbox transaction still require end-to-end verification.'})
        if token:result.set_cookie(COOKIE,token,httponly=True,samesite='lax',max_age=180*86400,path='/')
        return result

    @app.get('/api/projects')
    def projects(request:Request):
        with store.connection() as c:
            rows=c.execute('SELECT * FROM projects WHERE owner=? ORDER BY created DESC',(owner(request),)).fetchall()
            return [view(c,dict(p)) for p in rows]

    @app.post('/api/projects')
    def create_project(body:NewProject,request:Request):
        with store.connection() as c:
            if c.execute('SELECT COUNT(*) FROM projects WHERE owner=?',(owner(request),)).fetchone()[0]>=100:fail(409,'This local session has reached 100 projects. Archive your data folder to start a fresh workspace.')
        try:board,provenance=plan(body.brief,body.planner,settings,ai_client)
        except ValueError as e:fail(422,str(e))
        return save_project(owner(request),body.brief,board,provenance)

    @app.post('/api/projects/import')
    def import_project(body:ImportProject,request:Request):
        return save_project(owner(request),'Restored from a local storyboard file.',body.board,{'provider':'Imported storyboard. Payment rights are never imported.','model':None,'online_model_call':False})

    @app.get('/api/projects/{pid}')
    def get_project(pid:str,request:Request):
        with store.connection() as c:return view(c,project(c,pid,owner(request)))

    @app.put('/api/projects/{pid}')
    def edit_project(pid:str,body:EditProject,request:Request):
        with store.lock,store.connection() as c:
            p=project(c,pid,owner(request))
            if p['current_revision']!=body.expected_revision:fail(409,'This project changed in another tab. Reload before editing.')
            pending=c.execute("SELECT 1 FROM orders WHERE project=? AND revision=? AND status IN ('CREATING','CREATED','APPROVED','VERIFYING','PENDING')",(pid,p['current_revision'])).fetchone()
            if pending:fail(409,'Resolve or cancel the current checkout before editing this revision.')
            old=revision(c,pid,p['current_revision']);rev=p['current_revision']+1;b=pack(body.board.model_dump())
            prov=json.loads(old['provenance']);prov['edited_by_creator']=True
            c.execute('INSERT INTO revisions VALUES(?,?,?,?,?)',(pid,rev,b,pack(prov),digest(b)))
            c.execute('UPDATE projects SET title=?,current_revision=? WHERE id=?',(body.board.title,rev,pid))
            audit(c,'REVISION_SAVED',pid,detail=f'Revision {rev}; prior purchases remain bound to their original revision.')
            return view(c,project(c,pid,owner(request)))

    @app.get('/api/projects/{pid}/source')
    def source(pid:str,request:Request):
        with store.connection() as c:
            p=project(c,pid,owner(request));r=revision(c,pid,p['current_revision'])
            return JSONResponse({'format':'evovid-creator-commerce-v1','board':json.loads(r['board'])},headers={'Content-Disposition':f'attachment; filename="evovid-{pid[:8]}.json"'})

    @app.post('/api/projects/{pid}/preview')
    def preview(pid:str,request:Request):
        with store.connection() as c:
            p=project(c,pid,owner(request));r=revision(c,pid,p['current_revision'])
        target=settings.data_dir/'previews'/f'{pid}-{r["revision"]}.mp4'
        try:render(Board.model_validate_json(r['board']),target,True,settings.payment_mode)
        except (RuntimeError,OSError) as e:fail(503,'Preview render failed. Check FFmpeg and try again. Your storyboard is saved.')
        return {'url':f'/api/media/{pid}/preview?revision={r["revision"]}','revision':r['revision']}

    @app.post('/api/projects/{pid}/exports')
    def export(pid:str,request:Request):
        with store.connection() as c:
            p=project(c,pid,owner(request));r=revision(c,pid,p['current_revision'])
            if not entitled(c,pid,r['revision']):fail(403,'Export is locked. A matching COMPLETED server-verified capture is required.')
        target=settings.data_dir/'exports'/f'{pid}-{r["revision"]}-{settings.payment_mode}.mp4'
        try:render(Board.model_validate_json(r['board']),target,False,settings.payment_mode)
        except (RuntimeError,OSError):fail(503,'Export failed. Your entitlement is saved; retry without another payment.')
        with store.connection() as c:audit(c,'EXPORT_RENDERED',pid,detail=f'Revision {r["revision"]}; SHA256 {hashlib.sha256(target.read_bytes()).hexdigest()}')
        return {'url':f'/api/media/{pid}/export?revision={r["revision"]}','revision':r['revision'],'bytes':target.stat().st_size,'mode':settings.payment_mode}

    @app.get('/api/media/{pid}/{kind}')
    def media(pid:str,kind:str,revision:int,request:Request):
        if kind not in ('preview','export'):fail(404,'Unknown media type.')
        with store.connection() as c:
            project(c,pid,owner(request));r=c.execute('SELECT 1 FROM revisions WHERE project=? AND revision=?',(pid,revision)).fetchone()
            if not r:fail(404,'Unknown revision.')
            if kind=='export' and not entitled(c,pid,revision):fail(403,'This revision is locked.')
        path=settings.data_dir/('previews' if kind=='preview' else 'exports')/(f'{pid}-{revision}.mp4' if kind=='preview' else f'{pid}-{revision}-{settings.payment_mode}.mp4')
        if not path.is_file():fail(404,'Render this file first.')
        return FileResponse(path,media_type='video/mp4',filename=f'evovid-{pid[:8]}-r{revision}-{kind}.mp4',content_disposition_type='inline' if kind=='preview' else 'attachment')

    @app.post('/api/checkout/orders')
    def checkout(body:Checkout,request:Request):
        who=owner(request)
        with store.lock:
            with store.connection() as c:
                p=project(c,body.project_id,who)
                if p['current_revision']!=body.revision:fail(409,'Checkout revision is stale. Refresh the project.')
                old=c.execute('SELECT * FROM orders WHERE project=? AND revision=? AND mode=?',(p['id'],body.revision,settings.payment_mode)).fetchone()
                if old:
                    o=dict(old)
                    if o['paypal_id']:return public_order(o)
                    # Unknown creates never get a fresh key. Stop instead of risk replay beyond a conservative window.
                    if (datetime.now(timezone.utc)-datetime.fromisoformat(o['created'])).total_seconds()>300:fail(409,'Uncertain order creation is over five minutes old. Inspect the existing Sandbox order before retrying; this app will not create a second charge.')
                else:
                    oid=uid();merchant=settings.paypal_merchant_id if settings.payment_mode=='sandbox' else 'TEST-FIXTURE-MERCHANT'
                    c.execute('INSERT INTO orders(id,owner,project,revision,mode,sku,amount,currency,merchant,status,create_key,capture_key,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (oid,who,p['id'],body.revision,settings.payment_mode,SKU,PRICE,CURRENCY,merchant,'CREATING',str(uuid.uuid4()),str(uuid.uuid4()),now()))
                    audit(c,'ORDER_CREATED',p['id'],oid,f'{settings.payment_mode}; {CURRENCY} {PRICE}; revision {body.revision}')
                    o=order(c,oid,who)
            try:
                pp_id,approval_url=payments.create(o)
                with store.connection() as c:c.execute('UPDATE orders SET paypal_id=?,approval_url=?,status=?,error=NULL WHERE id=?',(pp_id,approval_url,'CREATED',o['id']))
            except PaymentUnavailable as exc:mark_uncertain(o,str(exc))
            return latest_order(o['id'],who)

    @app.get('/api/orders/{oid}')
    def get_order(oid:str,request:Request):return latest_order(oid,owner(request))

    @app.post('/api/orders/{oid}/cancel')
    def cancel(oid:str,request:Request):
        with store.lock,store.connection() as c:
            o=order(c,oid,owner(request))
            # Cancellation never overwrites evidence that a capture may have succeeded.
            if o['status'] in ('VERIFYING','PENDING'):fail(409,'Payment is uncertain or pending. Reconcile it before cancelling or editing.')
            if o['status'] not in ('COMPLETED','REJECTED'):
                c.execute('UPDATE orders SET status=?,error=NULL WHERE id=?',('CANCELED',oid));audit(c,'CHECKOUT_CANCELED',o['project'],oid)
            return public_order(order(c,oid,owner(request)))

    def reconcile_order(oid,who,do_capture=False):
        with store.lock:
            with store.connection() as c:o=order(c,oid,who)
            if o['status'] in ('COMPLETED','REJECTED'):return public_order(o)
            if not o['paypal_id']:fail(409,'Order creation is uncertain. Resume the same checkout; do not create a new project to retry payment.')
            try:
                remote=payments.get(o)
                if remote.get('id')!=o['paypal_id']:raise PaymentRejected('Remote order identity mismatch.')
                existing_captures=any(u.get('payments',{}).get('captures') for u in remote.get('purchase_units',[]))
                if remote.get('status')=='APPROVED' and do_capture and settings.payment_mode=='sandbox' and not existing_captures:
                    verify_order_identity(o,remote)
                    with store.connection() as c:c.execute('UPDATE orders SET status=? WHERE id=?',('VERIFYING',oid))
                    # Stable capture key is persisted before the request. Reconcile first on every retry.
                    payments.capture(o)
                    # Query the full authoritative order representation after capture.
                    remote=payments.get(o)
                units=remote.get('purchase_units',[])
                has_captures=any(u.get('payments',{}).get('captures') for u in units)
                if has_captures or remote.get('status')=='COMPLETED':apply_result(o,remote)
                else:
                    status=remote.get('status')
                    safe=status if status in ('CREATED','APPROVED','VOIDED') else 'VERIFYING'
                    with store.connection() as c:c.execute('UPDATE orders SET status=?,error=NULL WHERE id=?',(safe,oid))
            except PaymentRejected as exc:
                with store.connection() as c:c.execute('UPDATE orders SET status=?,error=? WHERE id=?',('REJECTED',str(exc),oid))
            except PaymentUnavailable as exc:mark_uncertain(o,str(exc))
            return latest_order(oid,who)

    @app.post('/api/orders/{oid}/reconcile')
    def reconcile(oid:str,request:Request):return reconcile_order(oid,owner(request))

    @app.post('/api/orders/{oid}/capture')
    def capture(oid:str,request:Request):
        if settings.payment_mode!='sandbox':fail(409,'This endpoint requires Sandbox mode. The fixture has a separately labeled control.')
        return reconcile_order(oid,owner(request),True)

    @app.post('/api/orders/{oid}/fixture')
    def fixture(oid:str,body:FixtureAction,request:Request):
        if settings.payment_mode!='fixture':fail(404,'Test fixtures are unavailable in Sandbox mode.')
        with store.lock:
            with store.connection() as c:o=order(c,oid,owner(request))
            if o['status'] in ('COMPLETED','REJECTED'):return public_order(o)
            remote=FixturePayments.response(o,body.scenario)
            with store.connection() as c:c.execute('UPDATE orders SET fixture_remote=? WHERE id=?',(pack(remote),oid))
            if body.scenario=='lost-response':mark_uncertain(o,'TEST FIXTURE: capture completed but response was lost. Reconcile the same order.')
            else:apply_result(o,remote)
            return latest_order(oid,owner(request))

    @app.get('/api/projects/{pid}/evidence')
    def evidence(pid:str,request:Request):
        with store.connection() as c:
            p=project(c,pid,owner(request));v=view(c,p)
            events=[dict(x) for x in c.execute('SELECT action,order_id,detail,created FROM audit WHERE project=? ORDER BY id',(pid,)).fetchall()]
            return {'project':v,'events':events,'verification_scope':'Local application evidence. Fixture runs are not real PayPal Sandbox transactions. No account/credential creation, publication or contest submission was performed.'}

    @app.get('/api/health')
    def health(request:Request):return {'ok':True,'payment_mode':settings.payment_mode,'production_payments':False}

    @app.get('/')
    def index():return FileResponse(ROOT/'static'/'index.html')
    app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
    return app
