"""Bounded bilingual commands. No model, network request, or simulated intelligence."""
import copy
import re
import uuid

TONES = {'warm': 'warm', '温暖': 'warm', '温暖语气': 'warm', 'bold': 'bold', '活力': 'bold', 'calm': 'calm', '平静': 'calm'}
PALETTES = {'warm': ['#e78455', '#b16649', '#cca468'], 'bold': ['#dd593f', '#417177', '#d7a23d'], 'calm': ['#668b88', '#7493a7', '#9b8ba6']}
MAX_TEXT = 2000


def short(value, maximum=140):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValueError(f'Text must contain 1–{maximum} characters. / 文本长度须为1–{maximum}字。')
    if any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise ValueError('Control characters are not accepted. / 不支持控制字符。')
    return value.strip()


def seconds(value):
    if isinstance(value, bool):
        raise ValueError('Duration must be 6–45 seconds. / 时长须为6–45秒。')
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError('Duration must be 6–45 seconds. / 时长须为6–45秒。')
    if str(value) != str(n) or not 6 <= n <= 45:
        raise ValueError('Duration must be 6–45 seconds. / 时长须为6–45秒。')
    return n


def new_project():
    return {'id': uuid.uuid4().hex, 'title': 'Untitled story', 'theme': '', 'audience': '', 'duration': 12, 'tone': 'warm', 'format': 'landscape', 'scenes': [], 'revision': 0, 'status': 'brief', 'wizard': {}, 'history': [], 'messages': [{'role': 'assistant', 'text': 'Let’s make a small story worth sharing. Start with “Create a project” or choose a sample below. / 输入「创建项目」，我会逐项收集主题、受众、时长和语气。'}]}


def save_undo(p):
    snapshot = {k: copy.deepcopy(v) for k, v in p.items() if k not in ('history', 'messages', 'revision')}
    p['history'] = (p.get('history', []) + [snapshot])[-20:]


def build(p, theme, audience, duration, tone):
    theme, audience, duration = short(theme, 100), short(audience, 100), seconds(duration)
    if tone not in PALETTES:
        raise ValueError('Tone must be warm, bold or calm. / 语气：温暖、活力、平静。')
    save_undo(p)
    zh = bool(re.search(r'[\u3400-\u9fff]', theme + audience))
    labels = ['一个小小的开始', '把好奇变成行动', '一起，让故事继续'] if zh else ['A small beginning', 'Make room for possibility', 'Let the story continue']
    captions = [f'{theme}，从一个想法出发。', f'为{audience}，留住值得分享的瞬间。', '现在，就是开始的好时刻。'] if zh else [f'{theme} starts with one idea.', f'A moment worth sharing with {audience}.', 'There is no better time to begin.']
    each, remainder = divmod(duration, 3)
    p.update(title=theme, theme=theme, audience=audience, duration=duration, tone=tone, status='storyboard', wizard={}, scenes=[{'id': uuid.uuid4().hex, 'title': title, 'caption': captions[i], 'seconds': each + (1 if i < remainder else 0), 'color': PALETTES[tone][i], 'motion': ['drift', 'rise', 'pulse'][i], 'asset': None} for i, title in enumerate(labels)])
    p['revision'] += 1


