---
title: Sync Engine
type: concept
tags:
- tidepool
- sync
- architecture
permalink: tidepool/concepts/sync-engine
---

# Sync Engine

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