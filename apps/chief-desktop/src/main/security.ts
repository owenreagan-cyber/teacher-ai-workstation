// Session and web-contents lockdown: CSP, local-only loading, no navigation, no permissions.
import fs from "node:fs";
import path from "node:path";

import { app, protocol, session, type WebContents } from "electron";

export const CSP =
  "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; " +
  "connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";

export const APP_SCHEME = "app";
export const APP_HOST = "chief";
export const APP_URL = `${APP_SCHEME}://${APP_HOST}/index.html`;

const DEV_URL_RE = /^http:\/\/localhost:\d{2,5}\/?$/;

/** The Vite dev server URL, only in an unpackaged build and only on http://localhost:<port>. */
export function devServerUrl(): string | null {
  const url = process.env.CHIEF_DEV_URL;
  return !app.isPackaged && url && DEV_URL_RE.test(url) ? url : null;
}

// Must run before app "ready".
export function registerAppScheme(): void {
  protocol.registerSchemesAsPrivileged([
    { scheme: APP_SCHEME, privileges: { standard: true, secure: true, supportFetchAPI: false } },
  ]);
}

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
};

/** Serve the bundled renderer from rendererDir under app://chief/, with the CSP header. */
export function serveRenderer(rendererDir: string): void {
  const root = path.resolve(rendererDir);
  protocol.handle(APP_SCHEME, async (request) => {
    try {
      const url = new URL(request.url);
      const rel = decodeURIComponent(url.pathname).replace(/^\/+/, "") || "index.html";
      const file = path.resolve(root, rel);
      if (url.host !== APP_HOST || (file !== root && !file.startsWith(root + path.sep))) {
        return new Response("Not found", { status: 404 });
      }
      const body = await fs.promises.readFile(file);
      const type = MIME[path.extname(file)] ?? "application/octet-stream";
      return new Response(body, {
        headers: { "Content-Type": type, "Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff" },
      });
    } catch {
      return new Response("Not found", { status: 404 });
    }
  });
}

function allowedRequest(url: string, devUrl: string | null): boolean {
  if (url.startsWith(`${APP_SCHEME}://${APP_HOST}/`)) return true;
  if (url.startsWith("devtools://")) return !app.isPackaged;
  if (devUrl) {
    const origin = new URL(devUrl).origin;
    return url === origin || url.startsWith(`${origin}/`);
  }
  return false;
}

export function lockDownSession(devUrl: string | null): void {
  const ses = session.defaultSession;
  // Deny every permission request and check (camera, mic, notifications, clipboard, …).
  ses.setPermissionRequestHandler((_wc, _permission, callback) => callback(false));
  ses.setPermissionCheckHandler(() => false);
  ses.setDevicePermissionHandler(() => false);
  // No network: only the bundled renderer (or the local dev server in dev) may load.
  ses.webRequest.onBeforeRequest((details, callback) => {
    callback({ cancel: !allowedRequest(details.url, devUrl) });
  });
  // CSP on every response (the dev server's included); app:// responses also carry it.
  ses.webRequest.onHeadersReceived((details, callback) => {
    const headers = { ...details.responseHeaders };
    for (const key of Object.keys(headers)) {
      if (key.toLowerCase() === "content-security-policy") delete headers[key];
    }
    headers["Content-Security-Policy"] = [CSP];
    callback({ responseHeaders: headers });
  });
}

/** Applied to every WebContents the app ever creates. */
export function lockDownContents(contents: WebContents): void {
  contents.on("will-navigate", (event) => event.preventDefault());
  contents.on("will-redirect", (event) => event.preventDefault());
  contents.on("will-attach-webview", (event) => event.preventDefault());
  contents.setWindowOpenHandler(() => ({ action: "deny" }));
}
