"""Check tracked files for accidental private data and common credential formats."""
import json
import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = {'.run', '.venv', 'node_modules', 'profiles', '.claude', '.agents', '__pycache__'}
PATTERNS = [re.compile(r'\b(?:ghp_|github_pat_|sk-ant-api\d+-)[A-Za-z0-9_-]{20,}'),
            re.compile(r'\bAKIA[A-Z0-9]{16}\b'),
            re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]


def main():
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    errors, checked = [], 0
    for name in filter(None, files):
        path = ROOT / name
        relative = Path(name)
        if set(relative.parts) & BLOCKED_PARTS or (relative.name.startswith('.env') and relative.name != '.env.example'):
            errors.append(f'Private or generated path is tracked: {name}')
        if relative.name.lower() == 'nul' or relative.suffix in {'.backup', '.sqlite3', '.db', '.log'}:
            errors.append(f'Local artifact is tracked: {name}')
        if path.stat().st_size > 50 * 1024 ** 2:
            errors.append(f'File exceeds the 50 MiB repository budget: {name}')
        if path.suffix.lower() in {'.pkl', '.png', '.npy'}:
            continue
        content = path.read_text(encoding='utf-8', errors='replace')
        for number, line in enumerate(content.splitlines(), 1):
            if any(pattern.search(line) for pattern in PATTERNS):
                errors.append(f'Potential credential: {name}:{number}')
        checked += 1
    if not checked:
        errors.append('No tracked text files were available to inspect')
    metadata = json.loads((ROOT / 'preprocessing_info.json').read_text())
    if {'skill_gaps', 'confidence_score'} & set(metadata['original_features']):
        errors.append('Bundled model includes target-derived features')
    evaluation = json.loads((ROOT / 'docs/model_evaluation.json').read_text())
    for name, expected in {**evaluation['artifacts_sha256'], evaluation['dataset']: evaluation['dataset_sha256']}.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            errors.append(f'Release artifact checksum mismatch: {name}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Checked {checked} tracked text files, artifact sizes, and bundled model feature metadata.')


if __name__ == '__main__':
    main()
