"""Deterministic, inspectable tool-using planner. No LLM or neural video claim."""
from .models import Scene

PALETTES = [['#202635', '#daed97', '#f7f3e8'], ['#322838', '#efadbc', '#f7f3e8'], ['#173e43', '#8ddad3', '#f7f3e8']]

def plan(request, references, evidence):
    sources = evidence['tags'] or evidence['entities']
    briefs = []
    strategies = ['Find the extraordinary', 'Follow a connection', 'Make a small discovery']
    structures = [['Notice', 'Cross a threshold', 'See it differently', 'Leave a question'],
                  ['Two separate worlds', 'A shared detail', 'A small exchange', 'A changed ritual'],
                  ['An ordinary object', 'An unexpected clue', 'A playful experiment', 'The quiet reveal']]
    for index, strategy in enumerate(strategies):
        theme = sources[index % len(sources)]
        movie = evidence['entities'][index % len(evidence['entities'])]
        theme_name = theme['name']
        seconds = request['duration'] // 4
        camera = ['locked', 'push', 'pan', 'orbit'] if request['pace'] == 'energetic' else ['locked', 'push', 'locked', 'pan']
        if request['pace'] == 'reflective': camera = ['locked', 'locked', 'push', 'locked']
        location = 'one familiar room' if request['budget'] == 'phone-only' else 'two nearby locations'
        captions = [f"In {location}, frame a small object that suggests {theme_name.lower()}. Make the first image ask a question.",
                    f"Let a person notice a detail. Explore {theme_name.lower()} through a gesture, without reenacting the reference.",
                    f"Change scale or perspective to connect the detail to: {request['goal']}",
                    f"Return to the opening composition with one visible change. End on {theme_name.lower()}, leaving space for interpretation."]
        scenes = [Scene(title=t, caption=c[:180], seconds=seconds, camera=camera[i], evidence_ids=list(dict.fromkeys([theme['id'], movie['id']]))).model_dump() for i, (t, c) in enumerate(zip(structures[index], captions))]
        briefs.append({'title': f'{theme_name[:45]} / {strategy}', 'strategy': strategy, 'theme': theme_name,
                       'audience_hypothesis': f'For viewers curious about {theme_name.lower()}. This is a creative hypothesis, not a demographic or sensitive-trait inference.',
                       'logline': f"{request['goal']}. A {request['duration']}-second original study of {theme_name.lower()} in {location}.",
                       'visual_direction': f"{request['pace'].capitalize()} pacing; original geometric compositions; a {['citrus and ink','rose and aubergine','lagoon and cream'][index]} palette. EvoVid creative interpretation.",
                       'sound_direction': f"Record original room tone and {['a soft percussive motif','a restrained melodic texture','a gentle rhythmic pulse'][index]}. No reference soundtrack is licensed or included.",
                       'palette': PALETTES[index], 'evidence_ids': list(dict.fromkeys([theme['id'], movie['id']])), 'scenes': scenes,
                       'interpretation': 'EvoVid deterministic creative proposal; these visual, sound and story choices are not Qloo conclusions.'})
    return {'schema_version': 1, 'title': briefs[0]['title'], 'mode': request['mode'], 'references': references,
            'constraints': {k: request[k] for k in ('goal', 'duration', 'aspect', 'pace', 'budget')},
            'evidence': evidence, 'briefs': briefs, 'brief_index': 0, 'scenes': briefs[0]['scenes'],
            'planner': 'evovid-rule-agent-v1', 'version': 1,
            'disclosures': ['Qloo associations are cultural evidence, not probabilities of personal preference.',
                            'Creative planning is deterministic; no language model was called.',
                            'Export is original silent motion-graphic storyboard video, not neural video or licensed reference footage.']}
