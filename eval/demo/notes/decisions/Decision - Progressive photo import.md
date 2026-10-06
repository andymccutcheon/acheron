---
title: Decision - Progressive photo import
type: decision
tags:
- tidepool
- decision
- storage
permalink: tidepool/decisions/decision-progressive-photo-import
---

# Decision - Progressive photo import

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