# Teacher Knowledge Vault — Extraction Cost and Budget Gate

Last updated: 2026-07-04

```text
Status: cost controls — API cost estimate $0.00 in M6
```

## Cost Controls

- API cost estimate must be `$0.00` unless explicitly approved later
- no cloud OCR without per-run estimate
- no AI calls without budget gate
- no background extraction jobs
- max files per approved run required before implementation
- max pages per approved run required before implementation
- selected-page OCR before full-document OCR
- cache lookup before extraction/OCR
- cancel/stop behavior required before implementation
- progress reporting required before implementation

## Local-First / Free-First Policy

Native extraction and local OCR are preferred. Cloud OCR/API escalation is rare and approval-gated. Cache lookup precedes any future extraction or OCR spend.
