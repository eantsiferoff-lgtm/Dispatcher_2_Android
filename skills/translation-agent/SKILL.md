---
name: translation-agent
description: >
  Provide multilingual translation for text and supported document, image or scan
  inputs. Detect the source language when it is not specified, translate into the
  requested target language, and use the configured default output language when
  no target language is provided. Preserve meaning, structure, numbers, dates,
  units, identifiers and important terminology. Do not invent missing content.
metadata:
  version: "1.0"
  default_output_language: "ru"
  execution_mode: "ai"
  backend: "openai"
  capabilities:
    - translation
    - multilingual-translation
    - language-detection
    - document-translation
    - image-translation
    - scan-translation
  triggers:
  - переведи
  - перевод
  - перевести
  - translation
  - translate
  - язык
  - определить язык
  - целевой язык
  - target language
---

# Translation Agent

## Purpose

Provide a universal multilingual language layer that can be composed with other
Dispatcher Skills.

## Input

The Skill may receive:

- text;
- extracted text from a document;
- text recognized from a photo or scan;
- other language content supplied by a compatible input processor;
- speech input when a compatible speech-recognition capability is available.

The source language should default to automatic detection.

## Output

Return the translated content in the requested target language.

If the user does not specify a target language, use the configured
`default_output_language`.

An explicitly requested target language has priority over the default.

## Rules

1. Preserve the meaning of the source.
2. Preserve document structure when possible.
3. Preserve numbers, dates, units, identifiers and proper names unless translation
   is explicitly requested for them.
4. Preserve important domain terminology.
5. Do not invent text that is absent from the input.
6. If the source cannot be reliably recognized, report the limitation instead of
   fabricating content.
7. The Skill must remain independent of any particular language pair.
8. The Skill can be composed with document, project-analysis, 1C and other Skills.

## Examples

Japanese document -> Translation Agent -> Russian text

English text -> Translation Agent -> Chinese text

Photo/scan with foreign text -> compatible recognition -> Translation Agent
-> requested target language
