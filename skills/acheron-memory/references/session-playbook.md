# Session playbook — remember and wrap

Two procedures turn a working session into durable, linked knowledge. Remember is the small one and runs mid-session; Wrap is the closing consolidation.

## Remember — mid-session capture

**Triggers:**
- an explicit ask ("remember this", "save that", "note that")
- a decision lands, with its reason
- a durable fact about a person, project, or preference
- a lesson or pattern worth reusing

**Not triggers:** task state ("the tests are running"), transient errors, content that belongs in code comments, secrets.

**Write path:**

1. **Classify** by type (see `conventions.md`): decision, person, project, concept, source, note.
2. **Search two or three variants** — different phrasings, entity names, synonyms. A near match means edit that note, not create a sibling.
3. **Choose the smallest change:** append an observation to an existing note, then update a hub, then — only if neither fits — create one new note.
4. **Draft** to convention: title, `type`, `tags`, `source: session <date>`, links to existing entities (each verified), `needs_review: true` when the capture is the agent's idea rather than the user's.
5. **Write** (`write_note`, or a `.md` file in the corpus) and confirm in one line: title, where it went, what it links to.

**Caps:** at most five new notes per session. More than that is a signal to run Wrap and consolidate rather than keep writing.

## Wrap — end-of-session consolidation

Run when asked to wrap, save the session, or consolidate — or at the close of a working session in a corpus-enabled project.

1. **Collect candidates.** Scan the session for decisions (with reasons), entities touched, lessons, open threads, preferences stated. Skip trivia, task state, secrets, and anything Remember already captured.
2. **Dedupe each candidate.** For every one, search the corpus. An existing note means plan an edit; otherwise plan a creation. Prefer editing hubs over adding pages.
3. **Write the session note.** One note, date-titled (`YYYY-MM-DD — topic`), typed `session`:
   - what was worked on (two or three lines)
   - decisions made, linking their decision notes
   - what was learned (bullets)
   - what is open (bullets, no promises)
   Link out to every entity the session touched; link in from anything that tracks state (project or map notes) back to the session.
4. **Update hubs.** Add the session note and any new decisions to the relevant project or map notes so the corpus stays navigable from the top.
5. **Propose, do not bulk-approve.** List new entity notes and `needs_review` items in the wrap report. Never clear a review flag on the user's behalf.
6. **Report in under ten lines:** session note path, notes created or edited, hubs updated, proposals outstanding.

## Noise control

The corpus stays useful only if writes stay scarce.

- If in doubt, do not write. A missing note is cheaper than a duplicate.
- One session produces one session note. Three genuinely separate topics are three notes or one note with three sections — never six pages.
- Entities are created on second use, not first mention.
- When asked for a consolidation pass: merge duplicates flagged `needs_review`, promote session lessons into `concept` notes, and let stale project notes point at what superseded them.
- Keep the graph honest: every link resolves, and every note is reachable from at least one hub or session.
