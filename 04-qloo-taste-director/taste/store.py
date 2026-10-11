"""SQLite project/event store adapted from MIT EvoVid Pocket's Store design."""
from pathlib import Path
import json, sqlite3, time, uuid, threading

class Store:
    def __init__(self, home):
        self.home = Path(home).resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.db = self.home / 'taste.sqlite3'
        self.lock = threading.RLock()
        with self.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created REAL);
            CREATE TABLE IF NOT EXISTS candidates (owner TEXT, mode TEXT, entity_id TEXT, data TEXT, PRIMARY KEY(owner,mode,entity_id));
            CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, owner TEXT, kind TEXT, project_id TEXT, request_id TEXT,
                created REAL, updated REAL, status TEXT, request TEXT, result TEXT, error TEXT,
                UNIQUE(owner,request_id));
            CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, at REAL, kind TEXT, detail TEXT);
            ''')
            c.execute("UPDATE jobs SET status='interrupted', error='The server restarted. Retry explicitly to continue.' WHERE status IN ('running','queued')")
    def connect(self):
        c = sqlite3.connect(self.db, timeout=15)
        c.row_factory = sqlite3.Row
        return c
    def session(self, token):
        with self.lock, self.connect() as c:
            if token and c.execute('SELECT 1 FROM sessions WHERE id=?', (token,)).fetchone(): return token
            if c.execute('SELECT count(*) FROM sessions').fetchone()[0] >= 1000: raise ValueError('Session capacity reached. The operator must clean up expired local demo data.')
            import secrets
            token = secrets.token_urlsafe(32)
            c.execute('INSERT INTO sessions VALUES (?,?)', (token, time.time()))
            return token
    def candidates(self, owner, mode, values):
        with self.lock, self.connect() as c:
            for item in values:
                c.execute('INSERT OR REPLACE INTO candidates VALUES (?,?,?,?)', (owner, mode, item['id'], json.dumps(item)))
    def resolve(self, owner, mode, ids):
        with self.connect() as c:
            values = [c.execute('SELECT data FROM candidates WHERE owner=? AND mode=? AND entity_id=?', (owner, mode, i)).fetchone() for i in ids]
        if not all(values): raise ValueError('Search and explicitly choose every reference in this mode before planning.')
        return [json.loads(r[0]) for r in values]
    def create(self, owner, kind, request, project_id=None):
        with self.lock, self.connect() as c:
            old = c.execute('SELECT id,kind,project_id,request FROM jobs WHERE owner=? AND request_id=?', (owner, request['request_id'])).fetchone()
            if old:
                if old['kind'] != kind or old['project_id'] != project_id or json.loads(old['request']) != request:
                    raise ValueError('Idempotency key conflict: reuse a request key only for the identical operation.')
                return old['id'], False
            if c.execute("SELECT count(*) FROM jobs WHERE owner=? AND status IN ('queued','running')", (owner,)).fetchone()[0] >= 2:
                raise ValueError('Two operations are already active. Cancel or wait before starting another.')
            if c.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0] >= 12:
                raise ValueError('The local queue is full. Try again after an operation completes.')
            if c.execute('SELECT count(*) FROM jobs').fetchone()[0] >= 2000:
                raise ValueError('This local instance has reached its 2000-run storage bound. The operator must archive application data before continuing.')
            if c.execute('SELECT count(*) FROM jobs WHERE owner=?', (owner,)).fetchone()[0] >= 100:
                raise ValueError('This browser has reached its local limit of 100 runs.')
            i, t = uuid.uuid4().hex, time.time()
            c.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)', (i, owner, kind, project_id, request['request_id'], t, t, 'queued', json.dumps(request), None, None))
            return i, True
    def get(self, i, owner=None):
        with self.connect() as c:
            row = c.execute('SELECT * FROM jobs WHERE id=?' + (' AND owner=?' if owner else ''), (i, owner) if owner else (i,)).fetchone()
        if not row: return None
        d = dict(row)
        d.pop('owner')
        for key in ('request', 'result'): d[key] = json.loads(d[key]) if d[key] else None
        return d
    def list(self, owner):
        with self.connect() as c:
            ids = [r[0] for r in c.execute('SELECT id FROM jobs WHERE owner=? ORDER BY created DESC LIMIT 100', (owner,))]
        return [self.get(i, owner) for i in ids]
    def update(self, i, status, result=None, error=None):
        with self.lock, self.connect() as c:
            c.execute('UPDATE jobs SET updated=?,status=?,result=?,error=? WHERE id=?', (time.time(), status, json.dumps(result) if result is not None else None, error, i))
    def edit(self, i, owner, edit):
        with self.lock, self.connect() as c:
            row = c.execute("SELECT result FROM jobs WHERE id=? AND owner=? AND kind='plan' AND status='complete'", (i, owner)).fetchone()
            if not row: raise ValueError('A completed project is required.')
            doc = json.loads(row[0])
            if doc['version'] != edit['version']: raise ValueError('This project changed in another tab. Reload before saving.')
            if sum(s['seconds'] for s in edit['scenes']) != doc['constraints']['duration']: raise ValueError('Shot durations must add up to the project duration.')
            valid = {e['id'] for e in doc['evidence']['entities'] + doc['evidence']['tags']}
            if any(x not in valid for s in edit['scenes'] for x in s['evidence_ids']): raise ValueError('A scene cites evidence that was not returned for this run.')
            doc.update({k: edit[k] for k in ('brief_index', 'title', 'scenes')})
            doc['version'] += 1
            c.execute('UPDATE jobs SET result=?, updated=? WHERE id=?', (json.dumps(doc), time.time(), i))
        return doc
    def event(self, i, kind, detail):
        with self.lock, self.connect() as c:
            c.execute('INSERT INTO events(job_id,at,kind,detail) VALUES (?,?,?,?)', (i, time.time(), kind, json.dumps(detail)))
    def events(self, i):
        with self.connect() as c: rows = c.execute('SELECT * FROM events WHERE job_id=? ORDER BY seq', (i,)).fetchall()
        return [{**dict(r), 'detail': json.loads(r['detail'])} for r in rows]
