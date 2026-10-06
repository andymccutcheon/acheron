---
title: Release checklist
type: guide
tags:
- tidepool
- process
permalink: tidepool/guides/release-checklist
---

# Release checklist

Every release follows these steps.

## Before tagging

- [ ] Tests green, including sync convergence tests.
- [ ] Storage migrations exercised against a copy of a large library.
- [ ] Import hash check runs on a fixture
  (learned from [[2026-02 Duplicate photos after 0.4.2]]).
- [ ] Changelog drafted from merged pull requests.

## After tagging

- [ ] Smoke-test import, sync, and thumbnail regeneration.
- [ ] Update the roadmap when a theme ships (see [[Roadmap 2026 H1]]).

Owners: Jonas (CI), Maya (engine), Priya (communications).