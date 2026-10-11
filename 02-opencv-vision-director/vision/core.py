"""Explainable vision analysis and a human-approved FFmpeg edit plan.
OpenCV5 guard derived from EvoVid Pocket desktop/evovid/vision.py (MIT).
"""
from __future__ import annotations
import cv2
import numpy as np
from pathlib import Path
import hashlib, importlib.metadata, json, math, os, platform, shutil, subprocess, sys, time
from .upstream_vision import require_opencv5

MAX_SECONDS = 180.0
MAX_PIXELS = 1920 * 1080
SAMPLE_HZ = 4


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def ffmpeg():
    p = shutil.which('ffmpeg')
    if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError: raise RuntimeError('FFmpeg is missing. Run the start script to install the bundled runtime.')


def version_evidence():
    require_opencv5()
    return {'opencv': cv2.__version__, 'package': importlib.metadata.version('opencv-python-headless'),
            'python': platform.python_version(), 'platform': platform.platform(), 'python_executable': sys.executable,
            'cv2_file': cv2.__file__, 'ffmpeg': subprocess.check_output([ffmpeg(), '-version'], text=True).splitlines()[0],
            'execution_environment': os.getenv('VISION_EXECUTION_ENV', 'local'),
            'aws_execution_verified': False}


def metrics(frame, previous=None):
    # Maintain aspect ratio: do not warp landscape/portrait differently.
    h, w = frame.shape[:2]
    small = cv2.resize(frame, (max(2, round(w*min(1, 480/w))), max(2, round(h*min(1,480/w)))))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [32], [0,256])
    cv2.normalize(hist, hist, alpha=1, norm_type=cv2.NORM_L1)
    out = {'luma': float(gray.mean()), 'sharpness': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
           'black_fraction': float((gray < 12).mean()), 'white_fraction': float((gray > 245).mean()),
           'motion': 0.0, 'scene_change': 0.0}
    if previous is not None:
        pg, ph = previous
        out['motion'] = float(cv2.absdiff(gray, pg).mean())
        out['scene_change'] = float(cv2.compareHist(hist, ph, cv2.HISTCMP_BHATTACHARYYA))
    return {k: round(v,5) for k,v in out.items()}, (gray,hist)


def flags(m):
    out=[]
    if m['black_fraction'] > .95: out.append('black')
    elif m['luma'] < 40: out.append('underexposed')
    if m['white_fraction'] > .7: out.append('overexposed')
    if m['sharpness'] < 65: out.append('soft')
    if m['motion'] > 35: out.append('motion')
    if m['scene_change'] > .55: out.append('scene_change')
    return out


