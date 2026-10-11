"""PayPal Orders v2 adapter. Only the fixed Sandbox REST host can be called."""
import copy, time, uuid
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import httpx
from .config import SANDBOX_API

class PaymentUnavailable(Exception):pass
class PaymentRejected(Exception):pass

class PayPalSandbox:
    mode='sandbox'
    def __init__(self,settings,client=None):
        self.settings=settings
        self.client=client or httpx.Client(timeout=httpx.Timeout(25,connect=8),follow_redirects=False,trust_env=False)
        self._token=None;self._expires=0
    def close(self):self.client.close()
    def _access_token(self):
        if self._token and time.monotonic()<self._expires:return self._token
        try:
            r=self.client.post(SANDBOX_API+'/v1/oauth2/token',auth=(self.settings.paypal_client_id,self.settings.paypal_secret),data={'grant_type':'client_credentials'})
            r.raise_for_status();body=r.json()
            self._token=body['access_token'];self._expires=time.monotonic()+min(int(body.get('expires_in',300)),3600)-30
            return self._token
        except (httpx.HTTPError,KeyError,ValueError,TypeError) as exc:
            raise PaymentUnavailable('PayPal Sandbox authentication unavailable. Check server configuration; no payment was inferred.') from exc
    def _request(self,method,path,body=None,key=None):
        headers={'Authorization':'Bearer '+self._access_token(),'Content-Type':'application/json','Prefer':'return=representation'}
        if key:headers['PayPal-Request-Id']=key
        try:
            r=self.client.request(method,SANDBOX_API+path,json=body,headers=headers)
            r.raise_for_status()
            if len(r.content)>500000:raise ValueError('Oversized response')
            return r.json()
        except (httpx.HTTPError,ValueError) as exc:
            raise PaymentUnavailable('PayPal Sandbox result is uncertain. Reconcile this same order before attempting anything else.') from exc
    def create(self,order):
        base=self.settings.origin
        result=self._request('POST','/v2/checkout/orders',{
            'intent':'CAPTURE','purchase_units':[{'reference_id':order['id'],'custom_id':order['id'],'invoice_id':'EVO-'+order['id'],
                'description':'EvoVid fictional creator project: one revision, portrait HD export (SANDBOX)',
                'payee':{'merchant_id':order['merchant']},'amount':{'currency_code':order['currency'],'value':order['amount']}}],
            'payment_source':{'paypal':{'experience_context':{'brand_name':'EvoVid Creator Commerce','shipping_preference':'NO_SHIPPING','user_action':'PAY_NOW',
                'return_url':base+'/?checkout='+order['id']+'&result=return','cancel_url':base+'/?checkout='+order['id']+'&result=cancel'}}}
            },order['create_key'])
        order_id=result.get('id','')
        if not isinstance(order_id,str) or not order_id or len(order_id)>100:raise PaymentUnavailable('PayPal returned no valid order ID.')
        link=next((x.get('href') for x in result.get('links',[]) if x.get('rel') in ('payer-action','approve')),None)
        u=urlparse(link or '')
        if u.scheme!='https' or u.hostname!='www.sandbox.paypal.com' or u.username or u.password or u.port not in (None,443):
            raise PaymentUnavailable('PayPal did not return an allowed Sandbox approval URL.')
        return order_id,link
    def get(self,order):return self._request('GET','/v2/checkout/orders/'+order['paypal_id'])
    def capture(self,order):return self._request('POST','/v2/checkout/orders/'+order['paypal_id']+'/capture',{},order['capture_key'])

class FixturePayments:
    mode='fixture'
    def create(self,order):return 'FIXTURE-'+order['id'],None
    def get(self,order):
        import json
        return json.loads(order['fixture_remote']) if order['fixture_remote'] else {'id':order['paypal_id'],'status':'CREATED'}
    def close(self):pass
    @staticmethod
    def response(order,scenario):
        capture={'id':'TEST-CAPTURE-'+order['id'],'status':'COMPLETED','final_capture':True,'amount':{'value':order['amount'],'currency_code':order['currency']}}
        result={'id':order['paypal_id'],'status':'COMPLETED','purchase_units':[{'reference_id':order['id'],'custom_id':order['id'],
            'payee':{'merchant_id':order['merchant']},'amount':copy.deepcopy(capture['amount']),'payments':{'captures':[capture]}}]}
        if scenario=='pending':capture['status']='PENDING';result['status']='APPROVED'
        if scenario=='declined':capture['status']='DECLINED';result['status']='APPROVED'
        if scenario=='wrong-amount':capture['amount']['value']='0.01'
        if scenario=='wrong-currency':capture['amount']['currency_code']='EUR'
        if scenario=='wrong-merchant':result['purchase_units'][0]['payee']['merchant_id']='OTHER-MERCHANT'
        if scenario=='wrong-order':result['id']='OTHER-ORDER'
        if scenario=='wrong-reference':result['purchase_units'][0]['custom_id']='OTHER-PROJECT'
        return result

def verify_order_identity(order,response):
    """Validate immutable order details BEFORE any capture request."""
    try:
        if response.get('id')!=order['paypal_id']:raise PaymentRejected('Order ID does not match the stored order.')
        units=response.get('purchase_units',[])
        if len(units)!=1:raise PaymentRejected('Expected exactly one purchase unit.')
        unit=units[0]
        if unit.get('reference_id')!=order['id'] or unit.get('custom_id')!=order['id']:raise PaymentRejected('Order reference does not match this project revision.')
        if unit.get('payee',{}).get('merchant_id')!=order['merchant']:raise PaymentRejected('Recipient merchant mismatch.')
        amount=unit.get('amount',{})
        if amount.get('currency_code')!=order['currency'] or Decimal(amount.get('value','NaN'))!=Decimal(order['amount']):
            raise PaymentRejected('Order amount or currency mismatch.')
        return unit
    except (InvalidOperation,AttributeError,TypeError,KeyError) as exc:raise PaymentRejected('Malformed payment evidence.') from exc

def verify_completion(order,response):
    """The only gateway to an entitlement. Reject mixed/partial/foreign captures."""
    try:
        unit=verify_order_identity(order,response)
        captures=unit.get('payments',{}).get('captures',[])
        if len(captures)!=1:raise PaymentRejected('Expected exactly one capture.')
        capture=captures[0];amount=capture.get('amount',{})
        if amount.get('currency_code')!=order['currency'] or Decimal(amount.get('value','NaN'))!=Decimal(order['amount']):
            raise PaymentRejected('Capture amount or currency mismatch.')
        status=capture.get('status')
        if status=='PENDING':return None,'PENDING'
        if status in ('DECLINED','DENIED','FAILED'):return None,'DECLINED'
        if response.get('status')!='COMPLETED' or status!='COMPLETED':return None,'VERIFYING'
        if capture.get('final_capture') is not True:raise PaymentRejected('Capture is not final.')
        cid=capture.get('id')
        if not isinstance(cid,str) or not cid or len(cid)>150:raise PaymentRejected('Invalid capture identifier.')
        return cid,'COMPLETED'
    except (InvalidOperation,AttributeError,TypeError,KeyError) as exc:raise PaymentRejected('Malformed payment evidence.') from exc
