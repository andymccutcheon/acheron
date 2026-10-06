---
title: 2026-02 Duplicate photos after 0.4.2
type: incident
tags:
- tidepool
- incident
- storage
permalink: tidepool/incidents/2026-02-duplicate-photos-after-0.4.2
---

# 2026-02 Duplicate photos after 0.4.2

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