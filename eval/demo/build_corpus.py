"""Generate the synthetic demo corpus for the retrieval benchmark.

The corpus is a fictional project knowledge base ("Tidepool", a local-first photo
sync tool). Its structure mirrors a mature personal knowledge base: hub pages
(concepts, people, roadmap) accumulate cross-references, while decision and
incident notes answer specific questions. No personal data is used or derived.

Run from the repo root:

    uv run python eval/demo/build_corpus.py

Writes one markdown file per note under eval/demo/notes/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_OUT = HERE / "notes"

NOTES: list[dict] = [
    {
        "path": "concepts/Sync Engine.md",
        "title": "Sync Engine",
        "type": "concept",
        "tags": ["tidepool", "sync", "architecture"],
        "body": """
The sync engine moves a photo library between a user's devices without a server. Every
device keeps a full local index; changes propagate as operation logs over the local network
or through a user-provided shared folder.

## How it works

- Each device runs a sync agent that watches the library directory for changes.
- Operations are exchanged as append-only logs and applied through the conflict resolver
  (see [[Conflict Resolution]]).
- Sync state lives in the same SQLite database as the library index (see [[Storage Layer]]).
- Mobile clients used a different relay transport and were sunset in August 2025
  (see [[Decision - Drop the native mobile app]]).

## Failure modes

- A retry storm against a rate-limited relay caused the November 2025 incident
  (see [[2025-11 Sync storm]]).
- Duplicate photo imports after v0.4.2 came from the dedup hash, not the engine
  (see [[2026-02 Duplicate photos after 0.4.2]]).

## Relations

- relates_to [[Conflict Resolution]]
- relates_to [[Storage Layer]]
- relates_to [[Maya Chen]]
- relates_to [[Jonas Weber]]
""",
    },
    {
        "path": "concepts/Conflict Resolution.md",
        "title": "Conflict Resolution",
        "type": "concept",
        "tags": ["tidepool", "sync", "crdt"],
        "body": """
Conflicts happen when two devices edit the same library record before syncing. Tidepool
resolves them deterministically so every device converges on the same state.

## Approach

- Field-level last-writer-wins with hybrid logical clocks for metadata.
- Photo membership and album edits use CRDT sets, adopted in January 2026
  (see [[Decision - CRDT conflict resolution]]).
- Deletions are tombstones, garbage-collected after 30 days without opposing edits.

## Why not simpler schemes

- Server-authoritative resolution is off the table: Tidepool has no server
  (see [[Decision - Local-first, no cloud sync]]).
- Timestamp-only ordering broke across devices with skewed clocks.

## Relations

- relates_to [[Sync Engine]]
- relates_to [[Decision - CRDT conflict resolution]]
- relates_to [[Maya Chen]]
""",
    },
    {
        "path": "concepts/Storage Layer.md",
        "title": "Storage Layer",
        "type": "concept",
        "tags": ["tidepool", "storage", "sqlite"],
        "body": """
Each library is a single directory plus one SQLite database. The exact layout is specified
in [[Photo library format]].

## Design

- SQLite holds the index, metadata, and sync state (see [[Decision - SQLite over Postgres]]).
- Original files are never modified; thumbnails live in a regenerable cache.
- Content hashes drive deduplication during import.
- Import is chunked to keep memory flat on large libraries
  (see [[Decision - Progressive photo import]]).

## Known issues

- The thumbnail cache was corrupted by a cache-invalidation bug in April 2026
  (see [[2026-04 Corrupted thumbnail cache]]).
- Jonas Weber owns this area.

## Relations

- relates_to [[Jonas Weber]]
- relates_to [[Decision - SQLite over Postgres]]
""",
    },
    {
        "path": "concepts/Mobile App.md",
        "title": "Mobile App",
        "type": "concept",
        "tags": ["tidepool", "product", "mobile"],
        "body": """
Tidepool shipped iOS and Android clients from 2023 to 2025. They were retired in
August 2025.

## History

- The mobile clients synced through a relay service rather than peer-to-peer.
- Maintenance consumed roughly half of the two-person team's release time.
- The drop decision and its consequences are recorded in
  [[Decision - Drop the native mobile app]].
- Priya Nair owned the mobile surface and the community fallout.

## What replaced it

- A read-only web gallery for sharing, plus a progressive web app experiment that never
  shipped.
- Mobile sync reliability complaints are collected in [[2025-11 Sync storm]].

## Relations

- relates_to [[Decision - Drop the native mobile app]]
- relates_to [[Priya Nair]]
""",
    },
    {
        "path": "concepts/Roadmap 2026 H1.md",
        "title": "Roadmap 2026 H1",
        "type": "concept",
        "tags": ["tidepool", "roadmap"],
        "body": """
Themes for the first half of 2026, agreed in the January planning meeting
(see [[2026-01-12 Weekly]]).

