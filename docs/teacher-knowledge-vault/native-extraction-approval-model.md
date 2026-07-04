# Teacher Knowledge Vault — Native Extraction Approval Model

Last updated: 2026-07-04

```text
Status: architecture model — native extraction future only
runtime_executed: false in M6
```

## Definition

Native extraction reads selectable text from files that already contain embedded text — **future only**, teacher-approved, and scoped.

## Planned File Types (Future Only)

PDF with embedded text, DOCX, PPTX, XLSX, HTML, TXT/Markdown

## Approved Future Extraction Limits

- metadata first
- title/first headings first
- first page or first few paragraphs before full extraction
- no extraction from `99_DO_NOT_SCAN`
- restricted extraction labeling for `10_TEACHER_ONLY`
- no student-facing disclosure from teacher-only extraction
- extracted text stored as cache/evidence only after approval
- extraction results routed to review queue
- extraction does not classify or organize by itself

## Rules

- Native extraction must come before OCR escalation
- Whole-document processing must not be default
- Future execution remains blocked until explicit Owen-approved runtime mission

Fixture: `assistant/teacher-knowledge-vault/m6/fake-native-extraction-eligibility.json`
