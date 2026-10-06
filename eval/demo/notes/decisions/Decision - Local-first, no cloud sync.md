---
title: Decision - Local-first, no cloud sync
type: decision
tags:
- tidepool
- decision
- privacy
permalink: tidepool/decisions/decision-local-first-no-cloud-sync
---

# Decision - Local-first, no cloud sync

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