"""Real H.264 storyboard rendering, adapted from EvoVid's Pillow+FFmpeg renderer.
No downloaded models, stock footage, external fonts, shell commands or paid services.
"""
from pathlib import Path
import math, os, shutil, subprocess, textwrap, time
from PIL import Image, ImageDraw, ImageFont

def ffmpeg_path():
    exe = shutil.which('ffmpeg')
    if exe: return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError('FFmpeg is not installed. Run the dependency installer or install FFmpeg from its official source.') from None

def font(size):
    candidates = [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\arial.ttf', '/System/Library/Fonts/PingFang.ttc',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for path in candidates:
        if Path(path).is_file(): return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)

def wrap(draw, text, face, width, limit=4):
    lines, line = [], ''
    for ch in text:
        if draw.textlength(line + ch, font=face) > width and line:
            lines.append(line.rstrip()); line = ch.lstrip()
        else: line += ch
    if line: lines.append(line.rstrip())
    if len(lines) > limit: lines = lines[:limit]; lines[-1] = lines[-1][:-2] + '…'
    return lines

def frame(doc, shot_index, progress, width, height):
    brief = doc['briefs'][doc['brief_index']]
    bg, accent, paper = brief['palette']
    im = Image.new('RGB', (width, height), bg)
    draw = ImageDraw.Draw(im)
    scene = doc['scenes'][shot_index]
    margin = int(width * .07)
    scale = width / 640
    titlefont, small = font(max(18, int(24*scale))), font(max(11, int(14*scale)))
    top = int(height * .14)
    orbit = 0 if scene['camera'] == 'locked' else math.sin(progress * math.pi * 1.5)
    cx = width * (.64 + .1 * orbit)
    cy = height * .37
    radius = min(width, height) * (.21 + (.05 * progress if scene['camera'] == 'push' else 0))
    draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=accent)
    draw.line((margin, top+30, width-margin, height*.61), fill=paper, width=2)
    draw.rectangle((margin, top+55, margin+width*.22, top+55+height*.23), outline=paper, width=2)
    draw.text((margin, 20), f'EVOVID / TASTE DIRECTOR       {shot_index+1:02d} / 04', fill=paper, font=small)
    label = 'DEMO FIXTURE / NO QLOO CALLS' if doc['mode'] == 'demo' else 'QLOO LIVE EVIDENCE / EVOVID STORY'
    draw.text((margin, height*.59), label, fill=paper, font=small)
    draw.rounded_rectangle((margin, height*.67, width-margin, height-margin*.5), radius=14, fill=paper)
    y = height*.70
    for line in wrap(draw, scene['title'], titlefont, width-margin*2-28, 1 if width > height else 2):
        draw.text((margin+14, y), line, fill=bg, font=titlefont); y += titlefont.size+3
    for line in wrap(draw, scene['caption'], small, width-margin*2-28, 3 if height > width else 2):
        draw.text((margin+14, y+4), line, fill=bg, font=small); y += small.size+4
    draw.rectangle((0, height-5, width*((shot_index+progress)/4), height), fill=accent)
    return im

def render(doc, target, stop=lambda: False, emit=lambda x: None):
    dimensions = {'16:9': (640, 360), '9:16': (360, 640), '1:1': (480, 480)}
    width, height = dimensions[doc['constraints']['aspect']]
    fps = 15
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.partial.mp4')
    proc = subprocess.Popen([ffmpeg_path(), '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-pix_fmt', 'rgb24', '-s', f'{width}x{height}', '-r', str(fps), '-i', 'pipe:0', '-an', '-c:v', 'libx264',
        '-threads', '2', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(temp)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    start = time.monotonic()
    try:
        for index, scene in enumerate(doc['scenes']):
            for n in range(scene['seconds']*fps):
                if stop(): raise InterruptedError('Render cancelled.')
                if time.monotonic()-start > 120: raise RuntimeError('Render exceeded the two-minute time limit.')
                proc.stdin.write(frame(doc, index, n/(scene['seconds']*fps), width, height).tobytes())
            emit({'shot': index+1, 'shots': 4, 'progress': (index+1)/4})
        proc.stdin.close()
        if proc.wait(timeout=15) != 0: raise RuntimeError('FFmpeg could not encode the video.')
        if stop(): raise InterruptedError('Render cancelled.')
        temp.replace(target)
        return {'width': width, 'height': height, 'fps': fps, 'seconds': sum(x['seconds'] for x in doc['scenes']), 'bytes': target.stat().st_size,
                'format': 'H.264 MP4', 'audio': 'silent', 'render_type': 'original motion-graphic storyboard'}
    except BrokenPipeError:
        raise RuntimeError('FFmpeg stopped before encoding completed.') from None
    finally:
        if proc.poll() is None: proc.kill(); proc.wait(timeout=5)
        temp.unlink(missing_ok=True)
