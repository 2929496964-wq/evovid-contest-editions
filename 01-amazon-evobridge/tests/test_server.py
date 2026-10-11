import base64
import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from PIL import Image
from evobridge.app import server, App
from evobridge import model


class HTTP(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = server(Path(self.temp.name), 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.token = self.server.app.token
        self.pid = self.server.app.projects()[0]['id']

    def tearDown(self):
        for event in list(self.server.app.events.values()): event.set()
        self.server.shutdown()
        self.server.server_close()
        self.server.app.pool.shutdown(wait=True)
        self.temp.cleanup()

    def request(self, path, body=None, headers=None):
        hs = {'Content-Type': 'application/json', 'X-EvoBridge-Token': self.token}
        hs.update(headers or {})
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode() if body is not None else None, headers=hs)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.read(), r.headers
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers

    def test_health_static_and_csp(self):
        code, raw, headers = self.request('/')
        self.assertEqual(code, 200)
        self.assertIn(b'Alexa+ simulation', raw)
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])

    def test_origin_and_token(self):
        for headers in [{'Origin': 'https://evil.example'}, {'Host': 'evil.example'}, {'X-EvoBridge-Token': 'bad'}]:
            code, _, _ = self.request('/api/projects', {}, headers)
            self.assertEqual(code, 403)

    def test_traversal_unknown_paths(self):
        for path in ['/../run.py', '/outputs/../../run.py', '/assets/%2e%2e%2f%2e%2e%2frun.py', '/outputs/not-an-id.mp4']:
            self.assertEqual(self.request(path)[0], 404)

    def test_confirmation_and_stale_revision_required(self):
        self.request('/api/brief', {'project_id': self.pid, 'theme': 'Test', 'audience': 'everyone', 'duration': 6, 'tone': 'warm'})
        for payload in [{'confirmed': False, 'revision': 1}, {'confirmed': True, 'revision': 0}]:
            code, _, _ = self.request('/api/render', {'project_id': self.pid, **payload})
            self.assertEqual(code, 400)
        self.assertEqual(len(self.server.app.store.list()), 0)

    def test_asset_sanitized_and_unknown_asset_refused(self):
        im = Image.new('RGB', (50, 30), 'red')
        data = io.BytesIO(); im.save(data, 'PNG')
        code, raw, _ = self.request('/api/assets', {'name': '../../hello.png', 'data': base64.b64encode(data.getvalue()).decode()})
        self.assertEqual(code, 200)
        aid = json.loads(raw)['asset']['id']
        self.assertRegex(aid, r'^[a-f0-9]{32}$')
        self.assertEqual(self.request('/assets/' + aid + '.jpg')[0], 200)
        self.assertEqual(self.request('/api/assets', {'name': 'bad', 'data': 'YWJj'})[0], 400)

    def test_restore_creates_new_project_and_drops_paths(self):
        p = model.new_project(); model.build(p, 'Restored', 'friends', 12, 'warm')
        p['scenes'][0]['asset'] = '../../secret'
        code, raw, _ = self.request('/api/import', {'project': p})
        self.assertEqual(code, 200)
        restored = json.loads(raw)['project']
        self.assertNotEqual(p['id'], restored['id'])
        self.assertEqual(restored['theme'], p['theme'])
        self.assertIsNone(restored['scenes'][0]['asset'])
        self.assertEqual(len(restored['history']), 0)

    def test_restart_recovery_marks_unfinished_job(self):
        app = self.server.app
        p = app.project(self.pid); model.build(p, 'Saved', 'friends', 6, 'warm'); app.save(p)
        jid = app.store.create({'project': p})
        app.store.update(jid, 'running')
        restored = App(Path(self.temp.name))
        try:
            self.assertEqual(restored.project(self.pid)['theme'], 'Saved')
            self.assertEqual(restored.store.get(jid)['status'], 'interrupted')
        finally:
            restored.pool.shutdown()


if __name__ == '__main__': unittest.main()
