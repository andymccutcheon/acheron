# Seed playbook — jumpstarting a corpus

Goal: turn a folder of existing files into a corpus that is indexed, linked, and reviewable — without destroying or rewriting what is already there. Work the phases in order; each one leaves the corpus in a valid state.

## Phase 0 — Recon

1. Locate the source folder or folders. Use one Basic Memory project per coherent corpus; personal notes and work notes should not mix. Two projects are fine.
2. Run the inventory:

   ```sh
   python3 scripts/corpus_scan.py inventory <path>
   ```

   It reports file counts by extension, markdown coverage, frontmatter presence, duplicate titles, and the largest files.
3. Agree scope with the user in one short message:
   - **Import as-is** — markdown notes, journals, docs already in text.
   - **Convert** — text exports (plain text, chat logs, CSV-ish files) flattened into markdown; keep conversion mechanical and lossless-ish.
   - **Skip for now** — PDFs, images, office binaries, anything needing an extraction pipeline. Say what is skipped rather than ignoring it.
4. Pick the project name — short, lowercase, stable. It becomes the permalink prefix.

## Phase 1 — Import

1. Prefer working **in place** (register the existing folder). Copy only when the user wants the corpus decoupled from the source; never maintain both — one canonical location.
2. Register the folder — both routes index files already present:
   - MCP: `create_memory_project(name, path)`
   - CLI: `bm project add <name> <path>`

   When possible, put the files in place before registering.
3. Catch up and confirm. If files arrived after registration, or a `context_search` for two known strings returns nothing, run `bm project index <name>` and re-check. Verified behavior: a freshly registered project did not pick up post-registration files on its own, while after one index pass, later file drops were watched live within about 30 seconds. `bm project index` rebuilds search and embeddings and is safe to rerun.
4. Do not bulk-edit during import. Import first, enrich second — a failed enrichment then leaves a working corpus, not a broken one.

## Phase 2 — Enrich in batches

Process **10–20 notes per batch** and finish a batch completely (links verified) before starting the next.

For each batch:

1. **Read.** Batch reads keep context small.
2. **Entity pass.** Collect recurring people, projects, and concepts. Create entity notes only for entities referenced by two or more notes, or clearly central. Each new note: short, typed, `needs_review: true`.
3. **Link pass.** In each note, link the first mention of every entity that now has a note, plus any existing note that clearly relates. Verify each target (`read_note`, or the scan). Add missing `tags` and `source: import <path>`.
4. **Hub pass, optional.** When a cluster of roughly five or more notes shares a theme, create one `map` note listing them, and link it from the cluster's most central note.
5. **Dedupe pass.** If two notes cover the same thing, do not delete. Write a one-line merge proposal and list it for the user; merge only on confirmation.
6. **Checkpoint.** Append the batch to the run log note: files processed, notes created, links added, proposals open.

Rules that keep this safe and boring: additive edits only (frontmatter, links, hub notes); no prose rewrites; every auto-created note flagged; every batch checkpointed.

## Phase 3 — Verify and report

1. `python3 scripts/corpus_scan.py links <path>` — expect zero broken links caused by your edits; pre-existing broken links are reported, not fixed silently.
2. Spot-check three to five real questions with `context_search`. The seed worked when ordinary questions surface the right notes.
3. Report to the user in ten lines or fewer:
   - files imported and skipped, with reasons
   - notes created, links added, items flagged `needs_review`
   - duplicate proposals outstanding
   - the run log's path
4. Schedule nothing automatically. Offer the Wrap procedure for the next working session instead.

## Reruns

Seeding is idempotent by design. On a rerun, start from the run log: skip batches already checkpointed, and re-run the scan passes over anything new. New files land in the same loop — inventory, batch, verify.
