---
title: Decision - Drop the native mobile app
type: decision
tags:
- tidepool
- decision
- mobile
permalink: tidepool/decisions/decision-drop-the-native-mobile-app
---

# Decision - Drop the native mobile app

Status: accepted, August 2025.

## Context

The two-person team maintained iOS and Android clients plus a relay service. Sync bugs on
mobile consumed about half of each release cycle, and the relay added a server dependency
the project did not want (see [[Decision - Local-first, no cloud sync]]).

## Options considered

1. Keep both clients and hire: not viable for a volunteer team.
2. Keep one platform: still owned a relay and store review cycles.
3. Retire both and invest in the desktop engine: chosen.

## Decision

Retire the native apps; keep a read-only web gallery for sharing. Direct users to the
desktop import flow.

## Consequences

- Mobile sync reliability issues end; community reaction was mixed.
- The relay service was shut down in September 2025.