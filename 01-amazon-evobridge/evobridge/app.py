"""Loopback-only HTTP app, persistent projects and cancellable render jobs."""
import base64
import copy
import hashlib
import io
import json
import re
import secrets
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from PIL import Image, ImageOps, UnidentifiedImageError
from . import model
from .job_store import Store
from .render import render

ROOT = Path(__file__).resolve().parent.parent
MAX_BODY = 12 * 1024 * 1024
ID = re.compile(r'^[a-f0-9]{32}$')


class App:
    def __init__(self, home):
        self.home = Path(home).resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.assets = self.home / 'assets'
        self.outputs = self.home / 'outputs'
        self.assets.mkdir(exist_ok=True)
        self.outputs.mkdir(exist_ok=True)
        self.store = Store(self.home)
        self.lock = threading.RLock()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='render')
        self.events = {}
        self.token = secrets.token_urlsafe(32)
        with self.store.connect() as c:
            c.executescript('CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, updated REAL, body TEXT); CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, name TEXT, width INT, height INT);')
            c.execute("UPDATE jobs SET status='interrupted', error='Application stopped. Please retry explicitly.' WHERE status IN ('queued','running')")
        for partial in self.outputs.glob('*.partial.mp4'):
            partial.unlink(missing_ok=True)
        if not self.projects():
            self.save(model.new_project())

    def save(self, project):
        with self.store.connect() as c:
            c.execute('INSERT OR REPLACE INTO projects VALUES(?,?,?)', (project['id'], time.time(), json.dumps(project, ensure_ascii=False)))

    def projects(self):
        with self.store.connect() as c:
            return [json.loads(r['body']) for r in c.execute('SELECT body FROM projects ORDER BY updated DESC LIMIT 100')]

    def project(self, pid):
        if not isinstance(pid, str) or not ID.fullmatch(pid):
            raise ValueError('Invalid project ID.')
        with self.store.connect() as c:
            row = c.execute('SELECT body FROM projects WHERE id=?', (pid,)).fetchone()
        if not row:
            raise KeyError('Project not found.')
        return json.loads(row['body'])

    def asset_list(self):
        with self.store.connect() as c:
            return [dict(r) for r in c.execute('SELECT * FROM assets ORDER BY rowid DESC LIMIT 100')]

    def asset_upload(self, body):
        name = model.short(str(body.get('name', 'Image')), 120)
        try:
            raw = base64.b64decode(body.get('data', ''), validate=True)
            if not 0 < len(raw) <= 8 * 1024 * 1024:
                raise ValueError('Image must be smaller than 8 MB.')
            with Image.open(io.BytesIO(raw)) as src:
                if src.format not in ('JPEG', 'PNG', 'WEBP') or src.width * src.height > 20_000_000:
                    raise ValueError('Use a JPEG, PNG or WebP under 20 megapixels.')
                im = ImageOps.exif_transpose(src).convert('RGB')
                im.thumbnail((2048, 2048))
                aid = uuid.uuid4().hex
                im.save(self.assets / (aid + '.jpg'), 'JPEG', quality=90)
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
            raise ValueError('Could not read this image. Try a JPEG, PNG or WebP.') from e
        # Names are display data only, never filesystem paths.
        with self.store.connect() as c:
            c.execute('INSERT INTO assets VALUES(?,?,?,?)', (aid, name, im.width, im.height))
        return {'id': aid, 'name': name, 'width': im.width, 'height': im.height}

    def start_render(self, body):
        with self.lock:
            p = self.project(body.get('project_id'))
            if body.get('confirmed') is not True:
                raise ValueError('Review and confirm the render first.')
            if body.get('revision') != p['revision']:
                raise ValueError('Storyboard changed. Review the latest revision before rendering.')
            if not p['scenes']:
                raise ValueError('Create a storyboard first.')
            fingerprint = hashlib.sha256(json.dumps({k: p[k] for k in ('id', 'revision', 'scenes', 'format', 'duration')}, sort_keys=True).encode()).hexdigest()
            for job in self.store.list():
                if job['request'].get('fingerprint') == fingerprint and job['status'] in ('queued', 'running', 'done'):
                    return job
            jid = self.store.create({'project_id': p['id'], 'fingerprint': fingerprint, 'project': copy.deepcopy(p)})
            event = threading.Event()
            self.events[jid] = event
            self.store.event(jid, 'confirmed', {'revision': p['revision'], 'duration': p['duration']})
            self.pool.submit(self.run_job, jid, p, event)
            return self.store.get(jid)

    def run_job(self, jid, p, event):
        if event.is_set():
            self.store.update(jid, 'cancelled')
            return
        self.store.update(jid, 'running', {'progress': 0})
        try:
            target = self.outputs / (jid + '.mp4')
            render(p, target, self.assets, stop=event.is_set, progress=lambda n: self.store.update(jid, 'running', {'progress': n}))
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            manifest = {'project': p, 'job_id': jid, 'sha256': digest, 'bytes': target.stat().st_size, 'format': p['format'], 'duration': p['duration'], 'renderer': 'Pillow motion graphics + FFmpeg H.264; no neural model'}
            (self.outputs / (jid + '.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            self.store.update(jid, 'done', {'progress': 100, 'url': '/outputs/' + jid + '.mp4', 'manifest': '/outputs/' + jid + '.json', 'sha256': digest, 'bytes': target.stat().st_size, 'duration': p['duration']})
            self.store.event(jid, 'completed', {'sha256': digest})
        except InterruptedError as e:
            self.store.update(jid, 'cancelled', error=str(e))
        except Exception as e:
            self.store.update(jid, 'failed', error=str(e)[:500])
        finally:
            self.events.pop(jid, None)

    def mutate(self, path, body):
        with self.lock:
            if path == '/api/projects':
                p = model.new_project()
                self.save(p)
                return {'project': p}
            if path == '/api/import':
                saved = body.get('project')
                if not isinstance(saved, dict) or not isinstance(saved.get('scenes'), list) or len(saved['scenes']) != 3:
                    raise ValueError('Import an EvoBridge JSON with exactly three scenes.')
                p = model.new_project()
                model.build(p, saved.get('theme'), saved.get('audience'), 6, saved.get('tone'))
                model.edit(p, {'format': saved.get('format', 'landscape')})
                for i, scene in enumerate(saved['scenes']):
                    if not isinstance(scene, dict):
                        raise ValueError('Invalid imported scene.')
                    patch = {key: scene[key] for key in ('title', 'caption', 'seconds', 'color', 'motion') if key in scene}
                    model.edit(p, {'scene': i, **patch})
                p['history'] = []
                p['messages'] = [{'role': 'assistant', 'text': 'Storyboard restored as a new local project. Reattach image assets if needed. / 分镜已恢复为新项目，请重新添加图片素材。'}]
                self.save(p)
                return {'project': p}
            if path == '/api/assets':
                return {'asset': self.asset_upload(body)}
            if path == '/api/render':
                return {'job': self.start_render(body)}
            if path == '/api/cancel':
                jid = body.get('job_id')
                if not isinstance(jid, str) or not ID.fullmatch(jid):
                    raise ValueError('Invalid job ID.')
                j = self.store.get(jid)
                if not j:
                    raise KeyError('Job not found.')
                if j['status'] in ('queued', 'running') and jid in self.events:
                    self.events[jid].set()
                    self.store.event(jid, 'cancel_requested', {})
                return {'job': self.store.get(jid)}
            p = self.project(body.get('project_id'))
            if path == '/api/brief':
                model.build(p, body.get('theme'), body.get('audience'), body.get('duration'), body.get('tone'))
                p['messages'].append({'role': 'assistant', 'text': 'Three-scene template ready. Edit, reorder or upload your own image. / 三段分镜已生成，可编辑、排序或上传自己的图片。'})
                result = {}
            elif path == '/api/command':
                _, action = model.command(p, body.get('text'))
                result = {'action': action}
            elif path == '/api/edit':
                if body.get('revision') != p['revision']:
                    raise ValueError('This edit is stale. Refresh and try again.')
                patch = body.get('patch')
                if not isinstance(patch, dict):
                    raise ValueError('Invalid edit.')
                if patch.get('asset') and (not isinstance(patch['asset'], str) or not ID.fullmatch(patch['asset'])):
                    raise ValueError('Invalid asset ID.')
                if patch.get('asset') and not (self.assets / (patch['asset'] + '.jpg')).is_file():
                    raise ValueError('Asset does not exist.')
                model.edit(p, patch)
                result = {}
            elif path == '/api/undo':
                model.undo(p)
                result = {}
            else:
                raise KeyError('Unknown endpoint.')
            self.save(p)
            return {**result, 'project': p}


def server(home, port=8711):
    app = App(home)

    class Handler(BaseHTTPRequestHandler):
        server_version = 'EvoBridge/1.0'

        def log_message(self, *_):
            pass

        def trusted(self):
            allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            if self.headers.get('Host') not in allowed:
                return False
            origin = self.headers.get('Origin')
            return not origin or origin in {'http://' + h for h in allowed}

        def reply(self, status, payload):
            raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            if not self.trusted() or not secrets.compare_digest(self.headers.get('X-EvoBridge-Token', ''), app.token):
                return self.reply(403, {'error': 'Same-origin session required.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length <= 0 or length > MAX_BODY:
                    return self.reply(413, {'error': 'Request is too large or empty.'})
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    return self.reply(415, {'error': 'Use application/json.'})
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError('Expected a JSON object.')
                self.reply(200, app.mutate(urlsplit(self.path).path, body))
            except (ValueError, TypeError) as e:
                self.reply(400, {'error': str(e)[:500]})
            except KeyError as e:
                self.reply(404, {'error': str(e)})
            except Exception:
                self.reply(500, {'error': 'Local operation failed. Your existing saved project is safe; retry or inspect the console.'})

        def do_GET(self):
            if not self.trusted():
                return self.reply(403, {'error': 'Loopback origin required.'})
            path = unquote(urlsplit(self.path).path)
            if path == '/api/state':
                return self.reply(200, {'token': app.token, 'projects': app.projects(), 'jobs': app.store.list(), 'assets': app.asset_list()})
            if path == '/api/health':
                return self.reply(200, {'ok': True, 'mode': 'Alexa+ experience simulation', 'version': '1.0.0'})
            if path.startswith('/outputs/'):
                name = path[len('/outputs/'):]
                if not re.fullmatch(r'[a-f0-9]{32}\.(mp4|json)', name):
                    return self.reply(404, {'error': 'File not found.'})
                target = app.outputs / name
                mime = 'video/mp4' if name.endswith('.mp4') else 'application/json'
            elif path.startswith('/assets/'):
                name = path[len('/assets/'):]
                if not re.fullmatch(r'[a-f0-9]{32}\.jpg', name):
                    return self.reply(404, {'error': 'File not found.'})
                target, mime = app.assets / name, 'image/jpeg'
            else:
                files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8')}
                if path not in files:
                    return self.reply(404, {'error': 'Not found.'})
                name, mime = files[path]
                target = ROOT / 'static' / name
            if not target.is_file():
                return self.reply(404, {'error': 'File not found.'})
            size, start, end, status = target.stat().st_size, 0, target.stat().st_size - 1, 200
            header = self.headers.get('Range')
            if header:
                match = re.fullmatch(r'bytes=(\d+)-(\d*)', header)
                if not match:
                    return self.reply(416, {'error': 'Unsupported range.'})
                start = int(match[1])
                end = min(int(match[2]) if match[2] else end, end)
                if start > end:
                    return self.reply(416, {'error': 'Invalid range.'})
                status = 206
            self.send_response(status)
            for key, value in {'Content-Type': mime, 'Content-Length': str(end - start + 1), 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'", 'Referrer-Policy': 'no-referrer'}.items():
                self.send_header(key, value)
            if status == 206:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            try:
                with target.open('rb') as file:
                    file.seek(start)
                    remaining = end - start + 1
                    while remaining:
                        chunk = file.read(min(65536, remaining))
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    httpd = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    httpd.app = app
    return httpd
