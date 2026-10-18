// Provider attribution for answers built from web search results (Brave's terms ask for it).
// Derived from what cos reported: web.search among the tools used and result links in the answer.
// A "not set up" or "limit reached" answer has no links, so it gets no attribution.
import type { Turn } from "./types.js";

export const SEARCH_ATTRIBUTION = "Search by Brave";

export function searchAttribution(turn: Pick<Turn, "answer" | "tools_used">): string | null {
  return turn.tools_used.includes("web.search") && /(^|\s)https?:\/\/\S/.test(turn.answer) ? SEARCH_ATTRIBUTION : null;
}