## Now

- CRDT-based conflict resolution rollout across desktop clients
  (see [[Decision - CRDT conflict resolution]]).
- Streamed import for very large libraries (see [[Decision - Progressive photo import]]).

## Next

- Non-destructive photo editing history.
- Plugin API for exporters.

## Later / watching

- Electron wrapper removal follow-ups (see [[Decision - Abandon the Electron wrapper]]).
- Revisiting a web-only companion.
""",
    },
    {
        "path": "people/Maya Chen.md",
        "title": "Maya Chen",
        "type": "person",
        "tags": ["tidepool", "team"],
        "body": """
Maya Chen is a co-maintainer of Tidepool. She works on the sync engine and conflict
resolution, and wrote most of the CRDT design.

## Contributions

- [architecture] Designed the operation-log sync protocol.
- [decision] Authored the CRDT conflict resolution decision (January 2026).
- [decision] Recommended dropping the native mobile app (August 2025).
- [incident] Led the response to the duplicate photo reports in February 2026.
- [review] Maintains the release checklist.

## Relations

- relates_to [[Sync Engine]]
- relates_to [[Conflict Resolution]]
- relates_to [[Decision - Drop the native mobile app]]
""",
    },
    {
        "path": "people/Jonas Weber.md",
        "title": "Jonas Weber",
        "type": "person",
        "tags": ["tidepool", "team"],
        "body": """
Jonas Weber is a co-maintainer of Tidepool. He owns storage, the SQLite schema, and the
import pipeline.

## Contributions

- [build] Migrated the library index from flat files to SQLite (June 2025).
- [storage] Wrote the photo library format specification.
- [incident] Postmortem owner for the November 2025 sync storm.
- [incident] Fixed the corrupted thumbnail cache in April 2026.
- [infra] Maintains CI and the release checklist.

## Relations

- relates_to [[Storage Layer]]
- relates_to [[Decision - SQLite over Postgres]]
""",
    },
    {
        "path": "people/Priya Nair.md",
        "title": "Priya Nair",
        "type": "person",
        "tags": ["tidepool", "team"],
        "body": """
Priya Nair leads product and community for Tidepool. She owned the mobile apps until
their retirement and writes the weekly notes.

## Focus

- [product] Mobile app owner, 2023-2025; ran the sunset communications.
- [incident] Fronted the duplicate photos response after v0.4.2.
- [community] Runs beta testing and the roadmap process.
- [process] Co-maintains the release checklist.

## Relations

- relates_to [[Mobile App]]
- relates_to [[Roadmap 2026 H1]]
""",
    },
    {
        "path": "decisions/Decision - Drop the native mobile app.md",
        "title": "Decision - Drop the native mobile app",
        "type": "decision",
        "tags": ["tidepool", "decision", "mobile"],
        "body": """
Status: accepted, August 2025.

## Context

The two-person team maintained iOS and Android clients plus a relay service. Sync bugs on
mobile consumed about half of each release cycle, and the relay added a server dependency
the project did not want (see [[Decision - Local-first, no cloud sync]]).

## Options considered

1. Keep both clients and hire: not viable for a volunteer team.
2. Keep one platform: still owned a relay and store review cycles.
3. Retire both and invest in the desktop engine: chosen.

## Decision

Retire the native apps; keep a read-only web gallery for sharing. Direct users to the
desktop import flow.

## Consequences

- Mobile sync reliability issues end; community reaction was mixed.
- The relay service was shut down in September 2025.
""",
    },
    {
        "path": "decisions/Decision - SQLite over Postgres.md",
        "title": "Decision - SQLite over Postgres",
        "type": "decision",
        "tags": ["tidepool", "decision", "storage"],
        "body": """
Status: accepted, June 2025.

## Context

The library index outgrew flat JSON files. Candidates were SQLite (embedded) and Postgres
(server).

## Decision

Use SQLite, one database per library.

## Rationale

- Tidepool is single-user and local-first (see [[Decision - Local-first, no cloud sync]]);
  a server dependency contradicts the premise.
- Backups are a file copy; no daemon, no ports, no credentials.
- Full-text and vector search both work in-process, which keeps the sync engine simple.

## Consequences

- Concurrent writers rely on WAL mode; multi-process access needs care.
- Migrations run at startup and must stay backward compatible for one release.
""",
    },
    {
        "path": "decisions/Decision - CRDT conflict resolution.md",
        "title": "Decision - CRDT conflict resolution",
        "type": "decision",
        "tags": ["tidepool", "decision", "sync", "crdt"],
        "body": """
Status: accepted, January 2026.

## Context

Two devices editing the same album before syncing produced lost edits. Timestamp ordering
failed across devices with skewed clocks; a server arbiter is impossible
(see [[Decision - Local-first, no cloud sync]]).

