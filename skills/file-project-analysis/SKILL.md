---
name: file-project-analysis
description: >
  Analyze multiple Word/PDF/Excel/image files or a large ongoing project as one coherent evidence set.
  Use when the user wants synthesis, contradiction detection, continuation across files, extraction
  of project facts, consistency checks, or new artifacts that must reuse prior project information.
metadata:
  version: "1.0"
  capabilities:
    - file-analysis
    - document-analysis
    - project-analysis
    - consistency-check
    - contradiction-detection
    - fact-extraction
    - project-continuation
    - artifact-preparation
  triggers:
    - файл
    - файлы
    - документ
    - документы
    - PDF
    - Excel
    - Word
    - фото
    - скан
    - проект
    - по файлам
    - из файлов
---

# File and Project Analysis

## Workflow

1. Inspect the relevant supplied files before answering.
2. Build a working project map:
   - documents;
   - facts;
   - dates;
   - people/organizations;
   - amounts;
   - technical parameters;
   - decisions and unresolved items.
3. Detect contradictions and missing information.
4. Reuse established facts consistently in subsequent outputs.
5. Do not ask the user to repeat information already present in accessible project materials.
6. For large PDFs, use structure/contents and contiguous relevant sections rather than disconnected snippets.
7. For tables, reconcile text and numeric data.
8. Before creating a new project artifact, check it against source materials and earlier project outputs.

If sources conflict, surface the conflict and apply the most authoritative/newest user-provided information
when a clear precedence exists.
