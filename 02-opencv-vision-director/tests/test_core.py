import json, math
from pathlib import Path
import cv2, numpy as np, pytest
from vision.core import metrics, flags, analyze, recommend, validate_plan, render
ROOT=Path(__file__).resolve().parents[1]

def test_real_version():
    assert cv2.__version__=='5.0.0'

def test_metric_directions():
    rng=np.random.default_rng(47); sharp=rng.integers(30,230,(180,320,3),dtype=np.uint8)
    soft=cv2.GaussianBlur(sharp,(31,31),10)
    a,_=metrics(sharp); b,_=metrics(soft); black,_=metrics(np.zeros_like(sharp)); white,_=metrics(np.full_like(sharp,255))
    assert a['sharpness']>b['sharpness']*10
    assert 'black' in flags(black)
    assert 'overexposed' in flags(white)

def test_black_scene():
    a=analyze(ROOT/'examples/synthetic-all-black.mp4')
    assert a['sample_count']>=10
    assert all('black' in s['flags'] for s in a['segments'])

def test_noisy_metadata_and_empty(tmp_path):
    p=tmp_path/'bad.mp4';p.write_bytes(b'not a video')
    with pytest.raises(ValueError): analyze(p)

def test_stop():
    with pytest.raises(InterruptedError): analyze(ROOT/'examples/synthetic-quality-lab.mp4',stop=lambda:True)

def test_parameter_causes_selection():
    # Controlled metrics isolate causal effect of sharpness preference.
    a={'duration':2,'segments':[{'id':0,'start':0,'end':1,'metrics':{'luma':120,'sharpness':1,'black_fraction':0,'white_fraction':0},'flags':['soft']},
       {'id':1,'start':1,'end':2,'metrics':{'luma':100,'sharpness':400,'black_fraction':0,'white_fraction':0},'flags':[]}]}
    assert recommend(a,1,0)['clips'][0]['segment_id']==0
    assert recommend(a,1,4)['clips'][0]['segment_id']==1

@pytest.mark.parametrize('approval',[False,'false','true',1,None])
def test_approval_must_be_boolean(approval):
    with pytest.raises(ValueError): validate_plan({'approved':approval,'clips':[{'start':0,'end':1}]},{'duration':2,'fps':24})

@pytest.mark.parametrize('clip',[{'start':-1,'end':1},{'start':0,'end':999},{'start':0,'end':1,'exposure':9},{'start':float('nan'),'end':1}])
def test_bad_plans(clip):
    with pytest.raises(ValueError):validate_plan({'approved':True,'clips':[clip]},{'duration':2,'fps':24})

def test_decode_render_actual(tmp_path):
    source=ROOT/'examples/synthetic-quality-lab.mp4';a=analyze(source)
    plan={'approved':True,'clips':[{'start':2,'end':4,'exposure':.2,'sharpen':False}]}
    r=render(source,plan,a,tmp_path)
    assert (tmp_path/'output.mp4').stat().st_size>1000
    assert abs(r['duration']-2)<.15
    original_luma=np.mean([s['luma'] for s in a['samples'] if 2<=s['time']<4])
    assert np.mean([s['luma'] for s in r['analysis_after']['samples']])>original_luma+20
    assert source.exists()

def test_silent_and_bundled_runtime(tmp_path,monkeypatch):
    import subprocess
    import vision.core as core
    import imageio_ffmpeg
    source=ROOT/'examples/synthetic-quality-lab.mp4'
    silent=tmp_path/'silent.mp4'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y','-i',str(source),'-t','1','-an','-c:v','copy',str(silent)],check=True)
    monkeypatch.setattr(core.shutil,'which',lambda _:None)
    a=analyze(silent)
    r=render(silent,{'approved':True,'clips':[{'start':0,'end':.5}]},a,tmp_path/'bundled')
    assert .4<r['duration']<.7
    assert '7.0.2' in r['analysis_after']['versions']['ffmpeg']


def test_playlist_rejected_before_decode(tmp_path):
    p=tmp_path/'playlist.media';p.write_bytes(b'#EXTM3U\n#EXTINF:1,\nhttps://example.invalid/secret.mp4\n')
    with pytest.raises(ValueError,match='signature'): analyze(p)
