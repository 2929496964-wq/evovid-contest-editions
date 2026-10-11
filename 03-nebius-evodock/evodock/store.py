"""EvoVid-derived SQLite store, persistent revisions, jobs and conservative quotas."""
import hashlib, json, sqlite3, threading, time, uuid
from pathlib import Path

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':'))
def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()
class Conflict(Exception): pass
class BudgetExceeded(Exception): pass
class Store:
    def __init__(self, home):
        self.home = Path(home); self.home.mkdir(parents=True, exist_ok=True)
        self.db = self.home/'evodock.sqlite3'; self.lock = threading.RLock()
        with self.connect() as c:
            c.executescript('''
              CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, created REAL, brief TEXT, mode TEXT, revision INTEGER DEFAULT 0);
              CREATE TABLE IF NOT EXISTS revisions(project TEXT, number INTEGER, at REAL, board TEXT, source TEXT, instruction TEXT, PRIMARY KEY(project,number));
              CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, project TEXT, kind TEXT, status TEXT, at REAL, error TEXT, result TEXT);
              CREATE TABLE IF NOT EXISTS traces(seq INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT, at REAL, detail TEXT, previous_hash TEXT, hash TEXT);
              CREATE TABLE IF NOT EXISTS budget(day TEXT PRIMARY KEY, attempts INTEGER DEFAULT 0, reserved_tokens INTEGER DEFAULT 0);
            ''')
            c.execute("UPDATE jobs SET status='interrupted',error='Server restarted. Review the retained project and retry explicitly.' WHERE status IN ('queued','running')")
    def connect(self):
        c=sqlite3.connect(self.db, timeout=15); c.row_factory=sqlite3.Row; return c
    def create(self, brief, mode):
        i=uuid.uuid4().hex
        with self.connect() as c: c.execute('INSERT INTO projects VALUES(?,?,?,?,0)',(i,time.time(),brief,mode))
        return i
    def get(self, i):
        with self.connect() as c:
            p=c.execute('SELECT * FROM projects WHERE id=?',(i,)).fetchone()
            if not p:return None
            d=dict(p); r=c.execute('SELECT * FROM revisions WHERE project=? ORDER BY number DESC',(i,)).fetchall()
            d['history']=[{**dict(x),'board':json.loads(x['board'])} for x in r]
            d['storyboard']=d['history'][0]['board'] if r else None
            jobs=c.execute('SELECT * FROM jobs WHERE project=? ORDER BY at DESC',(i,)).fetchall()
            d['jobs']=[{**dict(j),'result':json.loads(j['result']) if j['result'] else None} for j in jobs]
            d['traces']=self.traces(i)
        return d
    def list(self):
        with self.connect() as c:return [dict(x) for x in c.execute('SELECT * FROM projects ORDER BY created DESC LIMIT 100')]
    def save(self, i, board, source, expected, instruction=''):
        with self.lock, self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT revision FROM projects WHERE id=?',(i,)).fetchone()
            if not row or row[0] != expected:raise Conflict('Project changed. Reload before saving.')
            c.execute('INSERT INTO revisions VALUES(?,?,?,?,?,?)',(i,expected+1,time.time(),canonical(board),source,instruction))
            c.execute('UPDATE projects SET revision=? WHERE id=?',(expected+1,i))
        return expected+1
    def job(self,i,kind):
        with self.lock,self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute("SELECT 1 FROM jobs WHERE project=? AND status IN ('queued','running')",(i,)).fetchone():
                raise Conflict('A job is already active for this project.')
            active=c.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]
            if active>=4:raise Conflict('Local queue is full. Wait for a job or cancel one.')
            j=uuid.uuid4().hex
            c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?)',(j,i,kind,'queued',time.time(),None,None))
        return j
    def job_get(self,j):
        with self.connect() as c:r=c.execute('SELECT * FROM jobs WHERE id=?',(j,)).fetchone()
        if not r:return None
        return {**dict(r),'result':json.loads(r['result']) if r['result'] else None}
    def job_set(self,j,status,error=None,result=None):
        with self.connect() as c:c.execute('UPDATE jobs SET status=?,error=?,result=? WHERE id=?',(status,error,canonical(result) if result else None,j))
    def trace(self,i,detail):
        with self.lock,self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT hash FROM traces WHERE project=? ORDER BY seq DESC LIMIT 1',(i,)).fetchone()
            previous=row[0] if row else '0'*64; at=time.time()
            value={'project':i,'at':at,'detail':detail,'previous_hash':previous}
            c.execute('INSERT INTO traces(project,at,detail,previous_hash,hash) VALUES(?,?,?,?,?)',(i,at,canonical(detail),previous,digest(value)))
    def traces(self,i):
        with self.connect() as c:rows=c.execute('SELECT * FROM traces WHERE project=? ORDER BY seq',(i,)).fetchall()
        return [{**dict(x),'detail':json.loads(x['detail'])} for x in rows]
    def reserve(self,tokens,max_attempts,max_tokens):
        day=time.strftime('%Y-%m-%d',time.gmtime())
        with self.lock,self.connect() as c:
            c.execute('BEGIN IMMEDIATE'); c.execute('INSERT OR IGNORE INTO budget(day) VALUES(?)',(day,))
            r=c.execute('SELECT * FROM budget WHERE day=?',(day,)).fetchone()
            if r['attempts']+1>max_attempts or r['reserved_tokens']+tokens>max_tokens:
                raise BudgetExceeded('Daily request/token cap reached. No provider request was sent.')
            c.execute('UPDATE budget SET attempts=attempts+1,reserved_tokens=reserved_tokens+? WHERE day=?',(tokens,day))
    def budget(self):
        day=time.strftime('%Y-%m-%d',time.gmtime())
        with self.connect() as c:r=c.execute('SELECT * FROM budget WHERE day=?',(day,)).fetchone()
        return dict(r) if r else {'day':day,'attempts':0,'reserved_tokens':0}

def verify_traces(traces):
    previous='0'*64
    for x in traces:
        if x['previous_hash'] != previous:return False
        body={k:x[k] for k in ('project','at','detail','previous_hash')}
        if digest(body)!=x['hash']:return False
        previous=x['hash']
    return True