## Decision

Use CRDTs for collaborative collections:

- OR-Set for album membership and tags.
- Hybrid logical clocks for scalar fields, last-writer-wins per field.
- Tombstones for deletions, garbage-collected after 30 days.

## Alternatives rejected

- Server arbitration: no server.
- Manual conflict prompts: users found them confusing in beta.

## Consequences

- Every client must upgrade together for full convergence.
- Implemented in the sync engine behind a version flag (see [[Sync Engine]]).
""",
    },
    {
        "path": "decisions/Decision - Abandon the Electron wrapper.md",
        "title": "Decision - Abandon the Electron wrapper",
        "type": "decision",
        "tags": ["tidepool", "decision", "desktop"],
        "body": """
Status: accepted, March 2026.

## Context

The desktop shell wrapped the web UI in Electron. Bundle size, native module mismatches,
and predictable security review noise kept costing release time.

## Decision

Remove the Electron shell. Ship the local web UI as the primary desktop experience;
revisit a native shell only if a concrete use case appears.

## Alternatives

- Tauri: smaller, but a second toolchain to maintain for a two-person team.
- Keep Electron: rejected on maintenance cost.

## Consequences

- The installer shrinks; the auto-update path is temporarily manual.
- Users who expected a dock icon get a documented browser-based flow.
""",
    },
    {
        "path": "decisions/Decision - Local-first, no cloud sync.md",
        "title": "Decision - Local-first, no cloud sync",
        "type": "decision",
        "tags": ["tidepool", "decision", "privacy"],
        "body": """
Status: accepted, May 2025.

## Context

Tidepool began as a personal library tool. Every design proposal that added a hosted
component also added accounts, privacy questions, and ongoing costs.

## Decision

Tidepool stores all data locally. There is no Tidepool account, no hosted sync service,
and no telemetry. Device-to-device sync (see [[Sync Engine]]) is peer-to-peer or through a
user-provided folder.

## Consequences

- Sharing requires exporting or a self-hosted read-only gallery.
- The project avoids operational costs and vendor dependencies.
- Mobile clients that relied on a relay were eventually retired
  (see [[Decision - Drop the native mobile app]]).
""",
    },
    {
        "path": "decisions/Decision - Progressive photo import.md",
        "title": "Decision - Progressive photo import",
        "type": "decision",
        "tags": ["tidepool", "decision", "storage"],
        "body": """
Status: accepted, October 2025.

## Context

Importing a 200k-photo library in one pass held the whole manifest in memory and stalled
the UI.

## Decision

Stream imports in chunks of 500 files: hash, insert, and thumbnail each chunk, then
release it. The manifest is a resumable journal (see [[Storage Layer]]).

## Consequences

- Peak memory is flat regardless of library size.
- Import can resume after a crash; partial imports are visible and repairable.
- Progress reporting is chunk-granular rather than file-granular.
""",
    },
    {
        "path": "incidents/2025-11 Sync storm.md",
        "title": "2025-11 Sync storm",
        "type": "incident",
        "tags": ["tidepool", "incident", "sync"],
        "body": """
Date: November 2025. Severity: high. Owner: Jonas Weber.

## Summary

A relay outage caused clients to retry aggressively. Retries amplified into a request
storm when devices reconnected together, and some clients spun for hours.

## Timeline

- Nov 3: relay rate limits began returning 429s.
- Nov 4: retry storm; battery drain reports from users.
- Nov 5: workaround published (disable relay sync); fix landed with exponential backoff
  and jitter.

## Root cause

Retry logic had no backoff and no cap; reconnection was synchronized across devices.

## Follow-ups

- Backoff and a retry budget shipped in v0.4.1.
- Mobile clients were retired the following year
  (see [[Decision - Drop the native mobile app]]).
""",
    },
    {
        "path": "incidents/2026-02 Duplicate photos after 0.4.2.md",
        "title": "2026-02 Duplicate photos after 0.4.2",
        "type": "incident",
        "tags": ["tidepool", "incident", "storage"],
        "body": """
Date: February 2026. Severity: medium. Owner: Maya Chen.

## Summary

After the v0.4.2 import changes, re-running an import on existing libraries duplicated
some photos. The dedup hash was computed over file metadata instead of content in one
code path.

## Impact

About 40 beta libraries affected; no data loss, but clean-up was required.

## Fix

Restored content-hash deduplication and added a repair command that merges duplicates by
hash (see [[Storage Layer]]).

## Follow-ups

- Hash computation is now covered by the release checklist.
- Priya ran user communications.
""",
    },
    {
        "path": "incidents/2026-04 Corrupted thumbnail cache.md",
        "title": "2026-04 Corrupted thumbnail cache",
        "type": "incident",
        "tags": ["tidepool", "incident", "storage"],
        "body": """
