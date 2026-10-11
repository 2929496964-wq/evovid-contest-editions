"""Actual loopback startup/HTTP check, using no Qloo credentials."""
from pathlib import Path
import json, os, subprocess, tempfile, time, urllib.request
root=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(dir=root/'evidence') as home:
    env={**os.environ,'PORT':'18714','TASTE_DATA_DIR':home,'QLOO_API_KEY':''}
    process=subprocess.Popen([str(root/'start.sh'),'--no-browser'],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        for _ in range(100):
            try:
                with opener.open('http://127.0.0.1:18714/api/state',timeout=1) as response:
                    data=json.load(response);headers=dict(response.headers)
                break
            except OSError:
                if process.poll() is not None: raise RuntimeError('Launcher exited before startup.')
                time.sleep(.05)
        else: raise RuntimeError('Server did not become reachable.')
        with opener.open('http://127.0.0.1:18714/',timeout=2) as response:
            html=response.read().decode()
        assert 'Taste Director' in html and data['live_configured'] is False
        assert 'HttpOnly' in headers['set-cookie'] or 'HttpOnly' in headers.get('Set-Cookie','')
        result={'passed':True,'entrypoint':'start.sh --no-browser','port_environment':18714,'actual_http':True,'live_configured':data['live_configured'],'html_served':True,'security_headers':{k:v for k,v in headers.items() if k.lower() in ('content-security-policy','x-content-type-options','permissions-policy')}}
        (root/'evidence'/'http-startup.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
