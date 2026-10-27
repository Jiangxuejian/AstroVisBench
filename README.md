# AstroVisBench independent evaluations

This fork of the
[original AstroVisBench repository](https://github.com/NSF-Simons-CosmicAI-Institute/AstroVisBench)
adds independently run model evaluations, reproducibility records, and a fixed
lower-cost benchmark subset. It does not replace the upstream benchmark or its
official leaderboard.

## What this fork adds

- An [independent results page](docs/index.md) with audited Full-432 and Lite-72
  results.
- Full-432 local evaluations for Qwen3.8-27B Q4_K_M and Kimi K3.
- Separate Lite-72 T1 coding-agent evaluations for GPT-6 + Codex and Claude Code + Kimi K3.
- A frozen, deterministic [Lite-72 subset manifest](docs/data/lite72-candidate-v1.json),
  [UID selector](scripts/select_lite72_subset.py), and
  [reproducibility guide](LITE72_RUN_GUIDE.md).
- Machine-readable provenance and leaderboard data under [docs/data](docs/data/).

Lite-72 is a complete evaluation of a fixed sampled subset—not an unfinished
Full-432 run. Standard no-tool model runs and coding-agent runs are reported as
separate tracks because their tool access and interaction protocols differ.

## Current snapshot

![AstroVisBench independent leaderboard snapshot](docs/assets/leaderboard-full.svg)

The chart combines published reference rows from the official AstroVisBench
leaderboard with clearly labelled independent results from this fork. Hatched
bars identify local evaluations, and `(lite-72 subset)` identifies the sampled
suite. New historical-v2-selection rows are execution-only: missing judge bars
are marked `n/a`, not zero. Full-432, Lite-72 v1, and the v2 task selection are
different suites, not one directly comparable ranking.

See the [full table, metric definitions, and provenance](docs/index.md).
Both [SVG](docs/assets/leaderboard-full.svg) and
[PNG](docs/assets/leaderboard-full.png) are updated together.

### Latest execution results · 27 October 2026

| T1 coding agent | Coverage | Processing no error | Visualization no error | VIscore |
|---|---:|---:|---:|---:|
| GPT-6 Astra medium + Codex | 72/72 | 66.67% | 83.33% | 0.6700 |
| Claude Code + Kimi K3 | 72/72 | 61.11% | 86.11% | 0.6162 |

These use the **Lite-72 v2 task selection with historical inputs**, combining
65 preserved baseline executions with seven supplements per agent. They are
**not official frozen-input v2 scores**. VIscore denominators are 40 and 33;
complete-72 visualization judge scores remain pending. Old v1 results are retained.
See the [selection, protocol/version caveats and checksums](docs/lite72-v2-historical.md).

**23 October 2026 correction:** Kimi K3's historical execution records were
reconciled with the repaired records used for judging. Processing success is
**48.15%**, visualization success **76.85%**, and VIscore **0.731**; judge
category percentages are unchanged. Both figure formats and the table reflect
this correction. Network/input fairness is still being investigated; these
are not controlled-rerun scores. See the [audit note](docs/execution-fairness.md).

## Reproduce the Lite-72 subset

Follow [`LITE72_RUN_GUIDE.md`](LITE72_RUN_GUIDE.md) to:

1. validate the pinned 432-task source dataset and frozen UID manifest;
2. generate the exact 72-record benchmark input;
3. run the original generation, execution, visualization-judge, and aggregation
   sequence; and
4. record the model, harness, environment, tool policy, checksums, and judge
   configuration needed for comparison.

For the original environment setup, benchmark schema, usage instructions,
citation, and license, use the
[upstream README](https://github.com/NSF-Simons-CosmicAI-Institute/AstroVisBench#readme).
The [official website](https://astrovisbench.github.io/) remains the authority
for the published AstroVisBench leaderboard.
