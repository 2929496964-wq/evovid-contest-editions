#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from evobridge.app import server

parser = argparse.ArgumentParser(description='EvoBridge local Alexa+ simulation')
parser.add_argument('--port', type=int, default=int(os.getenv('PORT', '8711')))
parser.add_argument('--data', type=Path, default=Path(__file__).resolve().parent / 'data')
args = parser.parse_args()
if not 0 <= args.port <= 65535:
    parser.error('Invalid port')
httpd = server(args.data, args.port)
print(f'EvoBridge ready: http://127.0.0.1:{httpd.server_port}', flush=True)
print('Alexa+ SIMULATION. Deterministic local motion graphics. Press Ctrl+C to stop.', flush=True)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    for event in list(httpd.app.events.values()):
        event.set()
finally:
    httpd.server_close()
    httpd.app.pool.shutdown(wait=True, cancel_futures=True)
