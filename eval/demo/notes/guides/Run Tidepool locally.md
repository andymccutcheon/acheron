---
title: Run Tidepool locally
type: guide
tags:
- tidepool
- setup
permalink: tidepool/guides/run-tidepool-locally
---

# Run Tidepool locally

Tidepool runs as a local server plus a browser UI.

## Steps

1. Install the package for your platform.
2. Run `tidepool`; it creates a library in `~/Pictures/Tidepool`
   (see [[Photo library format]]).
3. Open the printed localhost URL.
4. Import photos; large libraries stream in chunks
   (see [[Decision - Progressive photo import]]).

## Troubleshooting

- Thumbnails regenerate automatically if the cache looks wrong
  (see [[2026-04 Corrupted thumbnail cache]]).
- For sync between machines, point both devices at a shared folder.