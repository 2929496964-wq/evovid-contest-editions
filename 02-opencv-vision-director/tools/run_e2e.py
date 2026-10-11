"""Launch HTTP checks in the same network namespace; no background orphan server."""
from pathlib import Path
import subprocess,sys,time,os,urllib.request
ROOT=Path(__file__).resolve().parents[1]
log=(ROOT/'evidence/server-e2e.log').open('w')
env={**os.environ,'VISION_DATA_DIR':str(ROOT/'runtime-e2e')}
p=subprocess.Popen([sys.executable,'-m','uvicorn','vision.server:app','--host','127.0.0.1','--port','8712'],cwd=ROOT,env=env,stdout=log,stderr=log)
try:
    for _ in range(100):
        try: urllib.request.urlopen('http://127.0.0.1:8712/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    else:raise RuntimeError('Server did not start. Check evidence/server-e2e.log')
    subprocess.run([sys.executable,'tools/e2e.py'],cwd=ROOT,check=True)
finally:
    p.terminate()
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:p.kill();p.wait()
    log.close()
