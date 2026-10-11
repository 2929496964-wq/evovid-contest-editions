"""Local-first Taste Director API: session isolation, bounded jobs and explicit live mode."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
import copy, hashlib, json, os, re, threading, time
from urllib.parse import urlsplit
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .models import Search, Plan, Edit, Render
from .qloo import Qloo, ProviderError, now
from .planner import plan as make_plan
from .render import render, ffmpeg_path
from .store import Store

ROOT = Path(__file__).resolve().parent.parent
ID = re.compile(r'^[0-9a-f]{32}$')

def create_app(home=None, provider=None, allowed_hosts=None):
    source_hash = hashlib.sha256()
    for source in sorted([*ROOT.joinpath('taste').glob('*.py'), *ROOT.joinpath('static').glob('*')]):
        if source.is_file(): source_hash.update(source.name.encode() + source.read_bytes())
    build_id = source_hash.hexdigest()[:16]
    store = Store(home or ROOT / '.taste-data')
    provider = provider or Qloo(os.environ.get('QLOO_API_KEY', ''), hourly_limit=max(1, min(1000, int(os.environ.get('QLOO_HOURLY_LIMIT', '100')))))
    pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='taste')
    tasks, task_lock = {}, threading.RLock()
    search_windows = {}
    secure_cookie = os.environ.get('TASTE_SECURE_COOKIE') == '1'
    @asynccontextmanager
    async def lifespan(app):
        yield
        for flag in tasks.values(): flag.set()
        pool.shutdown(wait=True, cancel_futures=True)
    app = FastAPI(title='EvoVid Taste Director', docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.store, app.state.provider = store, provider
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts or ['127.0.0.1', 'localhost', '[::1]'])
    @app.middleware('http')
    async def boundaries(request, call_next):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            origin = request.headers.get('origin')
            if origin:
                parts = urlsplit(origin)
                if parts.netloc != request.headers.get('host') or parts.scheme not in ('http', 'https'):
                    return JSONResponse({'detail': 'Cross-origin requests are blocked.'}, status_code=403)
            if request.headers.get('x-taste-client') != '1':
                return JSONResponse({'detail': 'A same-origin application request is required.'}, status_code=403)
            length = request.headers.get('content-length')
            if length is None: return JSONResponse({'detail': 'Content-Length is required.'}, status_code=411)
            if not length.isdigit() or int(length) > 65536:
                return JSONResponse({'detail': 'Request body exceeds 64 KiB.'}, status_code=413)
        if request.url.path.startswith('/api/'):
            try:
                owner = store.session(request.cookies.get('taste_session'))
            except ValueError as exc:
                return JSONResponse({'detail': str(exc)}, status_code=429)
            request.state.owner = owner
        response = await call_next(request)
        if request.url.path.startswith('/api/'):
            if owner != request.cookies.get('taste_session'):
                response.set_cookie('taste_session', owner, httponly=True, samesite='strict', secure=secure_cookie, max_age=60*60*24*30)
            response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
    @app.exception_handler(ProviderError)
    async def provider_error(request, exc):
        return JSONResponse({'detail': exc.message, 'code': exc.code, 'fixture_fallback': False}, status_code=exc.status)
    def owned(i, owner):
        if not ID.fullmatch(i): raise HTTPException(404, 'Project not found.')
        job = store.get(i, owner)
        if not job: raise HTTPException(404, 'Project not found.')
        return job
    def start(i, function):
        with task_lock:
            flag = threading.Event()
            tasks[i] = flag
        def work():
            try:
                with task_lock:
                    if flag.is_set(): raise InterruptedError('Cancelled.')
                    store.update(i, 'running')
                result = function(flag.is_set)
                with task_lock:
                    if flag.is_set(): raise InterruptedError('Cancelled.')
                    store.update(i, 'complete', result)
            except InterruptedError:
                (store.home / 'exports' / f'{i}.mp4').unlink(missing_ok=True)
                store.update(i, 'cancelled', error='Cancelled. You can retry explicitly; no successful result was claimed.')
            except ProviderError as exc:
                store.event(i, 'failure', {'code': exc.code, 'message': exc.message, 'fixture_fallback': False})
                store.update(i, 'failed', error=exc.message)
            except Exception:
                # Never return upstream bodies, exception repr, headers, env or filesystem paths.
                store.update(i, 'failed', error='The operation could not finish safely. Check the runtime requirements and retry. No fallback result was used.')
            finally:
                with task_lock: tasks.pop(i, None)
        pool.submit(work)
    @app.get('/')
    def index(): return FileResponse(ROOT / 'static' / 'index.html')
    @app.get('/static/{name}')
    def static(name: str):
        if name not in ('app.js', 'style.css'): raise HTTPException(404)
        return FileResponse(ROOT / 'static' / name)
    @app.get('/api/state')
    def state(request: Request):
        try: ffmpeg_path(); renderer = True
        except RuntimeError: renderer = False
        return {'app': 'EvoVid Taste Director', 'version': '1.0.0', 'build_id': build_id, 'default_mode': 'demo', 'live_configured': bool(provider.key),
                'live_verified': False, 'renderer_available': renderer,
                'disclosure': 'DEMO uses synthetic fixtures; LIVE requires a server-side authorized key. Configuration is not proof of live verification.',
                'projects': store.list(request.state.owner)}
    @app.post('/api/search')
    def search(payload: Search, request: Request):
        owner = request.state.owner
        with task_lock:
            stamps = [x for x in search_windows.get(owner, []) if x > time.monotonic()-60]
            if len(stamps) >= 15: raise HTTPException(429, 'Search limit reached. Wait one minute.')
            search_windows[owner] = stamps + [time.monotonic()]
        trace = []
        values = provider.search(payload.query, payload.category, payload.mode, trace.append)
        saved = [{**x, 'search_provenance': trace} for x in values]
        store.candidates(owner, payload.mode, saved)
        return {'mode': payload.mode, 'source': 'demo_fixture' if payload.mode == 'demo' else 'live_http', 'candidates': values, 'trace': trace}
    @app.post('/api/plans', status_code=202)
    def create_plan(payload: Plan, request: Request):
        owner = request.state.owner
        provider.ready(payload.mode)
        try: refs = store.resolve(owner, payload.mode, payload.entity_ids)
        except ValueError as exc: raise HTTPException(422, str(exc)) from None
        old = None
        if payload.parent_id:
            old = owned(payload.parent_id, owner)
            if old['kind'] != 'plan' or old['status'] != 'complete': raise HTTPException(409, 'Replanning requires a completed project.')
        data = payload.model_dump()
        try: i, fresh = store.create(owner, 'plan', data)
        except ValueError as exc: raise HTTPException(409 if 'Idempotency' in str(exc) else 429, str(exc)) from None
        if fresh:
            store.event(i, 'references_confirmed', {'build_id': build_id, 'mode': payload.mode, 'ids': payload.entity_ids, 'search_provenance': [r['search_provenance'] for r in refs]})
            if old:
                store.event(i, 'feedback_replan', {'previous_run': old['id'], 'previous_reference_ids': old['request']['entity_ids'],
                                                  'new_reference_ids': payload.entity_ids, 'previous_pace': old['request']['pace'], 'new_pace': payload.pace})
            def execute(stop):
                store.event(i, 'agent_tool_selection', {'tools': ['Qloo movie insights', 'Qloo media-tag insights'] if payload.mode == 'live' else ['Explicit synthetic fixture insights'], 'goal_sent_to_qloo': False})
                evidence = provider.insights(payload.entity_ids, payload.mode, lambda row: store.event(i, 'provider_trace', row), stop)
                if stop(): raise InterruptedError()
                doc = make_plan(data, [{k: v for k, v in r.items() if k != 'search_provenance'} for r in refs], evidence)
                doc['build_id'] = build_id
                store.event(i, 'constraint_check', {'shots': 4, 'duration': sum(s['seconds'] for s in doc['scenes']), 'budget': payload.budget, 'passed': True})
                if old:
                    doc['comparison'] = {'previous_run': old['id'], 'before': old['result']['briefs'][old['result']['brief_index']]['theme'], 'after': doc['briefs'][0]['theme'],
                                         'reference_changed': old['request']['entity_ids'] != payload.entity_ids,
                                         'note': 'The new evidence was requested again; the provider may still return overlapping cultural associations.'}
                return doc
            start(i, execute)
        return {'id': i, 'deduplicated': not fresh}
    @app.get('/api/jobs/{i}')
    def get_job(i: str, request: Request):
        job = owned(i, request.state.owner)
        return {**job, 'events': store.events(i)}
    @app.post('/api/jobs/{i}/cancel')
    def cancel(i: str, request: Request):
        job = owned(i, request.state.owner)
        with task_lock:
            if job['status'] in ('queued', 'running'):
                flag = tasks.get(i)
                if flag: flag.set()
                store.event(i, 'cancel_requested', {'note': 'An in-flight HTTP request can take up to its timeout to return.'})
        return {'status': 'cancel_requested' if job['status'] in ('queued', 'running') else job['status']}
    @app.patch('/api/projects/{i}')
    def save(i: str, payload: Edit, request: Request):
        owned(i, request.state.owner)
        try: doc = store.edit(i, request.state.owner, payload.model_dump())
        except ValueError as exc: raise HTTPException(409, str(exc)) from None
        store.event(i, 'user_edit', {'version': doc['version'], 'brief_index': doc['brief_index']})
        return doc
    @app.post('/api/projects/{i}/render', status_code=202)
    def create_render(i: str, payload: Render, request: Request):
        job = owned(i, request.state.owner)
        if job['kind'] != 'plan' or job['status'] != 'complete': raise HTTPException(409, 'Complete a plan before rendering.')
        if payload.version != job['result']['version']: raise HTTPException(409, 'Reload the current project version before rendering.')
        try: ffmpeg_path()
        except RuntimeError as exc: raise HTTPException(503, str(exc)) from None
        snapshot = copy.deepcopy(job['result'])
        try: rid, fresh = store.create(request.state.owner, 'render', payload.model_dump(), i)
        except ValueError as exc: raise HTTPException(409 if 'Idempotency' in str(exc) else 429, str(exc)) from None
        if fresh:
            store.event(rid, 'render_snapshot', {'project': i, 'version': snapshot['version'], 'mode': snapshot['mode'], 'renderer': 'Pillow + FFmpeg', 'neural_video': False})
            def execute(stop):
                output = render(snapshot, store.home / 'exports' / f'{rid}.mp4', stop, lambda row: store.event(rid, 'render_progress', row))
                return {**output, 'project_version': snapshot['version'], 'mode': snapshot['mode'], 'url': f'/api/exports/{rid}.mp4'}
            start(rid, execute)
        return {'id': rid, 'deduplicated': not fresh}
    @app.get('/api/exports/{rid}.mp4')
    def video(rid: str, request: Request):
        job = owned(rid, request.state.owner)
        if job['kind'] != 'render' or job['status'] != 'complete': raise HTTPException(404, 'A completed export is required.')
        target = store.home / 'exports' / f'{rid}.mp4'
        if not target.is_file(): raise HTTPException(404, 'This export file is missing. Render it again.')
        return FileResponse(target, media_type='video/mp4', filename=f'evovid-taste-{rid[:8]}.mp4')
    @app.get('/api/projects/{i}/export/{kind}')
    def export(i: str, kind: str, request: Request):
        job = owned(i, request.state.owner)
        if job['kind'] != 'plan' or job['status'] != 'complete': raise HTTPException(409, 'A completed project is required.')
        doc = job['result']
        if kind == 'json':
            return Response(json.dumps({'project': doc, 'trace': store.events(i)}, ensure_ascii=False, indent=2), media_type='application/json', headers={'Content-Disposition': f'attachment; filename="taste-{i[:8]}.json"'})
        if kind == 'md':
            brief = doc['briefs'][doc['brief_index']]
            lines = ['# ' + doc['title'], '', '**' + ('DEMO FIXTURE: no Qloo API calls.' if doc['mode'] == 'demo' else 'LIVE Qloo evidence; EvoVid creative interpretation.') + '**', '', brief['logline'], '', '## Creative direction', brief['visual_direction'], brief['sound_direction'], '', '## Storyboard']
            for n, scene in enumerate(doc['scenes'], 1): lines.extend([f"### {n}. {scene['title']} ({scene['seconds']}s / {scene['camera']})", scene['caption'], 'Evidence: ' + ', '.join(scene['evidence_ids']), ''])
            lines.extend(['## Cultural evidence', *[f"- {e['name']} ({e['id']})" for e in doc['evidence']['entities']+doc['evidence']['tags']], '', '## Disclosure', *doc['disclosures']])
            return Response('\n'.join(lines), media_type='text/markdown', headers={'Content-Disposition': f'attachment; filename="taste-{i[:8]}.md"'})
        raise HTTPException(404)
    return app
