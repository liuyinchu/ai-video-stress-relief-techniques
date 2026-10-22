#!/usr/bin/env python3
"""Verify every archived file and symlink without extracting or executing it."""
import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

parser = argparse.ArgumentParser()
parser.add_argument('archive', type=Path)
parser.add_argument('manifest', type=Path)
parser.add_argument('--receipt', type=Path)
args = parser.parse_args()
manifest = json.loads(args.manifest.read_text())
expected = {e['path']: e for e in manifest['entries']}
seen = set()
files = {}
total = 0

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

proc = subprocess.Popen(['zstd', '-d', '-q', '-c', str(args.archive)], stdout=subprocess.PIPE)
try:
    with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
        for member in archive:
            parts = PurePosixPath(member.name).parts
            if parts == (manifest['root'],):
                continue
            if not parts or parts[0] != manifest['root'] or '..' in parts:
                raise RuntimeError('Unexpected archive path: ' + member.name)
            path = PurePosixPath(*parts[1:]).as_posix()
            if path in seen or path not in expected:
                raise RuntimeError('Duplicate or unlisted entry: ' + path)
            want = expected[path]
            if member.mode != want['mode']:
                raise RuntimeError('Permissions changed: ' + path)
            if member.isdir():
                assert want['type'] == 'directory', path
            elif member.issym():
                assert want['type'] == 'symlink' and member.linkname == want['target'], path
            elif member.isfile() or member.islnk():
                assert want['type'] == 'file', path
                if member.islnk():
                    value = files.get(member.linkname)
                    if value is None:
                        raise RuntimeError('Unverified hardlink target: ' + path)
                    size, checksum = value
                else:
                    stream = archive.extractfile(member)
                    h = hashlib.sha256()
                    size = 0
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(block)
                        size += len(block)
                    checksum = h.hexdigest()
                assert size == want['size'] and checksum == want['sha256'], path
                files[member.name] = (size, checksum)
                total += size
            else:
                raise RuntimeError('Unsupported archive entry: ' + path)
            seen.add(path)
    proc.stdout.close()
    if proc.wait() != 0:
        raise RuntimeError('Compressed archive is damaged.')
except BaseException:
    proc.terminate()
    proc.wait()
    raise
if seen != set(expected):
    raise RuntimeError('Missing archived paths: ' + ', '.join(sorted(set(expected) - seen)))
receipt = {'verified': True, 'entries': len(seen), 'regular_file_bytes': total,
           'archive_sha256': digest(args.archive), 'manifest_sha256': digest(args.manifest),
           'original_commit': manifest['original_commit']}
if args.receipt:
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