def edit(p, patch):
    if not p['scenes']:
        raise ValueError('Create a storyboard first. / 请先创建分镜。')
    # Validate a complete copy before mutating anything.
    draft = copy.deepcopy(p)
    if 'format' in patch:
        if patch['format'] not in ('landscape', 'portrait'):
            raise ValueError('Unknown video format.')
        draft['format'] = patch['format']
    if 'tone' in patch:
        if patch['tone'] not in PALETTES:
            raise ValueError('Unknown tone.')
        draft['tone'] = patch['tone']
        for i, scene in enumerate(draft['scenes']):
            scene['color'] = PALETTES[patch['tone']][i % 3]
    if 'scene' in patch:
        index = patch['scene']
        if type(index) is not int or not 0 <= index < len(draft['scenes']):
            raise ValueError('Unknown scene. / 分镜不存在。')
        scene = draft['scenes'][index]
        for key in ('title', 'caption'):
            if key in patch:
                scene[key] = short(patch[key], 100 if key == 'title' else 220)
        if 'seconds' in patch:
            if type(patch['seconds']) is not int or not 1 <= patch['seconds'] <= 20:
                raise ValueError('A scene must be 1–20 seconds. / 单段时长须为1–20秒。')
            scene['seconds'] = patch['seconds']
        if 'motion' in patch:
            if patch['motion'] not in ('drift', 'rise', 'pulse'):
                raise ValueError('Unknown motion.')
            scene['motion'] = patch['motion']
        if 'color' in patch:
            if not isinstance(patch['color'], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', patch['color']):
                raise ValueError('Invalid color.')
            scene['color'] = patch['color']
        if 'asset' in patch:
            if patch['asset'] is not None and not re.fullmatch(r'[a-f0-9]{32}', str(patch['asset'])):
                raise ValueError('Invalid asset ID.')
            scene['asset'] = patch['asset']
    if 'move' in patch:
        pair = patch['move']
        if not isinstance(pair, list) or len(pair) != 2 or any(type(i) is not int or i not in range(len(draft['scenes'])) for i in pair):
            raise ValueError('Invalid scene order.')
        draft['scenes'].insert(pair[1], draft['scenes'].pop(pair[0]))
    draft['duration'] = sum(s['seconds'] for s in draft['scenes'])
    if not 3 <= draft['duration'] <= 45:
        raise ValueError('Total video length must be 3–45 seconds.')
    save_undo(p)
    for key in ('format', 'tone', 'scenes', 'duration'):
        p[key] = draft[key]
    p['revision'] += 1


def undo(p):
    if not p.get('history'):
        raise ValueError('Nothing to undo yet. / 暂无可撤回的修改。')
    previous = p['history'].pop()
    p.update(previous)
    p['revision'] += 1


def command(p, raw):
    text = short(raw, MAX_TEXT)
    low = text.lower().strip()
    answer, action = '', None
    if low in ('help', '帮助', '?'):
        answer = 'Supported commands: Create a project · Shorten scene 2 · Set scene 2 to 3 seconds · Tone warm/bold/calm · Text 2: your caption · Title 2: your title · Move 3 to 1 · Undo · Export. 中文：创建项目；把第2段改短；第2段设为3秒；换成温暖语气；文本2：你的字幕；标题2：你的标题；移动3到1；撤回上次修改；导出。'
    elif low in ('cancel', '取消') and p.get('wizard'):
        p['wizard'] = {}
        answer = 'Brief cancelled; the saved storyboard is unchanged. / 已取消，本来的分镜未改变。'
    elif low in ('create a project', 'create', 'new', '创建项目', '新建项目'):
        p['wizard'] = {'step': 'theme'}
        answer = 'What is your story about? / 你想创作什么主题？'
    elif p.get('wizard'):
        w = p['wizard']
        step = w['step']
        if step == 'theme':
            w['theme'], w['step'] = short(text, 100), 'audience'
            answer = 'Who is it for? / 你想分享给谁？'
        elif step == 'audience':
            w['audience'], w['step'] = short(text, 100), 'duration'
            answer = 'How many seconds? Enter 6–45. / 时长几秒？请输入6–45。'
        elif step == 'duration':
            w['duration'], w['step'] = seconds(re.sub(r'\s*(seconds?|秒)$', '', low)), 'tone'
            answer = 'Choose warm, bold or calm. / 选择：温暖、活力、平静。'
        else:
            if low not in TONES:
                raise ValueError('Please choose warm, bold or calm. / 请选择温暖、活力或平静。')
            build(p, w['theme'], w['audience'], w['duration'], TONES[low])
            answer = 'Your three-scene draft is ready. The template uses your brief; edit any line to make it yours. / 三段分镜已就绪。这是根据主题套用的规则模板，可以修改每一行。'
    elif low in ('undo', '撤回', '撤回上次修改'):
        undo(p)
        answer = 'Last storyboard change undone. / 已撤回上次分镜修改。'
    elif low in ('export', 'render', '导出', '渲染'):
        if not p['scenes']:
            raise ValueError('Create a storyboard first. / 请先创建分镜。')
        action = 'confirm'
        answer = 'Review the output settings before starting the local render. / 请确认输出设置，再启动本地渲染。'
    else:
        tone = re.fullmatch(r'(?:tone |set tone to |换成|语气[:：]?)(warm|bold|calm|温暖|活力|平静)(?:语气)?', low)
        shorten = re.fullmatch(r'(?:shorten scene (\d+)|把第(\d+)段改短)', low)
        length = re.fullmatch(r'(?:set scene (\d+) to (\d+) seconds?|第(\d+)段设为(\d+)秒)', low)
        content = re.fullmatch(r'(text|title|文本|标题)\s*(\d+)\s*[:：]\s*(.+)', text, re.I | re.S)
        move = re.fullmatch(r'(?:move (\d+) to (\d+)|移动(\d+)到(\d+))', low)
        if tone:
            edit(p, {'tone': TONES[tone[1]]})
        elif shorten:
            index = int(shorten[1] or shorten[2]) - 1
            if index not in range(len(p['scenes'])):
                raise ValueError('Unknown scene. / 分镜不存在。')
            edit(p, {'scene': index, 'seconds': max(1, p['scenes'][index]['seconds'] - 1)})
        elif length:
            edit(p, {'scene': int(length[1] or length[3]) - 1, 'seconds': int(length[2] or length[4])})
        elif content:
            edit(p, {'scene': int(content[2]) - 1, 'caption' if content[1].lower() in ('text', '文本') else 'title': content[3]})
        elif move:
            edit(p, {'move': [int(move[1] or move[3]) - 1, int(move[2] or move[4]) - 1]})
        else:
            raise ValueError('I didn’t match a supported command. Try “Shorten scene 2”, “Tone warm”, or “Help”. / 未匹配支持的语法，请试「把第2段改短」「换成温暖语气」或「帮助」。')
        answer = 'Storyboard updated and saved locally. / 分镜已更新并自动保存在本机。'
    p['messages'] = (p.get('messages', []) + [{'role': 'user', 'text': text}, {'role': 'assistant', 'text': answer}])[-60:]
    return answer, action
