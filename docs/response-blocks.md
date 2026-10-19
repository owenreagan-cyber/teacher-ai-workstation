# Response blocks

Status: P1a.5 · 2026-10-18 · Owner: Owen · Code: `cos/blocks.py`, `cos/present.py`,
`apps/chief-desktop/src/shared/blocks.ts`

Chief's answers are rich in the desktop window: weather cards, forecast charts, sources,
follow-up buttons. The rule is **the model chooses meaning, `cos` chooses the blocks, the window
chooses the look.** The model never writes block data: blocks are built by code from tool
results and from what the answering path recorded. Any future surface (the iPhone app) renders
the same format.

## Where blocks appear

`cos ask --json` returns two fields next to the existing ones:

```json
{"ok": true, "answer": "…plain text…", "tools_used": ["web.search"], "intent": "web_lookup",
 "search_query": "when do the ny rangers play",
 "blocks": [ … ],
 "resources": [{"id": "lnk-3f1c0a9b2e4d5f60", "url": "https://example.com/schedule"}]}
```

- `answer` stays: the CLI, Raycast, and the Copy button use it. It may contain URLs from that
  turn's tool results (the numbered sources), and nothing else (CERT-011).
- `blocks` is the rich form. **No string in a block contains a URL.**
- `resources` maps link ids to https URLs. Only the desktop **main process** reads it.
- Session turns store `blocks` and `resources` (optional fields), so `cos history --json`
  returns them and links still open after a relaunch. Old turns without them stay valid.

## Block types

Every block is an object with `type` and exactly the fields below. Numbers are integers or
`null`; temperatures are °F (−100..150), percentages 0..100.

| `type` | Fields | Notes |
|---|---|---|
| `text` | `text` (≤ 4000) | The answer prose, URLs removed. |
| `weather_now` | `place`, `temp_f`, `feels_like_f`, `conditions`, `is_day` (bool or null), `high_f`, `low_f`, `rain_chance_pct`, `wind_mph`, `as_of` (or null) | A card. `place` is the named place ("Sims, NC"). |
| `forecast_hourly` | `place`, `points`: 1–24 of {`time`, `temp_f`, `rain_chance_pct`, `conditions`, `is_day`} | A small chart: a temperature line over rain-chance bars. |
| `forecast_daily` | `place`, `days`: 1–7 of {`date` (YYYY-MM-DD), `label`, `high_f`, `low_f`, `rain_chance_pct`, `conditions`} | Rows with a low–high range bar. |
| `sources` | `items`: 1–5 of {`title`, `site`, `link_id` (`lnk-` + 16 hex, or null)} | Search results, collapsed by default. `link_id` is null when the result has no https URL. |
| `searched` | `query` (≤ 200) | The exact query that left the Mac ("Searched: …"). |
| `suggestions` | `items`: 2–4 of {`label` (≤ 60), `message` (≤ 300)} | Follow-up buttons. A click sends `message` as if Owen typed it. |
| `notice` | `level` (`info` or `warning`), `text` (≤ 500) | Notes such as "I left out steps that delete files…". |

At most 12 blocks per answer. Validation is the same in Python (`cos/blocks.py`,
`validate_blocks`: an unknown type or a bad field raises) and TypeScript (`toBlock` /
`toBlocks`: an unknown or bad block is dropped, so one bad block never blanks the answer).

### What each path returns

| Path | Blocks |
|---|---|
| Web search (typed or automatic) | `text` (the summary), `searched`, `sources` (+ `resources`) |
| Weather now | `text`, `weather_now`, `suggestions` |
| Weather tomorrow, a day, weekend, 5 day, next week | `text`, `forecast_daily`, `suggestions` |
| Weather hourly, tonight | `text`, `forecast_hourly`, `suggestions` |
| Unknown place | `text`, `suggestions` (the known places) |
| Capabilities, brief | `text`, `suggestions` |
| Auto web search off | `text`, `suggestions` ("Search the web" sends `search <query>`) |
| Everything else | `text`, plus a `notice` for each note |

## Links: ids in the window, URLs in the main process

1. `cos` puts each https result URL in `resources` under `lnk-<first 16 hex of SHA-256(url)>`.
2. The desktop main process (`CosRunner`) validates the answer, hands `resources` to its
   resource table (`src/main/resources.ts`), and removes every URL from the text it passes to
   the window (`answer`, `notices`, `question`). The window never receives a URL.
3. A source's button calls `window.chief.openLink(linkId)`. The main process looks the id up,
   re-checks that the URL is plain https (no credentials, no control characters), and only then
   calls `shell.openExternal`. That is the only `openExternal` call in the app (static check).
   An unknown id, or anything that is not https, is refused.

## Suggestions

A suggestion button sends its `message` text through the same ask path as the input box,
nothing more: no hidden parameters, no tool, no URL. Buttons are disabled while Chief is
answering. Suggestions are chosen by code (`cos/present.py`), never by the model.
