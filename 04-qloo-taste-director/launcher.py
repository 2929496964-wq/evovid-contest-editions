"""Start local Taste Director. No credential discovery, downloads or cloud calls at startup."""
from pathlib import Path
import argparse, os, threading, webbrowser
import uvicorn
from taste.server import create_app

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8714')))
    p.add_argument('--host', default='127.0.0.1', choices=['127.0.0.1', '0.0.0.0'])
    p.add_argument('--no-browser', action='store_true')
    args = p.parse_args()
    if not 1024 <= args.port <= 65535: p.error('Port must be 1024–65535.')
    hosts = ['127.0.0.1', 'localhost', '[::1]']
    hosts += [x.strip() for x in os.environ.get('TASTE_ALLOWED_HOSTS', '').split(',') if x.strip() and '*' not in x]
    home = Path(os.environ.get('TASTE_DATA_DIR', str(Path(__file__).parent / '.taste-data')))
    app = create_app(home, allowed_hosts=hosts)
    url = f'http://127.0.0.1:{args.port}'
    print(f'EvoVid Taste Director: {url}\nDefault: DEMO fixtures. LIVE credentials stay on the server.', flush=True)
    if args.host == '0.0.0.0': print('External binding enabled explicitly. Use the HTTPS/session-isolation deployment checklist before publication.', flush=True)
    if not args.no_browser: threading.Timer(1, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level='warning', access_log=False, proxy_headers=False)

if __name__ == '__main__': main()
