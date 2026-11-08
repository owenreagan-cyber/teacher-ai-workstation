import assert from "node:assert/strict";
import http from "node:http";
import { createRequire } from "node:module";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const { requestJson } = require("../out/main/cosd/http.js");

function withServer(handler, fn) {
  return new Promise((resolve, reject) => {
    const srv = http.createServer((req, res) => handler(req, res));
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

test("requestJson refuses non-loopback host", () => {
  assert.throws(() => requestJson("192.168.1.1", 9, "/health"));
});

test("requestJson reads health", async () => {
  await withServer((_req, res) => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true, service: "cosd", version: "0.1.0" }));
  }, async (port) => {
    const { status, body } = await requestJson("127.0.0.1", port, "/health");
    assert.equal(status, 200);
    assert.equal(body.ok, true);
    assert.equal(body.service, "cosd");
  });
});

test("response never includes token in client errors", async () => {
  await withServer((_req, res) => {
    res.writeHead(401, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: false, error_kind: "auth" }));
  }, async (port) => {
    const { body } = await requestJson("127.0.0.1", port, "/v1/status", { token: "abc123secret" });
    assert.equal(body.error_kind, "auth");
    assert.ok(!JSON.stringify(body).includes("abc123secret"));
  });
});
