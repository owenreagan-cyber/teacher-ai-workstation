#!/usr/bin/env python3
"""Install the developer safety hook outside the repository.

1. hash each versioned source file listed in FILES
2. copy it to ~/.claude/hooks/cos/<name>
3. make the installed copy read-only (0444)
4. write every installed SHA-256 to ~/.claude/hooks/cos/dev_guard.sha256

FILES: dev_guard.py (the hook), sandbox-lock.json (passed to `claude --settings`).

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

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "dev_guard.py")
FILES = ("dev_guard.py", "sandbox-lock.json")
DEFAULT_DEST_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "cos")
READ_ONLY = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _install_one(source: str, dest: str) -> str:
    with open(source, "rb") as f:
        data = f.read()
    source_sha = sha256_bytes(data)
    # Write to a temp file in the same directory, then atomically replace the
    # (possibly read-only) previous copy.
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dest), prefix=".dev_guard.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, READ_ONLY)
        os.replace(tmp, dest)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    with open(dest, "rb") as f:
        installed_sha = sha256_bytes(f.read())
    if installed_sha != source_sha:
        raise SystemExit(f"installed copy hash {installed_sha} != source {source_sha} ({dest})")
    mode = stat.S_IMODE(os.stat(dest).st_mode)
    if mode != 0o444:
        raise SystemExit(f"installed copy mode {oct(mode)} != 0o444 ({dest})")
    return installed_sha


def install(source_dir: str = HERE, dest_dir: str = DEFAULT_DEST_DIR, files=FILES) -> dict:
    os.makedirs(dest_dir, mode=0o755, exist_ok=True)
    shas = {name: _install_one(os.path.join(source_dir, name), os.path.join(dest_dir, name))
            for name in files}
    sha_path = os.path.join(dest_dir, "dev_guard.sha256")
    if os.path.exists(sha_path):
        os.chmod(sha_path, stat.S_IRUSR | stat.S_IWUSR)
    with open(sha_path, "w") as f:
        for name in files:
            f.write(f"{shas[name]}  {name}\n")
    os.chmod(sha_path, READ_ONLY)
    hook = os.path.join(dest_dir, "dev_guard.py")
    return {"source": os.path.join(source_dir, "dev_guard.py"), "source_sha256": shas["dev_guard.py"],
            "installed": hook, "installed_sha256": shas["dev_guard.py"],
            "mode": oct(stat.S_IMODE(os.stat(hook).st_mode)), "sha256_file": sha_path,
            "files": shas}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest-dir", default=DEFAULT_DEST_DIR)
    args = ap.parse_args(argv)
    for k, v in install(dest_dir=args.dest_dir).items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
