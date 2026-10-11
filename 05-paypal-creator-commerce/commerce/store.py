"""SQLite ledger. Rights are revision-specific and unique per payment provider mode."""
import sqlite3, threading
from contextlib import contextmanager

SCHEMA='''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, csrf TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES sessions(id), title TEXT NOT NULL, brief TEXT NOT NULL, current_revision INTEGER NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS revisions (project TEXT NOT NULL REFERENCES projects(id), revision INTEGER NOT NULL, board TEXT NOT NULL, provenance TEXT NOT NULL, checksum TEXT NOT NULL, PRIMARY KEY(project,revision));
CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES sessions(id), project TEXT NOT NULL REFERENCES projects(id), revision INTEGER NOT NULL, mode TEXT NOT NULL, sku TEXT NOT NULL, amount TEXT NOT NULL, currency TEXT NOT NULL, merchant TEXT NOT NULL, status TEXT NOT NULL, paypal_id TEXT UNIQUE, approval_url TEXT, create_key TEXT NOT NULL UNIQUE, capture_key TEXT NOT NULL UNIQUE, capture_id TEXT UNIQUE, fixture_remote TEXT, error TEXT, created TEXT NOT NULL, UNIQUE(project,revision,mode));
CREATE TABLE IF NOT EXISTS captures (id TEXT PRIMARY KEY, order_id TEXT NOT NULL UNIQUE REFERENCES orders(id), amount TEXT NOT NULL, currency TEXT NOT NULL, mode TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entitlements (project TEXT NOT NULL, revision INTEGER NOT NULL, mode TEXT NOT NULL, order_id TEXT NOT NULL UNIQUE REFERENCES orders(id), capture_id TEXT NOT NULL UNIQUE REFERENCES captures(id), created TEXT NOT NULL, PRIMARY KEY(project,revision,mode));
CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, action TEXT NOT NULL, project TEXT, order_id TEXT, detail TEXT NOT NULL, created TEXT NOT NULL);
'''
class Store:
    def __init__(self,path):
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with self.connection() as c:c.executescript(SCHEMA)
    @contextmanager
    def connection(self):
        c=sqlite3.connect(self.path,timeout=30)
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        try:
            yield c
            c.commit()
        except BaseException:
            c.rollback();raise
        finally:c.close()
