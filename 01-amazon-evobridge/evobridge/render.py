"""Pillow motion graphics → an actual H.264 MP4. Adapted from EvoVid render concepts.
No neural text-to-video, network access or shell interpolation.
"""
from pathlib import Path
import math
import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageOps


def ffmpeg_path():
    binary = shutil.which('ffmpeg')
    if binary:
        return binary
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        raise RuntimeError('FFmpeg unavailable. Install requirements.lock or FFmpeg.') from e


def font_path():
    paths = [os.getenv('EVOBRIDGE_FONT', ''), r'C:\Windows\Fonts\msyh.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/System/Library/Fonts/PingFang.ttc', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', r'C:\Windows\Fonts\arial.ttf']
    return next((p for p in paths if p and Path(p).is_file()), None)


def font(size):
    path = font_path()
    return ImageFont.truetype(path, size) if path else ImageFont.load_default(size=size)


def wrap(draw, value, f, width, max_lines):
    lines, current = [], ''
    for char in value:
        if char == '\n' or draw.textlength(current + char, font=f) > width:
            lines.append(current)
            current = '' if char == '\n' else char
        else:
            current += char
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-2] + '…'
    return lines


def frame(project, scene, index, t, size, assets_dir):
    w, h = size
    portrait = h > w
    scale = w / (720 if portrait else 960)
    im = Image.new('RGB', size, '#142b34')
    draw = ImageDraw.Draw(im)
    accent = scene['color']
    if scene.get('asset'):
        path = Path(assets_dir) / (scene['asset'] + '.jpg')
        if path.is_file():
            with Image.open(path) as asset:
                z = 1 + .05 * t
                bg = ImageOps.fit(asset.convert('RGB'), (int(w * z), int(h * z)))
                im.paste(bg, (-int(w * (z - 1) / 2), -int(h * (z - 1) / 2)))
            veil = Image.new('RGBA', size, (13, 32, 42, 155))
            im = Image.alpha_composite(im.convert('RGBA'), veil).convert('RGB')
            draw = ImageDraw.Draw(im)
    else:
        drift = (t - .5) * w * .15
        radius = w * (.33 + .025 * math.sin(t * math.pi * 2)) if scene['motion'] == 'pulse' else w * .34
        cx, cy = w * .84 + drift, h * .2 + (h * .10 * (1 - t) if scene['motion'] == 'rise' else 0)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=accent)
        draw.ellipse((w * .66, h * .10, w * .91, h * .10 + w * .25), outline='#f0d5b2', width=max(2, int(2 * scale)))
        draw.line((w * .77, 0, w * .77, h), fill='#39515a', width=1)
    pad = int(w * .073)
    draw.text((pad, int(h * .065)), f'EVOBRIDGE  /  {index + 1:02d}', font=font(int(17 * scale)), fill='#dfb395')
    entrance = max(0.0, 1.0 - t / .22)
    y = int(h * (.36 if portrait else .29) + (24 * scale * entrance if scene['motion'] == 'rise' else 0))
    text_x = pad + int(24 * scale * entrance if scene['motion'] == 'drift' else 0)
    f = font(int((52 if not portrait else 55) * scale))
    for line in wrap(draw, scene['title'], f, w - pad * 2, 3):
        draw.text((text_x, y), line, font=f, fill='#fffaf0')
        y += int(72 * scale)
    draw.rounded_rectangle((pad, h - int(145 * scale), w - pad, h - int(38 * scale)), radius=int(16 * scale), fill='#f4efe3')
    f = font(int(23 * scale))
    y = h - int(124 * scale)
    for line in wrap(draw, scene['caption'], f, w - pad * 2 - int(38 * scale), 2):
        draw.text((pad + int(20 * scale), y), line, font=f, fill='#19323a')
        y += int(32 * scale)
    progress = ((sum(s['seconds'] for s in project['scenes'][:index]) + scene['seconds'] * t) / project['duration'])
    draw.rectangle((0, h - max(3, int(5 * scale)), int(w * progress), h), fill=accent)
    # Deterministic fade-in, visible in the MP4 rather than a static slide export.
    if t < .1:
        im = Image.blend(Image.new('RGB', size, '#142b34'), im, min(1, t / .1))
    return im


def render(project, target, assets_dir, stop=lambda: False, progress=lambda p: None, fps=20):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    size = (960, 540) if project['format'] == 'landscape' else (540, 960)
    total = sum(s['seconds'] for s in project['scenes']) * fps
    temporary = target.with_name(target.stem + '.partial.mp4')
    cmd = [ffmpeg_path(), '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{size[0]}x{size[1]}', '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-threads', '2', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(temporary)]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) as proc:
        try:
            counter = 0
            for i, scene in enumerate(project['scenes']):
                for n in range(scene['seconds'] * fps):
                    if stop():
                        raise InterruptedError('Render cancelled; no output was published.')
                    im = frame(project, scene, i, n / max(1, scene['seconds'] * fps - 1), size, assets_dir)
                    proc.stdin.write(im.tobytes())
                    counter += 1
                    if counter % fps == 0:
                        progress(round(95 * counter / total))
            proc.stdin.close()
            proc.stdin = None
            _, err = proc.communicate(timeout=60)
            if proc.returncode:
                raise RuntimeError('FFmpeg failed: ' + err.decode(errors='replace')[-400:])
            if stop():
                raise InterruptedError('Render cancelled; no output was published.')
            temporary.replace(target)
            progress(100)
        except BaseException:
            proc.kill()
            proc.wait()
            temporary.unlink(missing_ok=True)
            raise
    return target
