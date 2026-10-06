---
title: Decision - CRDT conflict resolution
type: decision
tags:
- tidepool
- decision
- sync
- crdt
permalink: tidepool/decisions/decision-crdt-conflict-resolution
---

# Decision - CRDT conflict resolution

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