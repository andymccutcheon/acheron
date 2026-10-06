---
title: Storage Layer
type: concept
tags:
- tidepool
- storage
- sqlite
permalink: tidepool/concepts/storage-layer
---

# Storage Layer

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