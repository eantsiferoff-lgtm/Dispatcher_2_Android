---
name: 1c-ut-documents
description: >
  Process invoices, bills, waybills, UTD/UPD, acts and other primary accounting documents from
  PDF/JPEG/PNG or text, including English and Japanese documents. Use when the user needs
  recognition, Russian translation, field extraction, arithmetic checks, operator review, or a
  structured table/file for 1C:Управление торговлей 8.3.
metadata:
  version: "1.0"
---

# 1C:UT Documents

## Goal

Turn a primary document into verified, structured data suitable for operator review and subsequent
entry/import into 1C:Управление торговлей 8.3.

## Workflow

1. Determine document type and language.
2. Read the full document; if foreign, translate relevant content into Russian.
3. Extract:
   - supplier and buyer;
   - document number/date;
   - currency and payment terms;
   - bank/payment details when present;
   - product names, SKUs/articles, units, quantity, unit price, discounts, tax/VAT and line totals;
   - document subtotal/tax/total.
4. Check line arithmetic and totals.
5. Mark unreadable or ambiguous fields explicitly.
6. Never guess a value merely to fill a field.
7. Show a clear operator-review view before treating the data as final.
8. When requested, create an XLSX/CSV structure suitable for further mapping/import into 1C.

## Output

Provide:
1. Short document summary.
2. Header/requisites.
3. Item table.
4. Arithmetic check.
5. Fields requiring operator review.
6. Structured 1C-oriented data/file when requested.

## Quality checks

- Preserve original units and currency.
- Do not silently normalize names or SKUs if that could change meaning.
- Reconcile line totals to document total.
- If the original is unclear, write `требует проверки`.
