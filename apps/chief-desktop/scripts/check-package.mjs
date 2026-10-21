// Packaging check: every module the app needs at startup is in the packaged output.
//
//   node scripts/check-package.mjs          after `npm run build` (part of it): the startup
//                                           require graph and the renderer's assets exist and
//                                           match electron-builder.yml's `files:` globs
//   node scripts/check-package.mjs --asar   after `npm run package`: the same files are inside
//                                           release/mac-arm64/Chief.app/.../app.asar
//
// Startup entry points: package.json "main" (the main process), the preload script the main
// process loads, and the renderer's index.html. Relative require() calls are followed; a bare
// specifier other than electron or a node: builtin is reported, because the app ships no
// node_modules. Exits 1 and lists every missing file.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PRELOAD = "out/preload/preload.js";
const RENDERER_INDEX = "dist/renderer/index.html";
const ASAR = "release/mac-arm64/Chief.app/Contents/Resources/app.asar";
const RUNTIME_MODULES = new Set(["electron"]);

/** The `files:` globs from electron-builder.yml (a plain list under a top-level key). */
export function packedGlobs(yml) {
  const lines = yml.split("\n");
  const start = lines.findIndex((l) => /^files:\s*$/.test(l));
  if (start < 0) return [];
  const out = [];
  for (const line of lines.slice(start + 1)) {
    const m = line.match(/^\s+-\s+(.+?)\s*$/);
    if (!m) break;
    out.push(m[1].replace(/^["']|["']$/g, ""));
  }
  return out;
}

/** True when a repo-relative path matches one of the globs ("dir/**" or an exact path). */
export function isPacked(rel, globs) {
  return globs.some((g) => (g.endsWith("/**") ? rel.startsWith(g.slice(0, -2)) : rel === g));
}

function requires(code) {
  return [...code.matchAll(/\brequire\(\s*["']([^"']+)["']\s*\)/g)].map((m) => m[1]);
}

/** Every file the app loads at startup (repo-relative), plus problems found on the way. */
export function startupFiles(root) {
  const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf-8"));
  const files = new Set(["package.json"]);
  const problems = [];
  const queue = [pkg.main, PRELOAD].filter(Boolean).map((p) => path.normalize(p));
  while (queue.length) {
    const rel = queue.shift();
    if (files.has(rel)) continue;
    files.add(rel);
    let code;
    try {
      code = fs.readFileSync(path.join(root, rel), "utf-8");
    } catch {
      problems.push(`missing ${rel}`);
      continue;
    }
    for (const spec of requires(code)) {
      if (spec.startsWith(".")) {
        const target = path.normalize(path.join(path.dirname(rel), spec));
        queue.push(path.extname(target) ? target : `${target}.js`);
      } else if (!spec.startsWith("node:") && !RUNTIME_MODULES.has(spec)) {
        problems.push(`${rel} requires ${spec}, which is not packaged (the app ships no node_modules)`);
      }
    }
  }
  files.add(RENDERER_INDEX);
  let html = "";
  try {
    html = fs.readFileSync(path.join(root, RENDERER_INDEX), "utf-8");
  } catch {
    problems.push(`missing ${RENDERER_INDEX}`);
  }
  for (const m of html.matchAll(/\b(?:src|href)="(\.\/[^"]+|[^":/][^":]*)"/g)) {
    const asset = path.normalize(path.join(path.dirname(RENDERER_INDEX), m[1]));
    files.add(asset);
    if (!fs.existsSync(path.join(root, asset))) {
      problems.push(`missing ${asset} (referenced by ${RENDERER_INDEX})`);
    } else if (asset.endsWith(".css")) {
      cssAssets(root, asset, files, problems);
    }
  }
  return { files: [...files].sort(), problems };
}

/** Files a built stylesheet loads (the bundled fonts): each must exist, and none may be remote. */
function cssAssets(root, css, files, problems) {
  const text = fs.readFileSync(path.join(root, css), "utf-8");
  for (const m of text.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)) {
    const ref = m[1].trim();
    if (ref.startsWith("data:")) continue;
    if (/^([a-z]+:)?\/\//i.test(ref)) {
      problems.push(`${css} loads ${ref}, which is not bundled (the renderer makes no network requests)`);
      continue;
    }
    const asset = path.normalize(path.join(path.dirname(css), ref.split(/[?#]/)[0]));
    files.add(asset);
    if (!fs.existsSync(path.join(root, asset))) problems.push(`missing ${asset} (referenced by ${css})`);
  }
}

/** Paths of the files inside an asar archive (header only; contents are never read). */
export function asarFiles(file) {
  const fd = fs.openSync(file, "r");
  try {
    const head = Buffer.alloc(16);
    fs.readSync(fd, head, 0, 16, 0);
    const length = head.readUInt32LE(12);
    const json = Buffer.alloc(length);
    fs.readSync(fd, json, 0, length, 16);
    const out = [];
    const walk = (node, prefix) => {
      for (const [name, child] of Object.entries(node.files ?? {})) {
        const rel = prefix ? `${prefix}/${name}` : name;
        if (child.files) walk(child, rel);
        else out.push(rel);
      }
    };
    walk(JSON.parse(json.toString("utf-8")), "");
    return out;
  } finally {
    fs.closeSync(fd);
  }
}

export function checkPackage(root, { asar = false } = {}) {
  const globs = packedGlobs(fs.readFileSync(path.join(root, "electron-builder.yml"), "utf-8"));
  const { files, problems } = startupFiles(root);
  for (const rel of files) {
    if (!isPacked(rel, globs)) problems.push(`${rel} is needed at startup but not in electron-builder.yml files`);
  }
  if (asar) {
    const archive = path.join(root, ASAR);
    if (!fs.existsSync(archive)) {
      problems.push(`no packaged app at ${ASAR}; run npm run package first`);
    } else {
      const inside = new Set(asarFiles(archive));
      for (const rel of files) {
        if (!inside.has(rel.split(path.sep).join("/"))) problems.push(`${rel} is missing from app.asar`);
      }
    }
  }
  return { files, problems };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const asar = process.argv.includes("--asar");
  const { files, problems } = checkPackage(root, { asar });
  if (problems.length) {
    console.error(`package check: ${problems.length} problem(s)`);
    for (const p of problems) console.error(`  FAIL ${p}`);
    process.exit(1);
  }
  console.log(`package check: ${files.length} startup files present${asar ? " in app.asar" : " and packaged"}`);
}
