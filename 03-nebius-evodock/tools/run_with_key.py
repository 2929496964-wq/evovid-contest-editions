"""Optional secure local prompt AFTER legal access and runtime spending authorization.
Never saves the key; never creates credentials. This is not run during the offline build.
"""
import getpass,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evodock.provider import ENDPOINTS

def main():
    print('Only proceed after Nebius has resolved legitimate service access for your actual country, and you have an authorized existing key and approved usage budget.')
    print('Live calls send the current brief/storyboard/instruction to Nebius. Defaults: at most 6 inference attempts/day, 1600 output tokens/attempt, 45000 conservative reserved tokens/day. These are NOT a currency spending guarantee.')
    if input('Type I AUTHORIZE LIVE USAGE to enable live mode locally: ').strip()!='I AUTHORIZE LIVE USAGE':
        print('Cancelled. No key read and no API call.');return
    print('Select the endpoint assigned to your legitimate account; regions do not bypass service eligibility.')
    for i,ep in enumerate(ENDPOINTS):print(f'{i+1}. {ep}')
    value=input('Endpoint [1]: ').strip() or '1'
    if value not in ('1','2'):print('Invalid endpoint; cancelled.');return
    key=getpass.getpass('Existing authorized Nebius API key (hidden, never saved): ').strip()
    if not key:print('No key entered; cancelled.');return
    os.environ['NEBIUS_API_KEY']=key;os.environ['NEBIUS_LIVE_AUTHORIZED']='1';os.environ['NEBIUS_BASE_URL']=ENDPOINTS[int(value)-1]
    import uvicorn
    from evodock.app import create_app
    print('Open the local app. Model discovery and inference occur only after explicit UI actions.')
    uvicorn.run(create_app(),host='127.0.0.1',port=int(os.getenv('PORT','8713')),access_log=False)
if __name__=='__main__':main()
