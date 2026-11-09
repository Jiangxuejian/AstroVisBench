# AstroVisBench independent evaluations

## TL;DR

- How well can AI analyse astronomical data and make scientifically correct plots?
- **Lite-72** tests 72 workflows: 72 analysis tasks and 72 visualization tasks, selected from the full 432-workflow benchmark.
- [See the results](docs/index.md), [get the data (~9.9 GB)](docs/lite72-data-release.md), or [ask your agent to run the benchmark](LITE72_AGENT_PROMPT.md).

This fork adds independent evaluations and a lower-cost subset to
[AstroVisBench](https://github.com/NSF-Simons-CosmicAI-Institute/AstroVisBench).
It follows the original generation → execution → judging workflow and is not
the official leaderboard.

## Results

![AstroVisBench model comparison](docs/assets/leaderboard-portrait.svg)

**CorrectV** is the percentage of all visualization tasks judged free of errors.
A program that runs successfully is not necessarily scientifically correct.

The figure includes full-benchmark and Lite results. Tool-assisted agents and
models without tools are different experiments; the display is not a controlled
ranking across tracks. Qwen's recovery run includes extra attempts.
See the [full table, metric definitions and limitations](docs/index.md).

## Run Lite-72

1. [Download and prepare the data](docs/lite72-data-release.md).
2. Give your coordinating agent the [benchmark prompt](LITE72_AGENT_PROMPT.md).
3. Send the compressed generation/execution results to the maintainer for common judging. You do not need judge credentials.

Data downloads: [GitHub](https://github.com/Jiangxuejian/AstroVisBench/releases/tag/lite72-data-20261109) · [GitLab](https://gitlab.zhejianglab.com/jiangxuejian/astrovisbench-lite/-/tree/data/lite72-20261109-curated-v1/lite72-data/20261109-curated-v1).

Lite-72 spans spectroscopy, photometry, imaging, time series, cosmology and
simulation/modeling, using provisional notebook-family labels. It is a fixed
sample, not a replacement for the full benchmark.

Some tasks still need online services. Keep reference solutions hidden from
the evaluated model. The shared data include a declared compact NIRISS variant;
record the input version when comparing new runs.

[Detailed methods and run records](docs/lite72-v2-historical.md) ·
[GitLab mirror](https://gitlab.zhejianglab.com/jiangxuejian/astrovisbench-lite/) ·
[Original paper](https://arxiv.org/abs/2505.20538) ·
[Official leaderboard](https://astrovisbench.github.io/)
