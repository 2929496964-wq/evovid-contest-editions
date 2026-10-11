"""Local EvoVid-style geometric motion graphics. No neural video generation."""
import hashlib, json, math, os, shutil, subprocess, textwrap, zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from .models import Storyboard
from .store import canonical, digest
COLORS={'mint':(100,233,185),'amber':(255,189,97),'violet':(178,150,255),'sky':(120,190,255)}
def font(size):
    candidates=[os.getenv('EVODOCK_FONT_PATH',''),r'C:\Windows\Fonts\msyh.ttc',r'C:\Windows\Fonts\arial.ttf','/System/Library/Fonts/PingFang.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    p=next((p for p in candidates if p and Path(p).is_file()),None)
    return ImageFont.truetype(p,size) if p else ImageFont.load_default(size=size)
def frame(scene,index,t,mode,width=960,height=540):
    im=Image.new('RGB',(width,height),(13,23,31));d=ImageDraw.Draw(im);accent=COLORS[scene.color]
    phase=t if scene.motion=='drift' else (1-math.cos(t*math.pi))/2 if scene.motion=='rise' else .5+.25*math.sin(t*math.pi*2)
    cx=width*.73+40*phase;cy=height*.36
    if scene.asset_id=='orbit':
        for r in [55,105,165]:d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=accent,width=2)
        x=cx+105*math.cos(phase*6.28);y=cy+105*math.sin(phase*6.28);d.ellipse((x-12,y-12,x+12,y+12),fill=accent)
    elif scene.asset_id=='nature':
        d.ellipse((cx-75,cy-70-25*phase,cx+75,cy+80-25*phase),fill=accent)
        d.polygon([(width*.46,310),(width*.7,185),(width,355)],fill=(35,70,65));d.polygon([(width*.58,365),(width*.88,215),(width,355)],fill=(46,94,74))
    elif scene.asset_id=='product':
        y=int(270-45*phase);d.rounded_rectangle((cx-68,y-143,cx+68,y+20),radius=25,fill=accent)
        d.ellipse((cx-115,y+35,cx+115,y+65),fill=(44,64,75));d.line((cx-28,y-98,cx+28,y-98),fill=(13,23,31),width=6)
    else:
        for k in range(5):
            y=90+k*39;d.rounded_rectangle((width*.65,y,width*.65+110+45*math.sin(k+phase*3),y+14),radius=7,fill=accent)
    d.text((40,25),f'EVODOCK   /   SHOT {index+1:02d}   /   {scene.asset_id.upper()}',font=font(16),fill=(153,173,184))
    y=140-int(12*phase)
    wrap=17 if any(ord(x)>0x3000 for x in scene.title) else 26
    for line in textwrap.wrap(scene.title,wrap)[:3]:d.text((40,y),line,font=font(34),fill=(244,247,245));y+=45
    d.rounded_rectangle((34,389,width-34,482),radius=16,fill=(29,44,54))
    wrap=36 if any(ord(x)>0x3000 for x in scene.caption) else 86
    for k,line in enumerate(textwrap.wrap(scene.caption,wrap)[:3]):d.text((50,401+23*k),line,font=font(18),fill=(220,231,233))
    label='DEMO FIXTURE · No Nebius call' if mode=='fixture' else 'LIVE NEBIUS PLAN · Local motion rendering'
    d.text((40,503),label,font=font(14),fill=accent)
    d.rectangle((0,height-5,int(width*t),height),fill=accent)
    return im

def render(board:Storyboard,folder:Path,mode,stop,width=960,height=540,fps=24):
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('FFmpeg is missing. Install FFmpeg and put it on PATH; no video was fabricated.')
    folder.mkdir(parents=True,exist_ok=True);target=folder/'preview.mp4';tmp=folder/'preview.partial.mp4'
    log=folder/'render.stderr.txt'
    command=[ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)]
    try:
        with log.open('wb') as err:
            p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=err)
            try:
                for i,s in enumerate(board.scenes):
                    for n in range(s.seconds*fps):
                        if stop.is_set():raise InterruptedError('Render cancelled; no completed video was published.')
                        p.stdin.write(frame(s,i,n/(s.seconds*fps),mode,width,height).tobytes())
                p.stdin.close()
                try:p.wait(timeout=30)
                except subprocess.TimeoutExpired:raise RuntimeError('Local encoder timed out.') from None
                if p.returncode:raise RuntimeError('Local encoder failed; no completed video was published.')
                if stop.is_set():raise InterruptedError('Render cancelled.')
                if not tmp.exists() or tmp.stat().st_size<500:raise RuntimeError('Encoder output is missing or empty.')
                tmp.replace(target)
                frame(board.scenes[0],0,.5,mode,width,height).save(folder/'poster.png')
            finally:
                if p.stdin and not p.stdin.closed:p.stdin.close()
                if p.poll() is None:p.kill();p.wait()
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return target

def subtitles(board):
    def ts(s):return f'{s//3600:02d}:{s//60%60:02d}:{s%60:02d},000'
    pos=0;rows=[]
    for i,s in enumerate(board.scenes):
        rows.append(f'{i+1}\n{ts(pos)} --> {ts(pos+s.seconds)}\n{s.title}\n{s.caption}\n');pos+=s.seconds
    return '\n'.join(rows)

def package(project,folder):
    project={k:project[k] for k in ('id','created','brief','mode','revision','history','storyboard','traces')}
    board=Storyboard.model_validate(project['storyboard'])
    (folder/'storyboard.json').write_text(json.dumps(project['storyboard'],ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'trace.json').write_text(json.dumps(project['traces'],ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'captions.srt').write_text(subtitles(board),encoding='utf-8')
    mode='DEMO FIXTURE: deterministic template, no provider call' if project['mode']=='fixture' else 'Live plan source; inspect trace.json for actual provider result and later manual edits'
    (folder/'README.txt').write_text('EvoDock Storyboard Agent\n'+mode+'\nOpen preview.mp4 to play. Local geometric motion graphics, not neural video generation.\nproject.json contains brief, revision history and audit trace. Share only after checking its contents.\nTrace hashes prove local integrity, not an independent provider attestation.\n',encoding='utf-8')
    (folder/'preview.html').write_text('<!doctype html><meta charset="utf-8"><title>EvoDock export</title><style>body{background:#0d171f;color:#ebf2ef;font:18px system-ui;max-width:1000px;margin:40px auto}video{width:100%}p{color:#8de7be}</style><h1>EvoDock storyboard</h1><p>'+mode+'</p><video controls src="preview.mp4" poster="poster.png"></video><p>Local motion graphics · silent H.264 MP4</p>',encoding='utf-8')
    names=['storyboard.json','project.json','trace.json','captions.srt','preview.mp4','poster.png','preview.html','README.txt']
    manifest={'schema':1,'mode':project['mode'],'revision':project['revision'],'board_sha256':digest(project['storyboard']),'files':{n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in names}}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with zipfile.ZipFile(folder/'project.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in names+['manifest.json']:z.write(folder/name,name)
    return manifest
