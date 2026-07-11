from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ok = 0
    fail = 0
    for raw in (argv or sys.argv[1:]):
        payload = json.loads(Path(raw).read_text(encoding="utf-8"))
        manifest = payload["deploymentManifestV1"]
        if manifest["manifestVersion"] == 1 and manifest["mode"] == "preview-only" and manifest["validationSummary"]["failCount"] == 0:
            ok += 1
            print("PASS: manifest.preview Phase 27 manifest preview is valid")
        else:
            fail += 1
            print("FAIL: manifest.preview Phase 27 manifest preview is invalid")
    print(f"PASS: {ok}")
    print("WARN: 1")
    print(f"FAIL: {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())

