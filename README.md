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
- A separate Lite-72 T1 coding-agent evaluation for Claude Code + Kimi K3.
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
suite. Processing-only results without visualization judging are documented on
the results page rather than plotted as complete leaderboard rows.

See the [full table, metric definitions, and provenance](docs/index.md).

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
