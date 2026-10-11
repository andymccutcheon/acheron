# Architect changes applied

| Item | Status | Section edited | Before | After |
|---:|---|---|---|---|
| 1 | Applied | Bottom line; H1 “What it is”; top recommendation 1 | H1 was described as borrowing Helix Foundry's call/time/token budget pattern. | The report now says the search cap is generic min/max validation; only the bounded numeric-budget shape is analogous to Helix Foundry, which does not cap search windows. |
| 2 | Applied | H1 “Why it matters” | “Any MCP caller” could request an arbitrarily large set, without deployment context. | The report now identifies local owner-controlled agent sessions, corpus size as the practical ceiling, and the oversized request as a local footgun that remains Do now. |
| 3 | Applied* | H1 “How to adopt” | Generic server/config validation and tests, with no treatment of zero/negative values, title length, or query length. | The report now specifies clamping both parameters, applying the clamp to both paths, bounding title/query text, retaining a hard ceiling over any environment override, and not waiting for a new replay. |
| 4 | Applied | H1 effort line; ranked row 1 | Source was Helix Foundry; effort line told implementers to use the replay to set the cap. | Source is “Generic bound, shaped like Helix Foundry's numeric budgets”; S / Low / Do now is unchanged, with the wider-recall risk handled by an override inside the hard ceiling. |
| 5 | Applied | A1 “What it is”; ranked row 2 | The server and skill rule were jointly attributed to Agent Memory Repo and Helix Foundry (“Both” in the table). | Agent Memory Repo is credited only for the skill rule; the Decisions change is labeled generic prompt hygiene, with Helix cited only as an analogous tabular-data boundary. |
| 6 | Applied | Top recommendation 2; A1 “Why it matters”; ranked row 2 value | The report called both halves an avoidable prompt-injection path. | It now distinguishes score bias in the score-only Decisions model from the higher-impact risk that a consuming agent treats memory as orders; successful bias is outside fail-open. |
| 7 | Applied | A1 “How to adopt” | The report proposed a narrow read-time guardrail without explaining why it must remain narrow. | It now rejects pasting the broader Agent Memory Repo sentence because Acheron decision notes contain recorded choices agents should apply. |
| 8 | Applied | H2 “Why it matters” | The seam was said to make Acheron's portability claim true. | The report now says model portability already exists on OpenRouter; the seam is triggered by a second wire protocol, not a correction of a false claim. |
| 9 | Applied | Ranked row 11 | Optional inline provenance/path links had effort M. | Effort is S; priority remains Skip. |
| 10 | Applied | Open questions, upstream revision | The report noted `external_id` and `updated_at` were not stable revisions. | It now states `external_id` is a hosted deep-link identifier, neither field should be passed through as a revision stand-in, and local agents open notes by path. |

## Declined

- **Item 3 clause:** Declined “`README.md:104-116` already supports defaults of 10 candidates and 5 results.” Those lines report top-1/top-3 outcomes, not support for a five-result default. The report instead cites the 10/5 defaults at `src/acheron/config.py:36-37` and `README.md:154-155`, and accurately says the benchmark itself uses 10 candidates at `eval/benchmark.py:124-126`.

\* Item 3's supported implementation changes were applied; only the unsupported benchmark/default clause was declined.
