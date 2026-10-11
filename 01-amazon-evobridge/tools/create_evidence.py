#!/usr/bin/env python3
"""Repeatable real-render acceptance proof; no browser or prerecorded substitution."""
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evobridge import model
from evobridge.app import App
from evobridge.render import frame, font_path, ffmpeg_path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'samples'
OUT.mkdir(exist_ok=True)

def wait(app, jid, limit=120):
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        j = app.store.get(jid)
        if j['status'] not in ('queued', 'running'):
            return j
        time.sleep(.1)
    raise RuntimeError('Render timed out')

report = {'python': sys.version, 'platform': platform.platform(), 'font': font_path(), 'ffmpeg': subprocess.check_output([ffmpeg_path(), '-version'], text=True).splitlines()[0], 'cases': [], 'checks': {}}
with tempfile.TemporaryDirectory(prefix='evobridge-proof-') as home:
    app = App(Path(home))
    examples = [('cafe', 'The corner café', 'our neighborhood', 9, 'warm'), ('garden-zh', '阳台上的小菜园', '城市新手园丁', 12, 'calm'), ('makers', 'Build something that matters', 'independent makers', 9, 'bold')]
    for slug, theme, audience, length, tone in examples:
        p = model.new_project()
        model.build(p, theme, audience, length, tone)
        model.command(p, 'Shorten scene 2')
        model.command(p, 'Text 3: ' + ('一起播下明天的绿色。' if slug=='garden-zh' else 'Your next chapter starts here.'))
        if slug=='garden-zh':
            model.edit(p, {'format': 'portrait'})
        app.save(p)
        body = {'project_id': p['id'], 'revision': p['revision'], 'confirmed': True}
        job = app.start_render(body)
        duplicate = app.start_render(body)
        assert duplicate['id'] == job['id']
        done = wait(app, job['id'])
        assert done['status']=='done', done
        source = app.outputs / (job['id'] + '.mp4')
        target = OUT / (slug + '.mp4')
        shutil.copyfile(source, target)
        manifest = json.loads((app.outputs/(job['id']+'.json')).read_text())
        (OUT/(slug+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        subprocess.run([ffmpeg_path(), '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(p['scenes'][0]['seconds'] + p['scenes'][1]['seconds'] * .55), '-i', str(target), '-frames:v', '1', str(OUT/(slug+'-frame.png'))], check=True)
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height','-of','json',str(target)],text=True)) if shutil.which('ffprobe') else None
        if probe:
            assert abs(float(probe['format']['duration'])-p['duration'])<.1
            assert probe['streams'][0]['codec_name']=='h264'
        report['cases'].append({'name':slug,'requested_seconds':length,'final_seconds':p['duration'],'edits':2,'job_id':job['id'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'probe':probe,'duplicate_job_reused':True})
    assert len(set(c['sha256'] for c in report['cases']))==3
    report['checks']['distinct_input_produces_distinct_mp4']=True
    p=model.new_project();model.build(p,'Cancellation test','testers',45,'warm');app.save(p)
    j=app.start_render({'project_id':p['id'],'revision':p['revision'],'confirmed':True})
    app.mutate('/api/cancel',{'job_id':j['id']})
    result=wait(app,j['id'])
    assert result['status']=='cancelled'
    assert not (app.outputs/(j['id']+'.mp4')).exists()
    report['checks']['cancel_does_not_publish_video']=True
    p=model.new_project();model.build(p,'Failure and retry','testers',6,'calm');app.save(p)
    body={'project_id':p['id'],'revision':p['revision'],'confirmed':True}
    with patch('evobridge.app.render',side_effect=RuntimeError('Deliberate renderer failure for recovery test')):
        j=app.start_render(body);assert wait(app,j['id'])['status']=='failed'
    retried=app.start_render(body);assert retried['id']!=j['id'];assert wait(app,retried['id'])['status']=='done'
    report['checks']['failed_render_can_retry']=True
    app.pool.shutdown(wait=True)
report['passed']=True
(ROOT/'evidence'/'render-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
