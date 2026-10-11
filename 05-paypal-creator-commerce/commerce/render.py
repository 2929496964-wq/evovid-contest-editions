"""Adapted from MIT EvoVid motion renderer. Real H.264, never claimed neural footage."""
from pathlib import Path
import math, os, shutil, subprocess, tempfile, textwrap, threading, time
from PIL import Image, ImageDraw, ImageFont

COLORS={'lime':'#d3ff62','violet':'#b4a2ff','cyan':'#75e2e2','orange':'#ffb878'}
render_lock=threading.Lock()

def ffmpeg_path():
    p=shutil.which('ffmpeg')
    if p:return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as e:raise RuntimeError('Install requirements.lock; FFmpeg is bundled by imageio-ffmpeg. No model downloads.') from e

def font(size,bold=False):
    candidates=[os.getenv('EVOVID_FONT_PATH',''),r'C:\Windows\Fonts\msyh.ttc',r'C:\Windows\Fonts\arial.ttf',
        '/System/Library/Fonts/PingFang.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf']
    path=next((p for p in candidates if p and Path(p).is_file()),None)
    return ImageFont.truetype(path,size) if path else ImageFont.load_default(size=size)

def lines(text,max_width,draw,fnt):
    output=[];current=''
    # Character-aware wrapping also works for languages without spaces.
    for char in text:
        trial=current+char
        if draw.textlength(trial,font=fnt)>max_width and current:
            output.append(current.strip());current=char
        else:current=trial
    if current:output.append(current.strip())
    return output

def frame(board,scene_index,t,width,height,preview=False,mode='fixture'):
    im=Image.new('RGB',(width,height),'#111310');d=ImageDraw.Draw(im)
    s=board.scenes[scene_index];accent=COLORS[s.accent];scale=width/720
    def xy(v):return int(v*scale)
    def rect(box,**kw):d.rounded_rectangle(tuple(xy(v) for v in box),radius=xy(kw.pop('radius',20)),**kw)
    # Oversized orbiting shapes add original motion, without stock media.
    x=360+math.sin(t*1.4+scene_index)*130;y=520+math.cos(t*1.1)*85
    d.ellipse((xy(x-245),xy(y-245),xy(x+245),xy(y+245)),fill=accent)
    d.ellipse((xy(x-145),xy(y-145),xy(x+145),xy(y+145)),fill='#111310')
    for k in range(4):
        q=(t*.2+k*.25)%1
        d.arc((xy(70+q*60),xy(240+q*80),xy(650-q*60),xy(910-q*80)),start=scene_index*32+q*100,end=scene_index*32+q*100+130,fill='#44483c',width=max(1,xy(2)))
    tiny=font(xy(18));small=font(xy(25));big=font(xy(62),True)
    d.text((xy(46),xy(48)),'E V O V I D   /   C R E A T O R   C O M M E R C E',font=tiny,fill='#e8ede2')
    d.text((xy(46),xy(105)),f'0{scene_index+1} / 0{len(board.scenes)}     ORIGINAL MOTION STORY',font=tiny,fill='#b7bcae')
    rect((30,740,690,1150),fill='#f2f3e8',radius=28)
    y_text=778
    for line in lines(s.title,xy(590),d,big)[:3]:
        d.text((xy(62),xy(y_text)),line,font=big,fill='#14180d');y_text+=76
    y_text=max(y_text+22,994)
    for line in lines(s.caption,xy(592),d,small)[:3]:
        d.text((xy(62),xy(y_text)),line,font=small,fill='#414936');y_text+=34
    d.text((xy(46),xy(1190)),'FICTIONAL BRAND / ORIGINAL ARTWORK',font=tiny,fill='#abb39d')
    label='PREVIEW / EXPORT LOCKED' if preview else ('TEST FIXTURE / NOT A PAYPAL PAYMENT' if mode=='fixture' else 'PAYPAL SANDBOX / TEST MONEY')
    d.text((xy(46),xy(1230)),label,font=font(xy(16)),fill=accent)
    if preview:
        overlay=Image.new('RGBA',im.size,(0,0,0,0));od=ImageDraw.Draw(overlay)
        od.rounded_rectangle((xy(120),xy(552),xy(600),xy(626)),radius=xy(15),fill=(17,19,16,205))
        od.text((xy(158),xy(574)),'WATERMARKED PREVIEW',font=font(xy(25),True),fill='#ffffff')
        im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
    return im

def render(board,target,preview=False,mode='fixture'):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    width,height=(360,640) if preview else (720,1280)
    fps=12
    with render_lock:
        if target.exists():return target
        tmp=target.with_name(target.stem+'.working.mp4')
        with tempfile.TemporaryFile() as err:
            process=subprocess.Popen([ffmpeg_path(),'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
                '-s',f'{width}x{height}','-r',str(fps),'-i','-','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','22',
                '-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)],stdin=subprocess.PIPE,stderr=err,stdout=subprocess.DEVNULL)
            # Watchdog also kills a blocked pipe write. Bounded render size and duration.
            watchdog=threading.Timer(90,process.kill);watchdog.start()
            try:
                for i,s in enumerate(board.scenes):
                    for n in range(s.seconds*fps):
                        process.stdin.write(frame(board,i,n/fps,width,height,preview,mode).tobytes())
                process.stdin.close()
                if process.wait(timeout=15)!=0:raise RuntimeError('Video encoding failed or exceeded the time limit.')
                tmp.replace(target)
            except BaseException:
                process.kill();process.wait();tmp.unlink(missing_ok=True);raise
            finally:watchdog.cancel()
    return target