def analyze(path, folder=None, stop=lambda:False, progress=lambda x:None):
    require_opencv5(); started=time.monotonic()
    with open(path,'rb') as source:
        magic=source.read(32)
    is_video=(magic.startswith(b'RIFF') and magic[8:12]==b'AVI ') or magic.startswith(b'\x1aE\xdf\xa3') or magic[4:8] in [b'ftyp',b'moov',b'mdat',b'wide',b'free']
    if not is_video: raise ValueError('Unsupported container signature. Upload MP4/MOV, AVI, MKV or WebM; playlists and URLs are not accepted.')
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']='protocol_whitelist;file,pipe'
    cap=cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened(): raise ValueError('Video cannot be decoded. Use a valid MP4, MOV, MKV, AVI or WebM.')
        fps=float(cap.get(cv2.CAP_PROP_FPS)); count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if not math.isfinite(fps) or fps<=0 or count<=0 or min(w,h)<=0: raise ValueError('Invalid video metadata.')
        duration=count/fps
        if duration>MAX_SECONDS or w*h>MAX_PIXELS or max(w,h)>3840: raise ValueError('Limit: 180 seconds and 1920×1080 pixels (portrait supported).')
        if fps>120: raise ValueError('Limit: 120 frames per second.')
        samples=[]; previous=None; step=max(1,round(fps/SAMPLE_HZ)); idx=0
        # Sequential decoding produces correct sample ordering, unlike metadata-only seeks.
        while True:
            if stop(): raise InterruptedError('Cancelled by user; original video is retained.')
            if time.monotonic()-started>240: raise TimeoutError('Analysis exceeded 240 seconds.')
            ok,frame=cap.read()
            if not ok: break
            if idx>=round(MAX_SECONDS*fps)+2: raise ValueError('Decoded video exceeds duration limit.')
            if idx%step==0:
                m,previous=metrics(frame,previous)
                pts=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                # Some AVI decoders provide zero PTS; record explicit fallback.
                t=pts if math.isfinite(pts) and (pts>0 or idx==0) else idx/fps
                m.update({'frame':idx,'time':round(t,5),'timestamp_source':'decoder_pts' if pts>0 or idx==0 else 'frame_index_fps'})
                m['flags']=flags(m); samples.append(m)
                if folder is not None and len(samples)%4==1:
                    thumb=cv2.resize(frame,(320,max(2,round(h*320/w))))
                    cv2.imwrite(str(Path(folder)/f'frame-{len(samples)-1:04d}.jpg'),thumb)
                progress(min(90, int(90*idx/max(1,count))))
            idx+=1
        if not samples: raise ValueError('No decodable video frames.')
        if idx < count*.98: raise ValueError(f'Incomplete decoding: {idx} of {count} declared frames. Original retained.')
        duration=idx/fps
        segments=[]
        # One-second review bins bound cut decisions; metrics retain quarter-second observations.
        for i in range(math.ceil(duration)):
            ss=[s for s in samples if i<=s['time']<min(i+1,duration)]
            if not ss: continue
            avg={k:round(float(np.mean([s[k] for s in ss])),5) for k in ['luma','sharpness','black_fraction','white_fraction','motion','scene_change']}
            fs=flags(avg)
            suggestions=[]
            if 'black' in fs: suggestions.append('Omit unless this black interval is intentional.')
            if 'underexposed' in fs: suggestions.append('Review moderate exposure lift; clipped shadow detail cannot be recovered.')
            if 'overexposed' in fs: suggestions.append('Review exposure reduction; blown highlights cannot be recovered.')
            if 'soft' in fs: suggestions.append('Review softness; gentle sharpening improves edges, not lost detail.')
            if 'motion' in fs: suggestions.append('Review high motion; intentional camera movement is not a defect.')
            if not suggestions: suggestions.append('No strong technical warning at the sampled instants.')
            segments.append({'id':i,'start':float(i),'end':round(min(i+1,duration),5),'metrics':avg,'flags':fs,
                             'suggestions':suggestions,'sample_count':len(ss)})
        return {'duration':round(duration,5),'fps':fps,'width':w,'height':h,'decoded_frames':idx,'sample_hz_requested':SAMPLE_HZ,
                'sample_count':len(samples),'samples':samples,'segments':segments,'analysis_seconds':round(time.monotonic()-started,4),
                'input_sha256':digest(path),'versions':version_evidence(),
                'limitations':['Heuristic warnings are not semantic judgments; review creative intent.',
                              'Four samples/second can miss brief defects. One-second bins can include a transition.',
                              'Exposure cannot restore clipped detail; sharpening is not deblurring.',
                              'High motion can be intentional. Histogram distance can confuse lighting with a cut.',
                              'Frame-count/FPS duration assumes constant frame rate; VFR accuracy needs manual review.']}
    finally: cap.release()


def recommend(analysis, target=10, sharpness_weight=1.0):
    target=max(.04,min(float(target),analysis['duration']))
    ranked=[]
    for s in analysis['segments']:
        m=s['metrics']; score=50 - abs(m['luma']-120)*.15 - m['black_fraction']*100 - m['white_fraction']*50
        score+=float(sharpness_weight)*min(50,math.log1p(m['sharpness'])*8)
        ranked.append((score,s))
    remain=target; chosen=[]
    for score,s in sorted(ranked,key=lambda x:(-x[0],x[1]['start'])):
        if remain<.001: break
        take=min(remain,s['end']-s['start']); remain-=take
        chosen.append({'segment_id':s['id'],'start':s['start'],'end':round(s['start']+take,5),
                       'exposure':0.0,'sharpen':False,'score':round(score,3),
                       'reason':f"Quality score {score:.1f}; luma {s['metrics']['luma']:.1f}, sharpness {s['metrics']['sharpness']:.1f}. Warnings: {', '.join(s['flags']) or 'none'}."})
    chosen.sort(key=lambda x:x['start'])
    return {'clips':chosen,'target_seconds':target,'sharpness_weight':float(sharpness_weight),'approved':False,
            'policy':'Quality-ranked one-second bins, chronological output. User confirmation required.',
            'excluded':[{'segment_id':s['id'],'score':round(score,3),'reason':'Below target-duration selection cutoff.'}
                        for score,s in ranked if s['id'] not in {c['segment_id'] for c in chosen}]}


