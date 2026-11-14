// Stage an immutable, self-contained cos/cosd runtime into the app bundle.
//
// The packaged runtime contains the Python sources plus two launchers. The
// launchers resolve Python explicitly (CHIEF_PYTHON -> ~/.chief-runtime/python
// -> python3.12 -> Homebrew) and import from their own directory, never from
// the development checkout.
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(here, "..");
const repoRoot = path.resolve(appDir, "..", "..");
// CHIEF_STAGE_OUT lets tests stage into a temporary directory.
const outDir = process.env.CHIEF_STAGE_OUT
  ? path.resolve(process.env.CHIEF_STAGE_OUT)
  : path.join(appDir, "build", "runtime");

const LAUNCHER = (module) => `#!/usr/bin/env bash
# Chief packaged runtime launcher. Sources live beside this script.
set -euo pipefail
here="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd -P)"
py="\${CHIEF_PYTHON:-}"
if [[ -z "\${py}" && -f "\${HOME}/.chief-runtime/python" ]]; then
  py="$(cat "\${HOME}/.chief-runtime/python")"
fi
if [[ -z "\${py}" ]]; then
  py="$(command -v python3.12 || true)"
fi
if [[ -z "\${py}" && -x /opt/homebrew/bin/python3.12 ]]; then
  py=/opt/homebrew/bin/python3.12
fi
if [[ -z "\${py}" ]]; then
  echo "chief: Python 3.12 is required but was not found" >&2
  exit 127
fi
if [[ "$("\${py}" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)" != "3.12" ]]; then
  echo "chief: packaged runtime requires Python 3.12: \${py}" >&2
  exit 127
fi
# -B: never write bytecode into the signed bundle (it would break the code seal).
exec "\${py}" -B -s -E -P -c 'import sys; sys.path.insert(0, sys.argv.pop(1)); from ${module} import main; raise SystemExit(main(sys.argv[1:]))' "\${here}/py" "$@"
`;

function copyTree(from, to) {
  fs.cpSync(from, to, {
    recursive: true,
    filter: (src) => !src.includes("__pycache__") && !src.endsWith(".pyc"),
  });
}

function treeHash(root) {
  const files = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else files.push(full);
    }
  };
  walk(root);
  const hash = createHash("sha256");
  for (const file of files) {
    hash.update(path.relative(root, file).split(path.sep).join("/"));
    hash.update("\0");
    hash.update(fs.readFileSync(file));
    hash.update("\0");
  }
  return { digest: hash.digest("hex"), files: files.length };
}

function git(args) {
  try {
    return execFileSync("git", ["-C", repoRoot, ...args], { encoding: "utf8" }).trim();
  } catch {
    return null;
  }
}

fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

fs.mkdirSync(path.join(outDir, "py"), { recursive: true });
copyTree(path.join(repoRoot, "cos"), path.join(outDir, "py", "cos"));
copyTree(path.join(repoRoot, "cosd"), path.join(outDir, "py", "cosd"));

fs.writeFileSync(path.join(outDir, "cos"), LAUNCHER("cos.cli"), { mode: 0o755 });
fs.writeFileSync(path.join(outDir, "cosd"), LAUNCHER("cosd.cli"), { mode: 0o755 });

const pkg = JSON.parse(fs.readFileSync(path.join(appDir, "package.json"), "utf8"));
const cosHash = treeHash(path.join(outDir, "py", "cos"));
const cosdHash = treeHash(path.join(outDir, "py", "cosd"));

const manifest = {
  format: 1,
  app: { name: pkg.name, version: pkg.version },
  runtime: { version: `${pkg.version}+${(git(["rev-parse", "--short=12", "HEAD"]) ?? "unknown")}` },
  source: {
    commit: git(["rev-parse", "HEAD"]),
    branch: git(["rev-parse", "--abbrev-ref", "HEAD"]),
    dirty: (git(["status", "--porcelain", "--untracked-files=no"]) ?? "") !== "",
  },
  python: { requirement: "3.12", resolution: ["CHIEF_PYTHON", "~/.chief-runtime/python", "python3.12", "/opt/homebrew/bin/python3.12"] },
  dependencies: { file: "requirements-cosd-pairing.txt", cryptography: ">=42,<51" },
  architecture: process.arch,
  artifacts: {
    cos: { files: cosHash.files, sha256: cosHash.digest },
    cosd: { files: cosdHash.files, sha256: cosdHash.digest },
  },
  built_at: new Date().toISOString(),
};

fs.writeFileSync(path.join(outDir, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");

// The launchers and sources must not reference the development checkout.
for (const name of ["cos", "cosd", "manifest.json"]) {
  const text = fs.readFileSync(path.join(outDir, name), "utf8");
  if (text.includes(repoRoot)) {
    throw new Error(`staged ${name} references the development checkout`);
  }
}

console.log(`staged runtime ${manifest.runtime.version}: cos ${cosHash.files} files, cosd ${cosdHash.files} files`);
