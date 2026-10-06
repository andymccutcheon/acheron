---
title: 2025-11 Sync storm
type: incident
tags:
- tidepool
- incident
- sync
permalink: tidepool/incidents/2025-11-sync-storm
---

# 2025-11 Sync storm

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