Date: April 2026. Severity: low. Owner: Jonas Weber.

## Summary

A cache-invalidation bug wrote thumbnails under stale keys after migrations, producing
mismatched images in the grid.

## Fix

Cache keys now include the schema version; the cache is regenerated on mismatch. No
original files were affected (see [[Storage Layer]]).
""",
    },
    {
        "path": "meetings/2025-08-04 Weekly.md",
        "title": "2025-08-04 Weekly",
        "type": "meeting",
        "tags": ["tidepool", "meeting"],
        "body": """
Attendees: Maya, Jonas, Priya.

## Mobile app

- Reviewed maintenance load: mobile work is about half of every release.
- Maya proposed retiring both native clients; Priya flagged community impact and offered
  a communications plan.
- Decision recorded: [[Decision - Drop the native mobile app]].
""",
    },
    {
        "path": "meetings/2026-01-12 Weekly.md",
        "title": "2026-01-12 Weekly",
        "type": "meeting",
        "tags": ["tidepool", "meeting"],
        "body": """
Attendees: Maya, Jonas, Priya.

## Conflicts

- Maya presented the CRDT proposal: OR-Set membership, hybrid clocks for scalars.
- Jonas raised migration and upgrade-order concerns; agreed to a version flag.
- Decision recorded: [[Decision - CRDT conflict resolution]].

## Roadmap

- H1 themes drafted; Priya will circulate [[Roadmap 2026 H1]].
""",
    },
    {
        "path": "meetings/2026-02-09 Weekly.md",
        "title": "2026-02-09 Weekly",
        "type": "meeting",
        "tags": ["tidepool", "meeting"],
        "body": """
Attendees: Maya, Jonas, Priya.

## Duplicate photos

- Beta reports of duplicated imports after v0.4.2
  (see [[2026-02 Duplicate photos after 0.4.2]]).
- Root cause: one import path hashed metadata, not content.
- Repair command scoped; Priya to post the user note.

## Import

- Progressive import rollout looks healthy on large libraries.
""",
    },
    {
        "path": "guides/Run Tidepool locally.md",
        "title": "Run Tidepool locally",
        "type": "guide",
        "tags": ["tidepool", "setup"],
        "body": """
Tidepool runs as a local server plus a browser UI.

## Steps

1. Install the package for your platform.
2. Run `tidepool`; it creates a library in `~/Pictures/Tidepool`
   (see [[Photo library format]]).
3. Open the printed localhost URL.
4. Import photos; large libraries stream in chunks
   (see [[Decision - Progressive photo import]]).

## Troubleshooting

- Thumbnails regenerate automatically if the cache looks wrong
  (see [[2026-04 Corrupted thumbnail cache]]).
- For sync between machines, point both devices at a shared folder.
""",
    },
    {
        "path": "guides/Release checklist.md",
        "title": "Release checklist",
        "type": "guide",
        "tags": ["tidepool", "process"],
        "body": """
Every release follows these steps.

## Before tagging

- [ ] Tests green, including sync convergence tests.
- [ ] Storage migrations exercised against a copy of a large library.
- [ ] Import hash check runs on a fixture
  (learned from [[2026-02 Duplicate photos after 0.4.2]]).
- [ ] Changelog drafted from merged pull requests.

## After tagging

- [ ] Smoke-test import, sync, and thumbnail regeneration.
- [ ] Update the roadmap when a theme ships (see [[Roadmap 2026 H1]]).

Owners: Jonas (CI), Maya (engine), Priya (communications).
""",
    },
    {
        "path": "guides/Photo library format.md",
        "title": "Photo library format",
        "type": "guide",
        "tags": ["tidepool", "storage", "spec"],
        "body": """
A Tidepool library is one directory:

    library/
      tidepool.db        # index, metadata, sync state (SQLite)
      originals/         # content-addressed photo files
      cache/             # regenerable thumbnails

## Rules

- Original files are immutable; file names are content hashes.
- The content hash covers file bytes plus capture metadata, not the file path.
- `cache/` may be deleted at any time; it rebuilds from originals.
- Album and tag structure lives in the database, never in the file tree.

See [[Decision - SQLite over Postgres]] and [[Decision - Progressive photo import]].
""",
    },
]


def render(note: dict) -> str:
    lines = ["---", f'title: "{note["title"]}"', f'type: {note["type"]}']
    if note.get("tags"):
        lines.append("tags: [" + ", ".join(note["tags"]) + "]")
    lines.append("---")
    return "\n".join(lines) + f'\n\n# {note["title"]}\n\n' + note["body"].strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    for note in NOTES:
        target = args.out / note["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(note), encoding="utf-8")
    print(f"wrote {len(NOTES)} notes to {args.out}")


if __name__ == "__main__":
    main()
