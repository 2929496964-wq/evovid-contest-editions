"""Cross-platform loopback launcher; never starts a provider request automatically."""
import argparse, os
import uvicorn
from evodock.app import create_app
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=int(os.getenv('PORT','8713')));parser.add_argument('--data-dir',default=os.getenv('EVODOCK_DATA_DIR','data'));args=parser.parse_args()
    print(f'EvoDock local studio: http://127.0.0.1:{args.port} — DEMO FIXTURE is available without an API key.',flush=True)
    uvicorn.run(create_app(args.data_dir),host='127.0.0.1',port=args.port,access_log=False)
