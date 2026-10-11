"""Starts on loopback only. Credentials are loaded locally, never printed."""
import os
from urllib.parse import urlparse
from commerce.config import load_env, Settings
load_env()
port=int(os.getenv('PORT','8715'))
if not (1024<=port<=65535):raise SystemExit('PORT must be between 1024 and 65535.')
os.environ.setdefault('APP_ORIGIN',f'http://127.0.0.1:{port}')
settings=Settings.from_env()
if (urlparse(settings.origin).port or 80)!=port:raise SystemExit('APP_ORIGIN port must match PORT.')
if __name__=='__main__':
    import uvicorn
    from commerce.app import create_app
    print(f'EvoVid Creator Commerce: {settings.origin}')
    print('TEST FIXTURE, NOT PAYPAL PAYMENT' if settings.payment_mode=='fixture' else 'PAYPAL SANDBOX ONLY. NO REAL MONEY.')
    uvicorn.run(create_app(settings),host='127.0.0.1',port=port,access_log=False,log_level='warning')
