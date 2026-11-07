"""Check public release files without requiring copyrighted game data."""
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
release = json.loads((root / 'release.json').read_text(encoding='utf-8'))
translations = json.loads((root / 'translations/tr.json').read_text(encoding='utf-8'))
patch_bytes = (root / 'patch/flotsam-tr-v1.0.0.json.gz').read_bytes()
delta = json.loads(gzip.decompress(patch_bytes))
assert len(translations) == release['translation_entries'] == 3197
assert all(isinstance(row['turkce'], str) and row['turkce'].strip() for row in translations)
assert hashlib.sha256(patch_bytes).hexdigest() == release['patch_sha256']
assert len(patch_bytes) == release['patch_size']
for key in ('source_sha256', 'target_sha256', 'source_size', 'target_size'):
    assert delta[key] == release[key], key
helper = (root / 'Yama.ps1').read_text(encoding='utf-8')
for key in ('source_sha256', 'target_sha256', 'patch_sha256'):
    assert release[key].upper() in helper, key
assert delta['format'] == 'flotsam-delta-v1'
assert len(delta['operations']) <= 100_000
assert not list(root.rglob('*.assets')), 'Full game assets must not be committed'
assert not list(root.rglob('*.original')), 'Original game backups must not be committed'
print('3197 translations, delta integrity, installer hashes and package contents verified.')
