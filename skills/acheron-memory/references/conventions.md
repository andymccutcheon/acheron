# Conventions — note shapes for an Acheron corpus

The engine reads markdown; these conventions are what make a corpus connected and filterable. They are defaults, not law: check a few existing notes first, and follow the corpus's own habits when it has them.

## Frontmatter

Every new note should carry at least:

```yaml
---
title: Decision — drop the nightly re-index
type: decision
tags: [infra, search]
source: session 2026-10-05
created: 2026-10-05
---
```

| field | purpose |
|---|---|
| `title` | display name; also the wikilink target |
| `type` | note shape (table below) |
| `tags` | lowercase; reuse existing tags before inventing new ones |
| `source` | provenance — `session <date>`, `import <path>`, or `manual` |
| `aliases` | alternate names (handles, former titles) so the note stays findable |
| `needs_review` | `true` on auto-captured notes until a human or wrap pass confirms |
| `supersedes` | wikilink to the decision or note this one replaces |

## Note types

| type | use | shape |
|---|---|---|
| `note` | everything else | one idea; a few lines or bullets |
| `person` | someone the user works with or follows | who they are, why relevant, links to projects and sources |
| `project` | an ongoing effort | what it is, current status, links to decisions and people |
| `decision` | a choice with reasons | decision, context, alternatives, why, supersedes / superseded-by |
| `concept` | a durable idea or topic | definition in the user's terms, links to sources |
| `source` | an article, bookmark, or document | citation or URL, takeaway, links to concepts |
| `session` | one working session | date-titled; what happened, decided, learned; links out |
| `map` | a hub or index for a topic | a curated list of links — the corpus's table of contents |

Create a type only when it recurs. Two notes of an unclear type are just notes.

## Naming and layout

- File name equals title (`Title Case.md`). No dates in titles except session notes.
- Optional folders keep a growing corpus tidy: `people/`, `projects/`, `decisions/`, `sessions/`, `concepts/`, `sources/`. Do not reorganize an existing corpus's folders without being asked.
- People who use handles: `Name (@handle).md`, with the handle in `aliases`.

## Linking

- Link as `[[Title]]` or `[[Title|shown text]]`; never link a slug or path.
- **Verify every target before writing the link.** A `[[link]]` to nothing is a promise the corpus cannot keep.
- Link purposefully: the first mention of a known entity in a note, not every mention.
- Prefer one hub note (`map`) over repeating the same list across many notes.
- Backlinks come free — the engine derives them from one-directional links; do not link both ways.
- Renames: add the old title to `aliases` so search still finds the note, and re-point the links that used the old title (`corpus_scan.py links` finds them).

## What not to write

- Transcripts, scratchpads, todo lists, transient task state — those belong in the working context, not the corpus.
- Duplicates: search first; a near-match means edit, not create.
- Secrets, credentials, or private third-party data, unless the corpus is explicitly for that.
- Speculation presented as fact. Mark uncertainty ("claims", "unclear whether").
