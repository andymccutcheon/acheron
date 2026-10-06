---
title: Conflict Resolution
type: concept
tags:
- tidepool
- sync
- crdt
permalink: tidepool/concepts/conflict-resolution
---

# Conflict Resolution

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