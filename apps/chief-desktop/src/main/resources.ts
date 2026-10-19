// The resource table: link id -> https URL, from cos answers and history. Main process only: the
// renderer gets link ids, never URLs, and opening one goes through openLink, which looks the id up
// here and re-checks the URL before handing it to the system browser.
import type { OpenLinkResult } from "../shared/types.js";
import { httpsUrl, LINK_ID_RE, type Resource } from "../shared/blocks.js";

export const MAX_RESOURCES = 2000;

export class ResourceTable {
  private readonly urls = new Map<string, string>();

  add(resources: Resource[]): void {
    for (const r of resources) {
      const url = httpsUrl(r.url);
      if (!LINK_ID_RE.test(r.id) || url === null) continue;
      this.urls.delete(r.id); // re-adding moves it to the newest end
      this.urls.set(r.id, url);
      if (this.urls.size > MAX_RESOURCES) this.urls.delete(this.urls.keys().next().value as string);
    }
  }

  /** The https URL for a link id, or null (unknown id, wrong shape, or not https). */
  get(linkId: unknown): string | null {
    if (typeof linkId !== "string" || !LINK_ID_RE.test(linkId)) return null;
    const url = this.urls.get(linkId);
    return url === undefined ? null : httpsUrl(url);
  }
}

/** Open a link by id. open() is shell.openExternal in the app; it only ever gets a URL from the table. */
export async function openLink(table: ResourceTable, linkId: unknown, open: (url: string) => Promise<void>): Promise<OpenLinkResult> {
  const url = table.get(linkId);
  if (url === null) return { ok: false, error: "That link isn't available.", error_kind: "usage" };
  try {
    await open(url);
    return { ok: true };
  } catch {
    return { ok: false, error: "The link couldn't be opened.", error_kind: "internal" };
  }
}
