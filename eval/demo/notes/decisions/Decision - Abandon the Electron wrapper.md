---
title: Decision - Abandon the Electron wrapper
type: decision
tags:
- tidepool
- decision
- desktop
permalink: tidepool/decisions/decision-abandon-the-electron-wrapper
---

# Decision - Abandon the Electron wrapper

Status: accepted, March 2026.

## Context

The desktop shell wrapped the web UI in Electron. Bundle size, native module mismatches,
and predictable security review noise kept costing release time.

## Decision

Remove the Electron shell. Ship the local web UI as the primary desktop experience;
revisit a native shell only if a concrete use case appears.

## Alternatives

- Tauri: smaller, but a second toolchain to maintain for a two-person team.
- Keep Electron: rejected on maintenance cost.

## Consequences

- The installer shrinks; the auto-update path is temporarily manual.
- Users who expected a dock icon get a documented browser-based flow.