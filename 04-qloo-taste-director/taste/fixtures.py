"""Authored synthetic fixtures: IDs, affinities and associations are NOT Qloo output."""
from uuid import UUID

def entity(n, name, category='movie', year=None):
    return {'id': str(UUID(int=n)), 'name': name, 'category': category, 'year': year}

CATALOG = [entity(1, 'Spirited Away', year=2001), entity(2, 'Moonlight', year=2016),
           entity(3, 'Moonlight', year=2002), entity(4, 'Interstellar', year=2014),
           entity(5, 'Amélie', year=2001), entity(6, 'Daft Punk', 'artist'),
           entity(7, 'Björk', 'artist'), entity(8, 'Tycho', 'artist'),
           entity(9, 'Arrival', year=2016), entity(10, 'The Grand Budapest Hotel', year=2014)]
FAMILIES = {
    0: ([entity(21, 'My Neighbor Totoro', year=1988), entity(22, 'The Secret World of Arrietty', year=2010), entity(23, 'Song of the Sea', year=2014)], ['Wonder', 'Discovery', 'Everyday magic']),
    1: ([entity(24, 'Aftersun', year=2022), entity(25, 'Past Lives', year=2023), entity(26, 'Paterson', year=2016)], ['Memory', 'Connection', 'Quiet rituals']),
    2: ([entity(27, '2001: A Space Odyssey', year=1968), entity(28, 'Contact', year=1997), entity(29, 'Arrival', year=2016)], ['Time', 'Exploration', 'Communication']),
    3: ([entity(30, 'Fantastic Mr. Fox', year=2009), entity(31, 'Moonrise Kingdom', year=2012), entity(32, 'Amélie', year=2001)], ['Symmetry', 'Playfulness', 'Small adventures']),
}

def search(query, category):
    q = query.casefold()
    return [x.copy() for x in CATALOG if x['category'] == category and (q in x['name'].casefold() or (q == 'bjork' and x['name'] == 'Björk'))][:5]

def insights(ids):
    # All selected IDs influence deterministic fixtures. Never passed into live adapter.
    seed = sum(int(UUID(x)) for x in ids)
    group = {1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 3, 7: 0, 8: 1, 9: 2, 10: 3}.get(seed, seed % 4)
    movies, labels = FAMILIES[group]
    movies = [{**m, 'rank': i+1, 'affinity': None, 'explainability': None} for i, m in enumerate(movies)]
    tags = [{'id': 'fixture:theme:' + x.lower().replace(' ', '_'), 'name': x, 'rank': i+1, 'affinity': None} for i, x in enumerate(labels)]
    return {'entities': movies, 'tags': tags, 'warnings': ['Synthetic DEMO associations. No Qloo API calls were made. No synthetic affinity scores are displayed.'], 'source': 'demo_fixture'}
