"""Real local OpenAI-compatible adapter; the offline alternative is always labeled."""
import hashlib, json, re, time
import httpx
from .models import Board, Scene

def plan(brief, mode, settings, client=None):
    started = time.time()
    if mode == 'fixture':
        topic = brief.split('.')[0].strip()[:65]
        board = Board(title=topic[:80], scenes=[
            Scene(title='Small batch. Big possibility.', caption=topic[:140], seconds=3, accent='lime'),
            Scene(title='Made with intention.', caption='A fictional creator story, built one thoughtful frame at a time.', seconds=3, accent='violet'),
            Scene(title='From idea to first impression.', caption='Your story. Your rhythm. A little momentum.', seconds=3, accent='cyan'),
            Scene(title='Make something worth sharing.', caption='NORTHLIGHT / An original fictional launch concept', seconds=3, accent='orange')])
        provider = 'DEMO FIXTURE / deterministic template, not AI'
        model = 'fixture-v1'
    else:
        if not settings.ai_model: raise ValueError('Set AI_MODEL to the model already running in your local service, then restart.')
        provider, model = 'local OpenAI-compatible API', settings.ai_model
        c = client or httpx.Client(timeout=httpx.Timeout(45,connect=5),follow_redirects=False,trust_env=False)
        try:
            response = c.post(settings.ai_url.rstrip('/')+'/chat/completions', headers={'Authorization':'Bearer '+settings.ai_key} if settings.ai_key else {}, json={
                'model':model, 'temperature':0.4, 'max_tokens':1600,
                'messages':[{'role':'system','content':'Create an original fictional promotional motion-graphics storyboard. No asset URLs, files or commands. Return ONLY JSON matching this schema. Total duration at most 24 seconds. '+json.dumps(Board.model_json_schema())}, {'role':'user','content':brief}]})
            response.raise_for_status()
            if len(response.content)>100000: raise ValueError('Model response exceeded the safe size limit.')
            content = response.json()['choices'][0]['message']['content']
            if not isinstance(content,str) or len(content)>20000: raise ValueError('Invalid model response.')
            content = re.sub(r'^```(?:json)?\s*|\s*```$','',content.strip())
            board = Board.model_validate_json(content)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError('Local AI did not return a valid storyboard. Check the local service and model. No fixture was substituted.') from exc
        finally:
            if client is None:c.close()
    serialized=json.dumps(board.model_dump(),sort_keys=True,ensure_ascii=False)
    return board, {'provider':provider,'model':model,'online_model_call':mode=='local-ai','elapsed_ms':round((time.time()-started)*1000),
        'input_sha256':hashlib.sha256(brief.encode()).hexdigest(),'output_sha256':hashlib.sha256(serialized.encode()).hexdigest()}
