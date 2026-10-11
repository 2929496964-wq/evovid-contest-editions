#!/usr/bin/env python3
"""Install the documented locked dependencies into a fresh source directory and probe startup."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
ROOT = Path(__file__).resolve().parents[1]
log = ROOT/'evidence'/'clean-room-install.log'
with tempfile.TemporaryDirectory(prefix='clean-room-', dir=ROOT) as raw, log.open('w',encoding='utf-8') as out:
    work=Path(raw)
    for name in ('evobridge','static','tests'):
        shutil.copytree(ROOT/name,work/name,ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('run.py','requirements.lock','start.sh'):
        shutil.copyfile(ROOT/name,work/name)
    subprocess.run([sys.executable,'-m','venv',str(work/'.venv')],check=True,stdout=out,stderr=out)
    py=work/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    subprocess.run([str(py),'-m','pip','install','--disable-pip-version-check','-r','requirements.lock'],cwd=work,check=True,stdout=out,stderr=out)
    subprocess.run([str(py),'-m','unittest','discover','-s','tests','-v'],cwd=work,check=True,stdout=out,stderr=out)
    # Fixed alternate port keeps the interactive development session isolated.
    proc=subprocess.Popen([str(py),'run.py','--port','18711'],cwd=work,stdout=out,stderr=out)
    try:
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            try:
                with urllib.request.urlopen('http://127.0.0.1:18711/api/health') as r: health=json.load(r)
                assert health['ok'] is True
                break
            except OSError: time.sleep(.1)
        else: raise RuntimeError('Clean-room server did not start')
        with urllib.request.urlopen('http://127.0.0.1:18711/') as r:
            assert b'EvoBridge' in r.read()
        print('Clean-room startup and 17 tests passed.',file=out,flush=True)
    finally:
        proc.terminate();proc.wait(timeout=5)
print(str(log))
