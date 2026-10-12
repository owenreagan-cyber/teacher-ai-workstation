# Canvas HTML / Unicode Compatibility Contract

```text
Status: framework-only (evidence pending)
Authority: OWNER_POLICY
Approved by: Owen Reagan
```

## Purpose

Provide the Canvas-writing LLM an **evidence-backed rulebook** for what HTML and
Unicode Canvas actually accepts and renders, instead of relying on generic web
HTML knowledge. Every conclusion must be backed by a deliberate, guard-gated
sandbox write test and its readback — never by assumption.

## Test sandbox

```text
Course: 24399 — Math Automation Sandbox
Purpose: controlled Canvas API / HTML / Unicode / attachment / rendering experiments
```

Hard invariant:

```text
published == false BEFORE test
published == false AFTER test
```

Authoritative machine-readable contract:
`config/curriculum/canvas/canvas-test-sandbox.json`.

The sandbox has no students, parents, observers, or other family-facing users,
so it is appropriate for deliberate write tests.

### Allowed

```text
create/update/delete test pages
create test announcements
test HTML sanitization
test inline styles / gradients / flex layouts
test emoji / Unicode
test links/buttons
test images/attachments
test Canvas readback normalization
test page/announcement HTML differences
test mobile/iPad rendering
test API behavior
test LLM-generated Canvas-safe HTML
```

### Forbidden

```text
publishing the course
inviting/enrolling users
adding students / observers
cross-listing
changing term/account settings
touching production courses during experiments
```

## Guard sequence (every run)

```text
1. GET course 24399
2. verify published == false
3. verify course ID == 24399
4. perform only approved sandbox writes
5. read back exact Canvas-rendered HTML
6. verify published == false again
7. optionally delete test artifact
8. record findings locally
```

## Compatibility matrix

Machine-readable: `config/curriculum/canvas/canvas-html-compatibility.json`.

### HTML

```text
headings, div, span, p, strong, em, ul, ol, li, table,
flex, flex-wrap, border-radius, borders, gradients, box-shadow,
text-align, inline font sizing, inline spacing, links/buttons,
details/summary, hr, blockquote
```

### Unicode

```text
en dash –, em dash —, bullet •, arrow →, check ✓, star ★,
lightning ⚡, leaf 🍂, maple 🍁, book 📚, calendar 📅, link 🔗,
bus 🚌, birthday 🎂, microscope 🔬, water 💧, party 🎉
```

### Riskier Unicode

```text
variation-selector emoji
skin-tone modifiers
ZWJ sequences
flags
combined family/person emoji
```

## Capture fields

For each tested item record:

```text
SOURCE HTML
→ Canvas API accepted?
→ Canvas readback HTML
→ desktop browser render
→ iPad A16 render
→ sanitized/changed?
→ safe for future use?
```

## Status vocabulary

```text
VERIFIED_SAFE                — renders correctly everywhere tested
VERIFIED_WITH_NORMALIZATION  — safe, but Canvas rewrites/normalizes the HTML
UNSUPPORTED                  — rejected or stripped by Canvas
DEVICE_VARIANT               — renders differently across desktop vs iPad
REQUIRES_MORE_TESTING        — not yet evidenced
```

## Current state

Evidence has been recorded from a guard-gated sandbox write test in course 24399.
The following are now `VERIFIED_SAFE` (Canvas preserved them byte-for-byte in
readback, aside from the global CSS/JS wrapper):

```text
HTML structure: h1, h2, h3, p, div, span, strong, em, ul, ol, li,
                table (thead/tbody), flex, flex-wrap
CSS:            background-color, color, border, border-radius, padding,
                margin, font-size, text-align, linear-gradient, position:absolute
Unicode:        en dash, em dash, bullet, check ✓, heavy check ✔, arrow →,
                star ★, white star ⭐, lightning ⚡, leaf 🍂, maple 🍁, book 📚,
                calendar 📅, link 🔗, birthday 🎂, microscope 🔬, water 💧,
                party 🎉, smart quotes, variation-selector ❤️, ZWJ family
```

`UNSUPPORTED` (Canvas strips these from inline styles):

```text
box-shadow
CSS animation
```

`VERIFIED_WITH_NORMALIZATION` (Canvas rewrites but preserves):

```text
the page body wrapper — Canvas prepends a global <link rel=stylesheet ... canvas_global_app.css>
and appends a global <script ... canvas_global_app.js> around the submitted body
HTML entities — Canvas normalizes raw ampersands, e.g. "Water Bottles & Drinks"
    reads back as "Water Bottles &amp; Drinks"; renders identically
```

### Validator guidance

- Generated body fragments must NOT contain `<script>`, `<link>`, external CSS,
  or external JS. Canvas may add its own global wrapper
  (`canvas_global_app.css` / `canvas_global_app.js`) on readback; these platform
  wrappers are expected and validators must ignore them.
- Normal HTML escaping (e.g. `&` → `&amp;`) is normalization, not corruption.
  Validators must not flag a single, correctly-escaped entity as a mismatch.

Still `REQUIRES_MORE_TESTING`:

```text
links/buttons, details/summary, hr, blockquote
skin-tone modifiers, flags (desktop + iPad visual render pending)
```

The machine-readable evidence lives in
`config/curriculum/canvas/canvas-html-compatibility.json` (`results` array) and
the local readback dumps under `.local/canvas-llm/canvas-html-lab/`.

## Sandbox identity

Course `24399` is a **sandbox-only** identity with `mustRemainUnpublished=true`.
The school Canvas URL is intentionally **not** committed; the course ID/name and
the permanent unpublished invariant are sufficient for most logic.
