# PROMPT — P1a.5: Rich Messenger (response blocks, weather visuals, charts, follow-ups)

## Where you are

- **Worktree:** `~/Projects/taw-cos-m1`.
- **Branch:** create `feature/cos-p1a5` from the current `feature/cos-p1a` HEAD, after the P1a
  fix batch is committed: `git switch -c feature/cos-p1a5`. Do not push or merge.
- **Read first:**
  - `docs/DECISIONS.md` (binding)
  - `cos/fastpath.py`
  - `cos/tools/weather.py`
  - `cos/brief.py`
  - `cos/agent.py`
  - `cos/tools/web_search.py`
  - `apps/chief-desktop/src/` (`main/cos.ts`, `shared/types.ts`, `shared/homeCard.ts`,
    `renderer/App.tsx`, `renderer/HomeCard.tsx`)
  - `evals/README.md`

## Goal

Answers in the compact window become visual and useful instead of terminal-shaped text:

- a time card and weather cards with day and night visuals
- an hourly chart and a 5-day forecast
- collapsed sources
- one primary action button
- clickable follow-up suggestions

The governing rule: **the model chooses meaning; `cos` chooses the blocks; the renderer chooses
the look.** No block data is ever written by the model.

## 1. Response contract (`cos`)

- **New fields on `cos ask --json`:** `blocks` (a list) and `suggestions` (a list).
  - Keep every existing field. Raycast and the text output must keep working unchanged; text
    mode prints the answer as today.
