---
title: 2026-04 Corrupted thumbnail cache
type: incident
tags:
- tidepool
- incident
- storage
permalink: tidepool/incidents/2026-04-corrupted-thumbnail-cache
---

# 2026-04 Corrupted thumbnail cache

Date: April 2026. Severity: low. Owner: Jonas Weber.

## Summary

A cache-invalidation bug wrote thumbnails under stale keys after migrations, producing
mismatched images in the grid.

## Fix

Cache keys now include the schema version; the cache is regenerated on mismatch. No
original files were affected (see [[Storage Layer]]).