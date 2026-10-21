// Packaging check (scripts/check-package.mjs): a module the app needs at startup that would be
// missing from the packaged app is caught at build time. Temp layouts only, plus the real build.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { after, test } from "node:test";

import { asarFiles, checkPackage, isPacked, packedGlobs } from "../scripts/check-package.mjs";

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "chief-package-test-"));
after(() => fs.rmSync(dir, { recursive: true, force: true }));

const YML = "appId: x\nfiles:\n  - package.json\n  - out/main/**\n  - out/preload/**\n  - out/shared/**\n  - dist/renderer/**\nasar: true\n";

function layout(name, files, yml = YML) {
  const root = path.join(dir, name);
  const all = {
    "package.json": JSON.stringify({ main: "out/main/main.js" }),
    "electron-builder.yml": yml,
    "dist/renderer/index.html": '<script type="module" src="./assets/index.js"></script><link rel="stylesheet" href="./assets/index.css">',
    "dist/renderer/assets/index.js": "",
    "dist/renderer/assets/index.css": "",
    "out/preload/preload.js": 'require("electron");',
    ...files,
  };
  for (const [rel, body] of Object.entries(all)) {
    if (body === null) continue;
    fs.mkdirSync(path.dirname(path.join(root, rel)), { recursive: true });
    fs.writeFileSync(path.join(root, rel), body);
  }
  return root;
}

test("the files: globs are read from electron-builder.yml", () => {
  assert.deepEqual(packedGlobs(YML), ["package.json", "out/main/**", "out/preload/**", "out/shared/**", "dist/renderer/**"]);
  assert.equal(isPacked("out/shared/blocks.js", packedGlobs(YML)), true);
  assert.equal(isPacked("out/other/x.js", packedGlobs(YML)), false);
});

test("a complete layout passes", () => {
  const root = layout("ok", {
    "out/main/main.js": 'require("electron"); require("node:path"); require("./cos.js");',
    "out/main/cos.js": 'require("../shared/blocks.js");',
    "out/shared/blocks.js": "",
  });
  const { files, problems } = checkPackage(root);
  assert.deepEqual(problems, []);
  assert.ok(files.includes(path.normalize("out/shared/blocks.js")));
});

test("a missing startup module fails", () => {
  const root = layout("missing", { "out/main/main.js": 'require("./cos.js");', "out/main/cos.js": 'require("../shared/gone.js");' });
  assert.deepEqual(checkPackage(root).problems, [`missing ${path.normalize("out/shared/gone.js")}`]);
});

test("a startup module outside the packaged globs fails", () => {
  const yml = YML.replace("  - out/shared/**\n", "");
  const root = layout("unpacked", { "out/main/main.js": 'require("../shared/x.js");', "out/shared/x.js": "" }, yml);
  assert.match(checkPackage(root).problems.join("\n"), /out\/shared\/x\.js is needed at startup but not in electron-builder\.yml files/);
});

test("a bare package require fails (the app ships no node_modules)", () => {
  const root = layout("bare", { "out/main/main.js": 'require("lodash");' });
  assert.match(checkPackage(root).problems.join("\n"), /requires lodash, which is not packaged/);
});

test("a renderer asset referenced by index.html must exist", () => {
  const root = layout("asset", { "out/main/main.js": "", "dist/renderer/assets/index.css": null });
  assert.match(checkPackage(root).problems.join("\n"), /missing dist\/renderer\/assets\/index\.css/);
});

function writeAsar(file, tree) {
  const json = Buffer.from(JSON.stringify(tree));
  const head = Buffer.alloc(16);
  head.writeUInt32LE(4, 0);
  head.writeUInt32LE(json.length + 8, 4);
  head.writeUInt32LE(json.length + 4, 8);
  head.writeUInt32LE(json.length, 12);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, Buffer.concat([head, json]));
}

test("--asar checks the startup files inside app.asar", () => {
  const root = layout("asar", { "out/main/main.js": 'require("./cos.js");', "out/main/cos.js": "" });
  const asar = path.join(root, "release/mac-arm64/Chief.app/Contents/Resources/app.asar");
  assert.match(checkPackage(root, { asar: true }).problems.join("\n"), /no packaged app/);
  const f = { size: 0, offset: "0" };
  const tree = { files: {
    "package.json": f,
    out: { files: { main: { files: { "main.js": f } }, preload: { files: { "preload.js": f } } } },
    dist: { files: { renderer: { files: { "index.html": f, assets: { files: { "index.js": f, "index.css": f } } } } } },
  } };
  writeAsar(asar, tree);
  assert.ok(asarFiles(asar).includes("out/main/main.js"));
  assert.deepEqual(checkPackage(root, { asar: true }).problems, [`${path.normalize("out/main/cos.js")} is missing from app.asar`]);
  tree.files.out.files.main.files["cos.js"] = f;
  writeAsar(asar, tree);
  assert.deepEqual(checkPackage(root, { asar: true }).problems, []);
});

// `npm test` does not run the renderer build (vite), so on a fresh checkout dist/ does not exist yet.
// `npm run build` runs this same check itself, after building.
const NO_BUILD = fs.existsSync(path.join(APP, "dist", "renderer", "index.html"))
  ? false
  : "dist/renderer is missing: run `npm run build` first (it runs this check after building)";

test("the real build passes the check", { skip: NO_BUILD }, () => {
  assert.deepEqual(checkPackage(APP).problems, []);
});
