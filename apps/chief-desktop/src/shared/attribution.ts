// Provider attribution for answers built from web search results (Brave's terms ask for it).
// Derived from what cos reported: web.search among the tools used and a sources block (or, for
// text from cos before the URLs are removed, result links in the answer). A "not set up" or
// "limit reached" answer has neither, so it gets no attribution.
import type { Turn } from "./types.js";

export const SEARCH_ATTRIBUTION = "Search by Brave";

export function searchAttribution(turn: Pick<Turn, "answer" | "tools_used"> & { blocks?: Turn["blocks"] }): string | null {
  if (!turn.tools_used.includes("web.search")) return null;
  const sourced = (turn.blocks ?? []).some((b) => b.type === "sources") || /(^|\s)https?:\/\/\S/.test(turn.answer);
  return sourced ? SEARCH_ATTRIBUTION : null;
}
