# Printer Certification

Printable Teacher OS outputs must pass a real-world Ricoh printer certification flow before they are trusted for classroom use.

## Target real-world print path

- Mac browser
- Command-P
- default margins
- default scale
- wireless Ricoh printer
- school WiFi
- US Letter paper

## Required checks for generated worksheets later

Generated worksheets later must pass:

- browser preview
- PDF render
- no horizontal overflow
- smart page breaks
- answer key present
- physical Ricoh print test
- teacher approval

## Certification test file

Open and print:

```text
assets/print-tests/ricoh-letter-test.html
```

## Steps

1. Open `assets/print-tests/ricoh-letter-test.html` in Chrome or Arc.
2. Press Command-P.
3. Keep default margins and default scale.
4. Select the wireless Ricoh printer while on school WiFi.
5. Confirm the page preview stays within the visible safe print area.
6. Confirm the answer key starts on a new page.
7. Print on US Letter paper.
8. Review the physical printout for clipped text, overflow, missing content, and bad page breaks.
9. Mark the Ricoh printer certification complete in `docs/day-1-manual-steps.md`.
