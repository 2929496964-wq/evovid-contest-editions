"""Offline verification of media-export SHA-256 manifest and trace hash chain."""
import hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evodock.store import verify_traces

def verify(path):
    with zipfile.ZipFile(path) as z:
        m=json.loads(z.read('manifest.json'))
        for name,h in m['files'].items():
            if hashlib.sha256(z.read(name)).hexdigest()!=h:raise ValueError('File hash mismatch: '+name)
        if not verify_traces(json.loads(z.read('trace.json'))):raise ValueError('Trace chain invalid')
    print('PASS: package hashes and local trace chain. Mode:',m['mode'])
    print('This verifies local integrity only, not provider authenticity or contest compliance.')
if __name__=='__main__':verify(sys.argv[1])
