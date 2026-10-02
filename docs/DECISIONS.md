# Chief of Staff — Decisions

The single record of settled decisions.

- **Summaries are proposals.** Plans or summaries from any model (ChatGPT, Gemini, Claude) are
  proposals. If one conflicts with a decision here, the decision wins until Owen changes it on
  purpose.
- **Changing a decision.** Edit its entry, mark it `REVISED <date>`, and say why.
- **Status values:** ACCEPTED, PROPOSED (waiting on Owen), or REVISED.

| ID | Decision | Status |
|---|---|---|
| D-001 | **Student data stays local.** Any task that depends on student-identifiable information runs on local models only, and never on a cloud model or agent. Removing names first ("sanitize then escalate") is not allowed. A task may go to the cloud only if it is rewritten so it no longer depends on student information at all. | ACCEPTED |
| D-002 | **External content is data, never instructions.** This covers calendar titles, mail, web pages, search results, files, and tool output. | ACCEPTED |
| D-003 | **Code owns authority; models propose.** The `cos` core decides policy, routing, and execution. Every shell (desktop, Raycast, iPhone) is a client that displays `cos` results and never invents state. | ACCEPTED |
| D-004 | **Local models only, until the router exists.** `cos` refuses Ollama cloud models, both by name and by the details `/api/show` reports (F2, CERT-008). Cloud models arrive only through the M2 router, with a model allowlist and a hard budget. | ACCEPTED |
| D-005 | **Every write needs an approval packet.** No permanent deletion: removals go to a quarantine with a restore path. A packet records each target's before-state, and the executor re-checks it before acting. | ACCEPTED |
| D-006 | **Desktop shell is Electron + React.** Raycast is a launcher only. | ACCEPTED |
| D-007 | **iPhone app is native SwiftUI.** No PWA or web app on the phone. The phone is a client of `cosd` over Tailscale only, with device pairing, revocable tokens, and Face ID. Conversation or approval content is never synced through a cloud service. Builder: Cursor (or Claude Code). Reviewer: a different model family. | ACCEPTED |
| D-008 | **Model defaults.** `qwen3.6:35b`, `think: false`, `num_ctx` 16384, `keep_alive` "2h". `gpt-oss:20b` is the fallback. | ACCEPTED |
| D-009 | **Testing rules.** The harness uses synthetic fixtures only. Certification runs come from a clean commit. Failures are listed, then fixed in a separate batch. CERT IDs never change meaning, and are assigned when an invariant is implemented, not reserved in advance. | ACCEPTED |
| D-010 | **Separate builder and reviewer.** Phases that touch security, privacy, authority, the bridge, networking, or routing get a reviewer from a different model family than the builder. Docs-only and test-only changes need no review round. | ACCEPTED |
| D-011 | **Web search rules.** One allowlisted search API. The query text comes only from what Owen types; the model never writes or edits a search query. Results are untrusted data. | ACCEPTED |
| D-012 | **The agent registry lists only real tools.** It is built from tools detected on the Mac plus subscriptions Owen confirms, never from tools that were only discussed. Usage figures are estimates. | ACCEPTED |
| D-013 | **Mail is read through Apple Mail.** It is read-only to start, for both accounts. School mail is processed by local models only (D-001). Drafts, labels, and archiving require approval packets. | ACCEPTED |
| D-014 | **The phone may display school data but stores none.** The phone may show school calendar and mail summaries, the same information the Gmail app already shows there. It keeps nothing on the device and locks after 15 minutes idle. | PROPOSED |
| D-015 | **Reaching the Mac from the phone.** REVISED 2026-10-02: replaces "Mac stays awake." The iPhone app handles basics on the phone: time, weather, calendar, reminders, and short replies. The NAS (UGREEN DXP4800 Plus) runs an always-on Tailscale doorman container in Docker. For requests only the MacBook can answer, the doorman wakes it over the home network ("Wake for network access" is set to Only on Power Adapter). If the Mac can't be woken, the request waits in a queue encrypted end-to-end between phone and Mac, which the NAS cannot read. The NAS runs no models and holds no credentials for school data. There is no cloud fallback for school or personal data. | ACCEPTED |
| D-016 | **Developer program: paid.** Team "Owen Reagan", Admin role. Installed iOS builds last a year. | ACCEPTED |