- **Block types (v1).** Every block has `type` and `id`.

  | Block | Fields |
  |---|---|
  | `time_card` | `time`, `date`, `is_day` (from today's sunrise and sunset when weather is available), `timezone` |
  | `weather_card` | `place` (display name), `now` (temp_f, feels_f, condition, condition_code, is_day, wind_mph), `today` (high_f, low_f, rain_pct), `sunrise`, `sunset`, `updated` |
  | `hourly_chart` | 12 points of {`hour_label`, `temp_f`, `rain_pct`, `condition_code`, `is_day`} |
  | `daily_forecast` | 5–7 days of {`day_label`, `high_f`, `low_f`, `rain_pct`, `condition_code`} |
  | `sources` | up to 5 of {`title`, `url`} (https only), shown collapsed |
  | `action` | {`label`, `link_id`}, one primary link (for example "Open live radar"), referring to a URL in this result's link table |

- **Link table:** a `links` table on the result, `[{link_id, url}]`, containing only https URLs
  taken from tool results. The renderer never receives a URL it can open by itself (see section
  4).
- **Suggestions:** at most 3, each {`label`, `prompt`}, written only by the deterministic
  presenter (section 2).
  - A suggestion prompt must never match the web search command. That keeps D-011 intact.
- **Session storage:** store `blocks`, `links`, and `suggestions` in session turns, with the
  validation extended in `check_turn`, so history reloads them. Old turns without them stay valid.
- **Validation:**
  - A Python validator checks every block before it is emitted.
  - A TypeScript validator (like `toTurn`) rebuilds blocks field by field in `main/cos.ts`.
    Unknown types are dropped, and a bad block never blanks the window.
- **Docs:** write the schema in `docs/response-blocks.md`. The iPhone app (P1c) will render the
  same schema.

## 2. Presenter (deterministic, `cos/present.py`)

Map tool results to blocks with no model involved:

- **Time:** `time.now` produces a `time_card`.
- **Weather:** `weather.today` produces a `weather_card`, plus an `hourly_chart` when the
  question mentions rain, radar, storm, hour, tonight, later, or this afternoon. A
  `daily_forecast` is added when the question mentions forecast, week, 5-day, weekend, tomorrow,
  or days.
- **Web search:** `web.search` produces a `sources` block and an `action` for the top result.
  - If the typed query contains a weather word and the name of a configured place, also run
    `weather.today` for that place through the gate and add its `weather_card` and
    `hourly_chart`.
  - The query itself is unchanged and still exactly as typed.
- **Suggestions:**
  - For weather, the ones not already shown, from "Tomorrow", "5-day forecast", and "<other
    place> weather".
  - For time, "Today's schedule".
  - For search, none in v1.

## 3. Weather data and places

- **Open-Meteo:** same host, so no egress change.
  - `current`: temperature, apparent temperature, weather code, wind, `is_day`.
  - `hourly`: the next 12 hours of `temperature_2m`, `precipitation_probability`,
    `weather_code`, `is_day`.
  - `daily`: 7 days of high, low, precipitation probability max, weather code, sunrise, sunset.
  - Keep the cache. Keep the existing `weather.today` fields, and add `tomorrow`, `hourly`, and
    `daily`.
- **Named places:** new config key `places`, defaulting to:
  `{"home": {"name": "Wilson, NC", "latitude": 35.72, "longitude": -77.92}, "work": {"name": "Clayton, NC", "latitude": 35.65, "longitude": -78.46}}`.
  - Existing `latitude` and `longitude` keys still define "home" if present.
  - Validate coordinates.
- **Tool argument:** `weather.today` takes an optional `place` argument. It accepts an enum of
  configured place keys and names, and defaults to home.
- **Fast path patterns** (anchored, whole message):
  - "weather in <place>", "<place> weather", "weather at work", "weather at home"
  - "5 day forecast", "forecast", "weather tomorrow"
  - each with a place variant
- **The model** may pass `place` only as one of the configured values; the gate validates the
  enum.
- **Chief never geocodes** arbitrary place names in this phase. An unknown place gets "I only
  know Wilson (home) and Clayton (work)."

## 4. Renderer

- **Components:** `src/renderer/blocks/` holds `TimeCard`, `WeatherCard`, `HourlyChart`,
  `DailyForecast`, `SourcesList` (collapsed by default), `ActionButton`, and `SuggestionChips`,
  plus a `BlockList` that renders known types in order.
- **Visuals:** inline SVG and CSS only. No image files from the network, no icon library, no
  chart library.
  - Condition icons: sun, moon, sun with cloud, moon with cloud, cloud, rain, heavy rain,
    thunderstorm, snow, fog. Each has day and night variants, mapped from WMO codes in one
    shared table.
  - Card backgrounds: a warm daylight gradient for sunny, cool grey-blue for cloudy, deep blue
    for rain, navy with a moon for night, and a restrained amber accent for storms.
  - A subtle rain animation, disabled under `prefers-reduced-motion`.
  - Respect light and dark appearance.
- **Charts:** `HourlyChart` is an inline SVG with bars for rain % and a line for temperature,
  hour labels, and accessible text.
- **Time card:** large time and date, with a day or night treatment from `is_day`.
- **Text with blocks:** the model's text appears as one short paragraph above the blocks.
- **Home card:** reuses `WeatherCard`'s icon and background for its weather line.
- **Opening links (security):** add one bridge function, `openLink(turnId, linkId)`.
  - The main process looks up `linkId` in that turn's validated link table, requires https, and
    calls `shell.openExternal`.
  - The renderer never passes a raw URL.
  - Update the static checks: preload exposes exactly the allowed functions plus `openLink`, the
    renderer has no network, and no `shell.openExternal` call takes a renderer-supplied string.
- **Suggestion clicks:** clicking a suggestion sends its prompt exactly like typed input,
  through the same ask path. The audit records `input_source: "suggestion"`.
  - Suggestions are disabled while a request is running.

## 5. Search answer fix (observed bug)

The real model listed markdown links and URLs in its summary even though the rules forbid it,
so every link appeared twice. Fix it deterministically:

- After the model writes the search summary, strip markdown links (keep the link text), bare
  URLs, and lines that are only links.
- If the summary drops below 20 characters after stripping, use "Here's what I found." followed
  by the sources.
- Keep the `summary_not_contains` harness check, and add real-model cases for it.

## Tests and validation

- **Python:**
  - presenter mapping for each block type
  - block validation, including rejecting bad blocks
  - the places config and the place enum
  - fast-path weather and place patterns, plus near-misses ("is Clayton far" is not a weather
    question)
  - suggestions never matching the search command
  - link table https-only
  - summary stripping
  - sessions storing and reloading blocks
- **Harness:**
  - fixtures with hourly and daily data, including a night case (`is_day` 0) and a rain case
  - a `rich_blocks` suite asserting block types and suggestions for time, weather, Clayton,
    forecast, and "search weather radar wilson nc" (search plus a weather card)
  - CERT-009 must still pass with suggestions present
- **Desktop:**
  - validator tests (unknown or malformed blocks dropped)
  - `openLink` main-process validation tests (unknown `linkId`, non-https, wrong turn)
  - the WMO icon-mapping table
  - static checks
- **Run:**
  ```
  python3.12 -m unittest discover -s tests/cos -p 'test_*.py'
  python3.12 -m unittest discover -s tests/evals -p 'test_*.py'
  cd apps/chief-desktop && npm test && npm run typecheck && npm run build
  python3.12 evals/harness/run.py --model fake
  python3.12 evals/harness/run.py --suite rich_blocks --model real
  git diff --check
  ```
- **Don't launch the app.** Owen checks the look.

## Docs

- **`CHIEF-OF-STAFF.md`:**
  - what the cards show
  - named places, and how to add or change one in config, as an exact JSON example
  - suggestions
- **The review bundle:** update `docs/p1a-review-bundle.md`, or add `docs/p1a5-review-bundle.md`
  with the `openLink` bridge addition as a focus item.
- **Owen's live check:** exact steps to rebuild and install Chief.app, then try:
  - "what time is it"
  - "weather"
  - "weather in Clayton"
  - "5 day forecast"
  - "search weather radar wilson nc"
  - clicking a suggestion and the "Open live radar" button

## Report

- commit SHAs and test counts
- fake run with all CERTs
- the real `rich_blocks` result with 3 quoted answers and their block types
- any failures listed, not fixed
- `git status -sb`
