---
name: image-editing-workflow
description: >
  Coordinate image generation and iterative image edits from user instructions, including adding
  or removing people/objects, face replacement, body-shape adjustments, background changes,
  greeting cards and text placement. Use when the user asks to create or modify an image and wants
  continuity across successive revisions.
metadata:
  version: "1.0"
---

# Image Editing Workflow

## Principles

1. Use the actual image-generation/editing capability for image requests when available.
2. For edits, use the image present in the current conversation as the target; if no usable target
   exists, ask the user to upload/identify it rather than inventing one.
3. Preserve identities, composition, perspective, lighting and shadows unless the user asks to change them.
4. Add people/objects at a natural scale and avoid obscuring important subjects.
5. For body-shape edits, maintain realistic anatomy and proportions.
6. For greeting cards, prioritize subject recognizability, legible text and balanced decoration.
7. Treat the latest edited image as the new working base when the user asks for another revision,
   unless the user explicitly refers back to an earlier image.
8. Change only what the user requested where practical.
