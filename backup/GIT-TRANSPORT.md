# Recover through Git transport

The public website and editable project are on `main`; GitHub Pages serves `gh-pages`.
The independent `backup-upload-20261022` branch holds the complete original snapshot and 4K film as 48 MiB chunks.
It does not modify the original project history.

The normal recovery route is the v1.0.0 Release and `RESTORE.md`.
If Release attachments are unavailable, reconstruct the identical assets directly from Git:

```bash
git clone --single-branch --branch backup-upload-20261022 https://github.com/liuyinchu/ai-video-stress-relief-techniques.git backup-transport
cd backup-transport
python3 assemble-release.py
cd release
shasum -a 256 -c SHA256SUMS
python3 ../verify-backup.py complete-project-20261022.tar.zst MANIFEST.json
```

The verifier needs Python 3 and `zstd`. It checks every archived regular file, directory, symbolic link, permission, and hard-link target without extracting or executing archived code.

`transport.json` identifies every chunk and whole-file digest. A final `READY` commit triggers `.github/workflows/release-from-chunks.yml`, which reconstructs the assets, verifies all 6,607 archive entries, uploads the release files, publishes the existing draft, and compares GitHub's stored asset digests. Re-running this workflow is supported on the transport branch.
