#!/usr/bin/env python3
"""Reassemble release assets only after each Git transport chunk passes SHA-256."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
index = json.loads((root / 'transport.json').read_text())
out = root / 'release'
out.mkdir(exist_ok=True)
for asset in index['assets']:
    name = asset['name']
    if Path(name).name != name:
        raise ValueError('Invalid asset name')
    checksum = hashlib.sha256()
    count = 0
    with (out / name).open('wb') as target:
        for part in asset['parts']:
            path = root / part['path']
            if path.resolve().parent != (root / 'parts').resolve():
                raise ValueError('Invalid part path')
            data = path.read_bytes()
            if len(data) != part['size'] or hashlib.sha256(data).hexdigest() != part['sha256']:
                raise ValueError('Damaged chunk: ' + part['path'])
            target.write(data)
            checksum.update(data)
            count += len(data)
    if count != asset['size'] or checksum.hexdigest() != asset['sha256']:
        raise ValueError('Damaged assembled asset: ' + name)
    print(name, count, checksum.hexdigest(), flush=True)

