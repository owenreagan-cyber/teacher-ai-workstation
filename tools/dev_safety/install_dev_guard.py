#!/usr/bin/env python3
"""Install the developer safety hook outside the repository.

1. hash the versioned source tools/dev_safety/dev_guard.py
2. copy it to ~/.claude/hooks/cos/dev_guard.py
3. make the installed copy read-only (0444)
4. write the installed SHA-256 to ~/.claude/hooks/cos/dev_guard.sha256

Run by Owen, outside a Claude Code session running under the profile (the
profile's hook denies agent access to the install directory). Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
import tempfile

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev_guard.py")
DEFAULT_DEST_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "cos")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def install(source: str = SOURCE, dest_dir: str = DEFAULT_DEST_DIR) -> dict:
    with open(source, "rb") as f:
        data = f.read()
    source_sha = sha256_bytes(data)
    os.makedirs(dest_dir, mode=0o755, exist_ok=True)
    dest = os.path.join(dest_dir, "dev_guard.py")
    sha_path = os.path.join(dest_dir, "dev_guard.sha256")

    # Write to a temp file in the same directory, then atomically replace the
    # (possibly read-only) previous copy.
    fd, tmp = tempfile.mkstemp(dir=dest_dir, prefix=".dev_guard.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        os.replace(tmp, dest)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    with open(dest, "rb") as f:
        installed_sha = sha256_bytes(f.read())
    if installed_sha != source_sha:
        raise SystemExit(f"installed copy hash {installed_sha} != source {source_sha}")
    mode = stat.S_IMODE(os.stat(dest).st_mode)
    if mode != 0o444:
        raise SystemExit(f"installed copy mode {oct(mode)} != 0o444")

    if os.path.exists(sha_path):
        os.chmod(sha_path, stat.S_IRUSR | stat.S_IWUSR)
    with open(sha_path, "w") as f:
        f.write(f"{installed_sha}  dev_guard.py\n")
    os.chmod(sha_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return {"source": source, "source_sha256": source_sha, "installed": dest,
            "installed_sha256": installed_sha, "mode": oct(mode), "sha256_file": sha_path}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest-dir", default=DEFAULT_DEST_DIR)
    args = ap.parse_args(argv)
    for k, v in install(dest_dir=args.dest_dir).items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
