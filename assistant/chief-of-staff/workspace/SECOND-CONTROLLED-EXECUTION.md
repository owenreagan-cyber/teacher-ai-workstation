# Phase L.5G Second Controlled Execution

Phase L.5G authorizes one request for the fixed Grade 4 Writing Launcher entity
through loopback-only Ollama, `qwen3.5:35b`, task `explain`, and
`local-model-response.v2`.

The execution order is fixed:

1. Build the existing sanitized `AIContextPackage`.
2. Build the current closed response vocabulary.
3. Validate an ideal deterministic v2 candidate.
4. Render that ideal candidate deterministically.
5. Confirm the static runtime policy and exact v2 payload.
6. Confirm Ollama and the exact model are already available.
7. Make at most one model request.
8. Decode the final JSON without repair.
9. Validate schema and grounding.
10. Render accepted references or return safe diagnostics and stop.

The execution wrapper does not own transport. `ollama_runtime.py` remains the
only runtime adapter and enforces one attempt, no retry, no fallback, no tools,
no vision, no startup, no pull, no persistence, and no action authority.

`controlled_execution.py` owns only deterministic gates, sanitized semantic
summaries, accepted-reference rendering, outcome classification, and an
in-memory audit. It contains no network or persistence primitive.

The runner has no arguments and one execution call site. Preflight failure
returns `PREFLIGHT STOP`. A validation failure after the request returns
`SAFE REJECTION` with finite codes only. A fully accepted reference selection
returns `PASS` and wording rendered exclusively from Chief of Staff context.

No live result, model candidate, prompt transcript, hidden reasoning, or audit
record is written to disk.
