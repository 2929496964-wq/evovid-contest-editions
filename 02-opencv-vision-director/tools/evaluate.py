"""Small synthetic evaluation; no invented human preferences or real-world accuracy."""
import sys,json,time,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vision.core import analyze,recommend,render
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence/evaluation';OUT.mkdir(parents=True,exist_ok=True)

def stats(a):
    samples=a['samples'];n=len(samples)
    return {'technical_warning_ratio':round(sum(bool(set(s['flags'])&{'black','underexposed','overexposed','soft'}) for s in samples)/n,4),
            'black_sample_ratio':round(sum('black' in s['flags'] for s in samples)/n,4),
            'low_change_ratio':round(sum(s['motion']<.5 for s in samples[1:])/max(1,n-1),4),
            'mean_luma':round(sum(s['luma'] for s in samples)/n,3),
            'mean_sharpness':round(sum(s['sharpness'] for s in samples)/n,3),
            'histogram_jump_count':sum(s['scene_change']>.55 for s in samples[1:])}
rows=[]
for source in sorted((ROOT/'examples').glob('synthetic-*.mp4')):
    a=analyze(source);target=min(4,a['duration']);base={'approved':True,'clips':[{'start':0,'end':target}]}
    b=render(source,base,a,OUT/source.stem/'baseline')
    plan=recommend(a,target,1);plan['approved']=True
    v=render(source,plan,a,OUT/source.stem/'vision')
    low=recommend(a,target,0);high=recommend(a,target,4)
    rows.append({'file':source.name,'synthetic':True,'duration':a['duration'],'fps':a['fps'],'input':stats(a),
                 'baseline':stats(b['analysis_after']),'vision':stats(v['analysis_after']),
                 'analysis_seconds':a['analysis_seconds'],'baseline_render_seconds':b['render_seconds'],'vision_render_seconds':v['render_seconds'],
                 'plan':plan,'weight0_selection':[c['segment_id'] for c in low['clips']],
                 'weight4_selection':[c['segment_id'] for c in high['clips']],
                 'weight_changed_selection':[c['segment_id'] for c in low['clips']]!=[c['segment_id'] for c in high['clips']],
                 'input_sha256':a['input_sha256'],'baseline_sha256':b['sha256'],'vision_sha256':v['sha256'],
                 'human_preference':None,'cut_quality_human_rating':None})
(OUT/'results.json').write_text(json.dumps({'definition':'Technical warning means a sampled frame is black, underexposed, overexposed or soft. Low change is mean absolute grayscale difference <0.5. Neither is semantic quality. Histogram jumps are not human-rated cut quality.','samples':rows,'limits':'5 synthetic fixtures only; no real-world benchmark or human study. Intentional low light and softness are preserved failure cases.'},indent=2))
with (OUT/'summary.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['file','input_warning_ratio','baseline_warning_ratio','vision_warning_ratio','baseline_seconds','vision_seconds','sharpness_parameter_changes_selection'])
    for r in rows:w.writerow([r['file'],r['input']['technical_warning_ratio'],r['baseline']['technical_warning_ratio'],r['vision']['technical_warning_ratio'],r['baseline_render_seconds'],r['vision_render_seconds'],r['weight_changed_selection']])
print(json.dumps(rows,indent=2))
