"""Fail-closed local-only settings. No production PayPal endpoint exists."""
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
import os

ROOT = Path(__file__).resolve().parent.parent
SANDBOX_API = 'https://api-m.sandbox.paypal.com'

def load_env(path=ROOT / '.env'):
    if path.is_file():
        for raw in path.read_text(encoding='utf-8').splitlines():
            raw = raw.strip()
            if not raw or raw.startswith('#') or '=' not in raw: continue
            key, value = raw.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('\"').strip("'"))

@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: ROOT / 'data')
    origin: str = 'http://127.0.0.1:8715'
    payment_mode: str = 'fixture'
    paypal_client_id: str = ''
    paypal_secret: str = ''
    paypal_merchant_id: str = ''
    ai_url: str = 'http://127.0.0.1:8081/v1'
    ai_model: str = ''
    ai_key: str = ''

    def __post_init__(self):
        self.data_dir = Path(self.data_dir)
        o = urlparse(self.origin)
        if o.scheme != 'http' or o.hostname not in ('127.0.0.1', 'localhost') or o.path not in ('', '/') or o.query or o.username:
            raise ValueError('This local edition requires a loopback HTTP origin.')
        self.origin = self.origin.rstrip('/')
        if self.payment_mode not in ('fixture', 'sandbox'):
            raise ValueError('PAYMENT_MODE must be fixture or sandbox. Live payments are forbidden.')
        if self.payment_mode == 'sandbox' and not all((self.paypal_client_id, self.paypal_secret, self.paypal_merchant_id)):
            raise ValueError('Sandbox requires an existing client ID, secret and merchant ID. No fallback to fixture.')
        u = urlparse(self.ai_url)
        if u.scheme not in ('http', 'https') or u.hostname not in ('127.0.0.1', 'localhost', '::1') or u.username or u.password or u.query or u.fragment:
            raise ValueError('AI endpoint must be a local OpenAI-compatible service. Remote providers are not enabled.')
        for key in ('PAYPAL_BASE_URL', 'PAYPAL_API_BASE', 'PAYPAL_ENV'):
            value = os.getenv(key, '')
            if value and value not in (SANDBOX_API, 'sandbox'):
                raise ValueError(f'{key}: production/custom payment endpoints are forbidden.')

    @classmethod
    def from_env(cls):
        load_env()
        return cls(data_dir=Path(os.getenv('EVOVID_DATA_DIR', str(ROOT/'data'))), origin=os.getenv('APP_ORIGIN', 'http://127.0.0.1:8715'),
            payment_mode=os.getenv('PAYMENT_MODE','fixture'), paypal_client_id=os.getenv('PAYPAL_SANDBOX_CLIENT_ID',''),
            paypal_secret=os.getenv('PAYPAL_SANDBOX_SECRET',''), paypal_merchant_id=os.getenv('PAYPAL_SANDBOX_MERCHANT_ID',''),
            ai_url=os.getenv('AI_BASE_URL','http://127.0.0.1:8081/v1'), ai_model=os.getenv('AI_MODEL',''), ai_key=os.getenv('AI_API_KEY',''))
