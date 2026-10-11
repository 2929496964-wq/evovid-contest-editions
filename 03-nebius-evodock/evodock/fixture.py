"""Explicit deterministic fixture. This is not an LLM and not Nebius evidence."""
import copy,re
from .models import Storyboard

def fixture(brief,previous=None,instruction=''):
    if previous:
        b=copy.deepcopy(previous);low=instruction.lower()
        if any(x in low for x in ('short','快','短')):
            for s in b['scenes']:s['seconds']=max(2,s['seconds']-1)
        elif any(x in low for x in ('reverse','倒','反转')):b['scenes'].reverse()
        elif any(x in low for x in ('warm','暖')):
            for s in b['scenes']:s['color']='amber'
        else:
            b['scenes'][-1]['caption']=instruction[:180]
        return Storyboard.model_validate(b)
    low=brief.lower();asset='nature' if any(w in low for w in ['nature','garden','forest','自然','花园']) else 'orbit' if any(w in low for w in ['space','orbit','太空']) else 'product'
    cleaned=' '.join(brief.split())
    title=cleaned[:65]
    rows=[('s1','Make room for an idea',cleaned if len(cleaned)<=180 else cleaned[:177]+'...',4,'rise'),('s2','See it take shape','A clear rhythm. One considered detail at a time.',5,'drift'),('s3','Bring the story home','Start small. Create something that lasts.',4,'pulse')]
    return Storyboard(title=title,scenes=[dict(id=i,asset_id=asset if n<2 else 'type',title=t,caption=c,seconds=s,motion=m,color=['mint','sky','violet'][n]) for n,(i,t,c,s,m) in enumerate(rows)])
