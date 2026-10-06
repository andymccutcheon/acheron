---
title: Decision - SQLite over Postgres
type: decision
tags:
- tidepool
- decision
- storage
permalink: tidepool/decisions/decision-sqlite-over-postgres
---

# Decision - SQLite over Postgres

Status: accepted, June 2025.

## Context

The library index outgrew flat JSON files. Candidates were SQLite (embedded) and Postgres
(server).

## Decision

Use SQLite, one database per library.

## Rationale

- Tidepool is single-user and local-first (see [[Decision - Local-first, no cloud sync]]);
  a server dependency contradicts the premise.
- Backups are a file copy; no daemon, no ports, no credentials.
- Full-text and vector search both work in-process, which keeps the sync engine simple.

## Consequences

- Concurrent writers rely on WAL mode; multi-process access needs care.
- Migrations run at startup and must stay backward compatible for one release.