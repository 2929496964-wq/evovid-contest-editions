#!/usr/bin/env python3
"""Verify the reviewed source inventory without contacting any service.

This bounded static check is not a guarantee of secret absence or a security audit.
Run from any directory: python tools/verify_public_source.py
"""
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'PUBLIC-MANIFEST.json'
EXCLUDED_DIRS = {'.venv', 'node_modules', '.qa-node', '.wheel-cache', '__pycache__',
                 '.pytest_cache', 'qa_internal', '.taste-data', '.evidence-data',
                 '.ui-data', 'test-output', 'data'}
EXCLUDED_SUFFIXES = {'.log', '.pid', '.pyc', '.db', '.sqlite', '.sqlite3', '.pem', '.key',
                     '.ttf', '.otf', '.ttc', '.woff', '.woff2', '.whl', '.exe', '.so', '.dll'}
OLD_SOURCE_INVENTORIES = {'PACKAGE-FILES.txt', 'SOURCE-SHA256.json', 'BUILD_MANIFEST.json',
                        'release-manifest.json'}
SECRET_PATTERNS = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'aws_access_key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'google_api_key': re.compile(r'\bAIza[A-Za-z0-9_-]{30,}\b'),
    'slack_token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
    'jwt': re.compile(r'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b'),
    'signed_download': re.compile(r'(?:[?&](?:X-Amz-Signature|sig)=)[A-Za-z0-9%+/]{20,}', re.I),
    'private_workspace': re.compile(r'/(?:workspace/(?:shared|scratch)|home/agent|root/\.codex)/'),
}


def files():
    return sorted(p for p in ROOT.rglob('*') if '.git' not in p.relative_to(ROOT).parts and p.is_file())


def scan_text(name, raw, failures):
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        return
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            failures.append(f'{label}: {name}')
    if name.endswith('.env.example'):
        for line in text.splitlines():
            if line.lstrip().startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            if re.search(r'(?:API_KEY|SECRET|CLIENT_ID|MERCHANT_ID|PASSWORD)$', key.strip()) and value.strip():
                failures.append(f'nonempty credential template: {name}')


def verify():
    failures = []
    manifest = json.loads(MANIFEST.read_text())
    expected = {f['path']: f for f in manifest['files']}
    actual = {p.relative_to(ROOT).as_posix(): p for p in files() if p != MANIFEST}
    for rel in sorted(expected.keys() - actual.keys()):
        failures.append('missing: ' + rel)
    for rel in sorted(actual.keys() - expected.keys()):
        failures.append('unreviewed extra: ' + rel)
    link_count = 0
    archive_entries = 0
    for rel, p in actual.items():
        parts = p.relative_to(ROOT).parts
        if p.is_symlink():
            failures.append('symlink: ' + rel)
        if any(x in EXCLUDED_DIRS or x.startswith('runtime') for x in parts[:-1]):
            failures.append('excluded directory: ' + rel)
        if p.suffix.lower() in EXCLUDED_SUFFIXES or p.name in OLD_SOURCE_INVENTORIES:
            failures.append('excluded artifact: ' + rel)
        if p.name == '.env' or (p.name.startswith('.env.') and p.name != '.env.example'):
            failures.append('credential file: ' + rel)
        raw = p.read_bytes()
        if rel in expected and (hashlib.sha256(raw).hexdigest() != expected[rel]['sha256'] or len(raw) != expected[rel]['bytes']):
            failures.append('digest/size mismatch: ' + rel)
        scan_text(rel, raw, failures)
        if p.suffix == '.md':
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', raw.decode('utf-8')):
                url = target.split(' ', 1)[0].strip('<>')
                if not url or url.startswith('#') or urlsplit(url).scheme:
                    continue
                path = unquote(urlsplit(url).path)
                link_count += 1
                resolved = (p.parent / path).resolve()
                if not resolved.is_relative_to(ROOT) or not resolved.exists():
                    failures.append(f'broken local link: {rel} -> {url}')
        if p.suffix == '.zip':
            with zipfile.ZipFile(p) as archive:
                inner = json.loads(archive.read('manifest.json'))
                expected_names = set(inner['files']) | {'manifest.json'}
                if set(archive.namelist()) != expected_names:
                    failures.append('archive inventory mismatch: ' + rel)
                for item in archive.infolist():
                    archive_entries += 1
                    if item.is_dir():
                        continue
                    name = item.filename
                    if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                        failures.append('unsafe archive path: ' + rel)
                    contents = archive.read(name)
                    scan_text(rel + ':' + name, contents, failures)
                    if name in inner['files'] and hashlib.sha256(contents).hexdigest() != inner['files'][name]:
                        failures.append('archive digest mismatch: ' + rel + ':' + name)
    report = {'files_verified': len(actual), 'relative_markdown_links_checked': link_count,
              'archive_entries_checked': archive_entries, 'failures': failures,
              'scope': 'Static manifest, excluded-artifact, selected-secret-pattern, archive and relative-link checks only.'}
    print(json.dumps(report, indent=2))
    return bool(failures)


if __name__ == '__main__':
    sys.exit(verify())
