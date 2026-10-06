---
title: Photo library format
type: guide
tags:
- tidepool
- storage
- spec
permalink: tidepool/guides/photo-library-format
---

# Photo library format

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