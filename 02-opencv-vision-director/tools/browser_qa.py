"""Optional UI QA. Uses installed Playwright/Chromium, does not download browsers."""
from pathlib import Path
import os, subprocess, time, json, urllib.request
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
PYTHON=ROOT/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')
ENV={**os.environ,'VISION_DATA_DIR':str(ROOT/'runtime-ui-qa')}
logs=(ROOT/'evidence/browser-server.log').open('w')
server=subprocess.Popen([str(PYTHON),'-m','uvicorn','vision.server:app','--host','127.0.0.1','--port','8712'],cwd=ROOT,env=ENV,stdout=logs,stderr=logs)
results=[]
try:
    for _ in range(100):
        try: urllib.request.urlopen('http://127.0.0.1:8712/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8712');page.wait_for_selector('#engine:has-text("5.0.0")')
        page.screenshot(path=str(ROOT/'evidence/ui-desktop-empty.png'),full_page=True)
        page.click('#demo');page.wait_for_selector('#analysis-view:not([hidden])',timeout=60000)
        page.wait_for_function("document.getElementById('state').textContent === 'review'")
        assert page.locator('.segment').count()==12
        assert 'SYNTHETIC' in page.locator('#job-type').inner_text()
        results.append({'check':'Demo analyzed and 12 review intervals visible','passed':True})
        page.fill('#target','4');page.select_option('#weight','4');page.click('#recommend')
        page.wait_for_function("document.getElementById('selected-summary').textContent.includes('4.00 seconds')")
        page.check('#approved');page.click('#render')
        page.wait_for_function("document.getElementById('state').textContent === 'complete'",timeout=90000)
        page.wait_for_function("document.getElementById('after').readyState >= 2")
        assert page.locator('#after').evaluate('(v)=>v.duration')>3.5
        page.screenshot(path=str(ROOT/'evidence/ui-desktop-complete.png'),full_page=True)
        results.append({'check':'Human approval renders playable video in browser','passed':True})
        page.reload();page.wait_for_selector('#downloads:not([hidden])')
        results.append({'check':'Reload restores selected completed session','passed':True})
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(ROOT/'evidence/ui-mobile-complete.png'),full_page=True)
        overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
        assert not overflow
        results.append({'check':'390px mobile has no horizontal overflow','passed':not overflow})
        page.click('#load-logs');page.wait_for_function("document.getElementById('logs').textContent.includes('render_finished')")
        results.append({'check':'Log inspection works','passed':True})
        assert not errors,errors
        results.append({'check':'No browser JavaScript errors','passed':not errors})
        browser.close()
finally:
    server.terminate();server.wait(timeout=15);logs.close()
    (ROOT/'evidence/browser-qa.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