def validate_plan(plan, analysis):
    clips=plan.get('clips',[])
    if plan.get('approved') is not True: raise ValueError('Explicit human approval is required.')
    if not isinstance(clips,list) or not 1<=len(clips)<=180: raise ValueError('Select between 1 and 180 clips.')
    total=0; prev_end=0
    clean=[]
    for c in clips:
        start=float(c['start']); end=float(c['end']); exposure=float(c.get('exposure',0))
        if not all(math.isfinite(v) for v in [start,end,exposure]): raise ValueError('Plan numbers must be finite.')
        if not (0<=start<end<=analysis['duration']+.001) or end-start<1/analysis['fps']-.0001: raise ValueError('Invalid clip time range.')
        if start<prev_end-.0001: raise ValueError('Clips must be chronological and non-overlapping.')
        if not -.25<=exposure<=.25: raise ValueError('Exposure must be between -0.25 and 0.25.')
        total+=end-start; prev_end=end
        clean.append({'start':start,'end':end,'exposure':exposure,'sharpen':bool(c.get('sharpen',False)),
                      'segment_id':c.get('segment_id'),'reason':str(c.get('reason','Human-selected'))[:500]})
    if total>MAX_SECONDS+.01: raise ValueError('Output exceeds 180 seconds.')
    return {'clips':clean,'approved':True,'expected_duration':round(total,5),'approved_at':time.time()}


def run_process(command, logfile, stop, timeout=300):
    began=time.monotonic()
    with open(logfile,'ab') as log:
        log.write(('\nARGV '+json.dumps(command)+'\n').encode()); log.flush()
        proc=subprocess.Popen(command,stdout=log,stderr=log)
        try:
            while proc.poll() is None:
                if stop(): raise InterruptedError('Cancelled by user; original and attempt logs retained.')
                if time.monotonic()-began>timeout: raise TimeoutError('Render exceeded time limit.')
                time.sleep(.05)
            if proc.returncode: raise RuntimeError(f'FFmpeg failed with exit {proc.returncode}. See attempt log.')
        except BaseException:
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
            raise


def render(source, plan, analysis, outdir, stop=lambda:False, progress=lambda x:None):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    plan=validate_plan(plan,analysis); (outdir/'approved-plan.json').write_text(json.dumps(plan,indent=2))
    parts=[]; began=time.monotonic()
    for i,c in enumerate(plan['clips']):
        if stop(): raise InterruptedError('Cancelled by user.')
        target=outdir/f'clip-{i:03}.mp4'
        vf=['scale=trunc(iw/2)*2:trunc(ih/2)*2','setsar=1',f"eq=brightness={c['exposure']:.5f}"]
        if c['sharpen']: vf.append('unsharp=5:5:0.5:5:5:0')
        vf.append(f"fps={analysis['fps']:.6f}")
        command=[ffmpeg(),'-hide_banner','-loglevel','warning','-nostdin','-y','-protocol_whitelist','file,pipe','-ss',f"{c['start']:.6f}",'-i',str(source),
                 '-t',f"{c['end']-c['start']:.6f}",'-map','0:v:0','-map','0:a:0?','-vf',','.join(vf),
                 '-c:v','libx264','-preset','veryfast','-crf','20','-threads','2','-pix_fmt','yuv420p',
                 '-c:a','aac','-b:a','128k','-af','aresample=async=1:first_pts=0','-movflags','+faststart',str(target)]
        run_process(command,outdir/'ffmpeg.log',stop); parts.append(target)
        progress(int(80*(i+1)/len(plan['clips'])))
    # Generated relative basenames only; user input never reaches concat grammar.
    listing=outdir/'concat.txt'; listing.write_text(''.join(f"file '{p.name}'\n" for p in parts))
    result=outdir/'output.mp4'
    command=[ffmpeg(),'-hide_banner','-loglevel','warning','-nostdin','-y','-f','concat','-safe','1','-i',str(listing),
             '-map','0:v:0','-map','0:a:0?','-c','copy','-movflags','+faststart',str(result)]
    run_process(command,outdir/'ffmpeg.log',stop)
    check=analyze(result,stop=stop)
    tolerance=max(.5,len(parts)/analysis['fps']+.15)
    if abs(check['duration']-plan['expected_duration'])>tolerance: raise RuntimeError('Output duration check failed; attempt retained.')
    return {'file':'output.mp4','sha256':digest(result),'duration':check['duration'],'expected_duration':plan['expected_duration'],
            'tolerance_seconds':tolerance,'render_seconds':round(time.monotonic()-began,4),'analysis_after':check,
            'audio_policy':'First audio stream retained and AAC encoded when present. Check sync manually, especially VFR.',
            'plan':plan}
