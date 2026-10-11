"""Minimal official REST adapter. Fixed host, whitelist, no redirects or personal signals."""
from datetime import datetime, timezone
from uuid import UUID
import json, math, threading, time
import httpx
from . import fixtures

BASE_URL = 'https://hackathon.api.qloo.com'
class ProviderError(Exception):
    def __init__(self, code, message, status=502):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status

def now():
    return datetime.now(timezone.utc).isoformat()

def score(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None

def normalize_entity(item, rank=None):
    if not isinstance(item, dict):
        raise ProviderError('schema', 'Qloo returned an invalid entity record.')
    try:
        eid = str(UUID(item['entity_id']))
        name = item['name']
        subtype = item.get('subtype', item.get('type'))
        if not isinstance(name, str) or not 1 <= len(name) <= 200 or subtype not in ('urn:entity:movie', 'urn:entity:artist'):
            raise ValueError()
        props = item.get('properties') or {}
        query = item.get('query') or {}
        year = props.get('release_year')
        result = {'id': eid, 'name': name, 'category': subtype.split(':')[-1], 'year': year if isinstance(year, int) else None}
        if rank is not None:
            # Overall affinity is distinct from per-input explainability contributions.
            result.update(rank=rank, affinity=score(query.get('affinity')), explainability=safe_explanation(query.get('explainability')))
        return result
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ProviderError('schema', 'Qloo entity schema did not match the documented ID/name/type contract.') from None

def safe_explanation(value, depth=0):
    """Only UUID keys/values, numeric contributions and known structural keys survive."""
    if depth > 5:
        return None
    if isinstance(value, (int, float)):
        return score(value)
    if isinstance(value, list):
        return [safe_explanation(x, depth+1) for x in value[:10]]
    if isinstance(value, str):
        try: return str(UUID(value))
        except ValueError: return None
    if isinstance(value, dict):
        allowed = {'entities', 'entity_id', 'score', 'contribution', 'value', 'signal', 'interests', 'signal.interests.entities', 'top_3', 'top_5', 'top_10', 'all'}
        out = {}
        for k, v in list(value.items())[:25]:
            try: UUID(k); valid = True
            except (ValueError, TypeError): valid = k in allowed
            if valid:
                cleaned = safe_explanation(v, depth+1)
                if cleaned is not None: out[k] = cleaned
        return out or None
    return None

class Qloo:
    def __init__(self, key='', transport=None, hourly_limit=100):
        self.key = key
        self.transport = transport
        self.source = 'contract_mock' if transport is not None else 'live_http'
        self.hourly_limit = hourly_limit
        self.calls = []
        self.lock = threading.Lock()

    def ready(self, mode):
        if mode == 'live' and not self.key:
            raise ProviderError('missing_key', 'LIVE is unavailable: the server owner must configure an authorized QLOO_API_KEY. Choose DEMO explicitly to explore fixtures.', 503)

    def _request(self, path, params, emit, stop):
        self.ready('live')
        if stop(): raise InterruptedError('Cancelled.')
        with self.lock:
            stamp = time.monotonic()
            self.calls = [x for x in self.calls if x > stamp - 3600]
            if len(self.calls) >= self.hourly_limit:
                raise ProviderError('local_quota', 'This demo has reached its local hourly Qloo request budget. Try later.', 429)
            self.calls.append(stamp)
        record = {'at': now(), 'provider': 'Qloo', 'mode': 'live', 'source': self.source, 'actual_http_call': self.transport is None,
                  'method': 'GET', 'host': BASE_URL, 'path': path, 'params': params, 'cache': False}
        try:
            with httpx.Client(transport=self.transport, timeout=httpx.Timeout(15, connect=5), follow_redirects=False, trust_env=False) as client:
                with client.stream('GET', BASE_URL + path, params=params,
                                   headers={'X-Api-Key': self.key, 'Accept': 'application/json'}) as response:
                    record['http_status'] = response.status_code
                    if response.status_code != 200:
                        emit({**record, 'outcome': 'error'})
                        if response.status_code in (401, 403):
                            raise ProviderError('authentication', 'Qloo rejected the server credential. No fixture fallback was used.', 502)
                        if response.status_code == 429:
                            raise ProviderError('rate_limited', 'Qloo rate limit reached. Wait, then retry explicitly. No automatic retry was made.', 429)
                        if response.status_code == 404 and path == '/search': return {'results': []}
                        raise ProviderError('upstream', f'Qloo returned HTTP {response.status_code}. The run stopped; try again later.')
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        if stop(): raise InterruptedError('Cancelled.')
                        size += len(chunk)
                        if size > 2_000_000: raise ProviderError('response_limit', 'Qloo response exceeded the safe size limit.')
                        chunks.append(chunk)
                    data = json.loads(b''.join(chunks))
            if not isinstance(data, dict) or data.get('success') is False:
                raise ProviderError('schema', 'Qloo returned an unsuccessful or invalid response.')
            record['outcome'] = 'success'
            emit(record)
            return data
        except httpx.TimeoutException:
            emit({**record, 'outcome': 'timeout'})
            raise ProviderError('timeout', 'Qloo timed out. No automatic retry or fixture fallback was made.', 504) from None
        except httpx.HTTPError:
            emit({**record, 'outcome': 'network_error'})
            raise ProviderError('network', 'Qloo could not be reached securely. Check connectivity; no fallback was used.') from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            emit({**record, 'outcome': 'invalid_json'})
            raise ProviderError('schema', 'Qloo returned invalid JSON.') from None

    def search(self, query, category, mode, emit=lambda x: None, stop=lambda: False):
        self.ready(mode)
        if mode == 'demo':
            values = fixtures.search(query, category)
            emit({'at': now(), 'mode': 'demo', 'source': 'demo_fixture', 'actual_http_call': False, 'operation': 'search', 'result_ids': [x['id'] for x in values]})
            return values
        data = self._request('/search', {'query': query, 'types': 'urn:entity:' + category, 'take': 5}, emit, stop)
        rows = data.get('results')
        if isinstance(rows, dict): rows = rows.get('entities')
        if not isinstance(rows, list): raise ProviderError('schema', 'Qloo search response is missing its results array.')
        values = [normalize_entity(x) for x in rows[:5]]
        values = [x for x in values if x['category'] == category]
        emit({'at': now(), 'mode': mode, 'operation': 'normalized_search', 'result_ids': [x['id'] for x in values]})
        return values

    def insights(self, ids, mode, emit=lambda x: None, stop=lambda: False):
        self.ready(mode)
        if mode == 'demo':
            data = fixtures.insights(ids)
            emit({'at': now(), 'mode': mode, 'source': 'demo_fixture', 'actual_http_call': False, 'operation': 'insights', 'input_ids': ids,
                  'result_ids': [x['id'] for x in data['entities']] + [x['id'] for x in data['tags']]})
            return data
        common = {'signal.interests.entities': ','.join(str(UUID(x)) for x in ids), 'take': 5}
        movie_data = self._request('/v2/insights', {**common, 'filter.type': 'urn:entity:movie', 'feature.explainability': 'true'}, emit, stop)
        rows = (movie_data.get('results') or {}).get('entities')
        if not isinstance(rows, list): raise ProviderError('schema', 'Qloo Insights response is missing results.entities.')
        movies = [normalize_entity(x, i+1) for i, x in enumerate(rows[:5])]
        if not movies: raise ProviderError('empty_results', 'Qloo returned no cultural associations. Change your public references and replan.', 422)
        tags_data = self._request('/v2/insights', {**common, 'filter.type': 'urn:tag', 'filter.tag.types': 'urn:tag:keyword:media',
                                    'filter.parents.types': 'urn:entity:movie,urn:entity:tv_show'}, emit, stop)
        tag_rows = (tags_data.get('results') or {}).get('tags')
        if not isinstance(tag_rows, list): raise ProviderError('schema', 'Qloo Insights response is missing results.tags.')
        tags = []
        for i, row in enumerate(tag_rows[:5]):
            tid, name = row.get('tag_id'), row.get('name')
            if not isinstance(tid, str) or not tid.startswith('urn:tag:keyword:media:') or len(tid) > 250 or not isinstance(name, str) or not 1 <= len(name) <= 200:
                raise ProviderError('schema', 'Qloo returned an invalid media tag.')
            tags.append({'id': tid, 'name': name, 'rank': i+1, 'affinity': score((row.get('query') or {}).get('affinity'))})
        warnings = []
        if not tags: warnings.append('Qloo returned no theme tags. Briefs use returned entity names; no tags were invented.')
        explanation = (movie_data.get('query') or {}).get('explainability') or {}
        if isinstance(explanation, dict) and explanation.get('warning'):
            warnings.append('Qloo reported that explainability was unavailable for this request.')
        if not any(x['explainability'] for x in movies): warnings.append('No supported per-input explainability contributions were returned. Rank and affinity remain separate.')
        emit({'at': now(), 'mode': mode, 'operation': 'normalized_insights', 'result_ids': [x['id'] for x in movies] + [x['id'] for x in tags]})
        return {'entities': movies, 'tags': tags, 'warnings': warnings, 'source': self.source}
