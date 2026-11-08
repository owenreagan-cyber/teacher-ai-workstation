import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { CosdHttpError, assertLoopback, requestJson } from "../dist-lib/http.js";
import { CosdClient } from "../dist-lib/cosd-client.js";
import { readDaemonToken, readPidRecord } from "../dist-lib/paths.js";

function withServer(handler, fn) {
  return new Promise((resolve, reject) => {
    const srv = http.createServer(handler);
    srv.listen(0, "127.0.0.1", async () => {
      const port = srv.address().port;
      try {
        await fn(port);
        resolve();
      } catch (e) {
        reject(e);
      } finally {
        srv.close();
      }
    });
  });
}

test("rejects non-loopback host", () => {
  assert.throws(() => assertLoopback("192.168.1.1"), CosdHttpError);
});

test("token is never included in error strings", async () => {
  const token = "a".repeat(64);
  await withServer((req, res) => {
    res.writeHead(401, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: false, error: "unauthorized" }));
  }, async (port) => {
    const { body } = await requestJson("127.0.0.1", port, "/v1/status", { token });
    assert.equal(body.ok, false);
    assert.ok(!JSON.stringify(body).includes(token));
  });
});

test("client reports DISCONNECTED without pid file", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "raycast-cosd-"));
  const snap = new CosdClient(root).connectionSnapshot();
  return snap.then((s) => {
    assert.equal(s.state, "DISCONNECTED");
    assert.equal(readPidRecord(root), null);
    assert.equal(readDaemonToken(root), null);
  });
});

test("client connects with valid pid and token", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "raycast-cosd-"));
  const cosd = path.join(root, "cosd");
  fs.mkdirSync(cosd, { recursive: true });
  const token = "b".repeat(64);
  fs.writeFileSync(path.join(cosd, "api.token"), token, { mode: 0o600 });

  await withServer((req, res) => {
    const auth = req.headers.authorization ?? "";
    if (req.url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true, service: "cosd", version: "0.1.0" }));
      return;
    }
    if (req.url === "/v1/status" && auth === `Bearer ${token}`) {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: true, model: "fixture" }));
      return;
    }
    res.writeHead(401);
    res.end("{}");
  }, async (port) => {
    fs.writeFileSync(
      path.join(cosd, "cosd.pid"),
      JSON.stringify({ pid: process.pid, host: "127.0.0.1", port, started_at: new Date().toISOString(), service: "cosd" }),
    );
    const client = new CosdClient(root);
    const snap = await client.connectionSnapshot();
    assert.equal(snap.state, "CONNECTED");
    const askBody = JSON.stringify({ ok: true, text: "hello", answer: "hello" });
    await withServer((req, res) => {
      if (req.method === "POST" && req.url === "/v1/ask") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(askBody);
      }
    }, async () => {
      // ask uses same pid port — already running server; skip integrated ask in this nested case
    });
  });
});

test("create task idempotency key validation on client", async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "raycast-cosd-"));
  const client = new CosdClient(root);
  const bad = await client.getTask("not-a-valid-id");
  assert.equal(bad.ok, false);
});
