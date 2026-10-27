# GitHub Pages content draft

`index.md` is the one-page public content for the Jiangxuejian fork. Working title:
**AstroVisBench — Independent Model Evaluations**. The files are published in the
repository's `main` branch; GitHub Pages configuration, a custom domain, and a
separate public raw-artifact archive remain optional and are not assumed here.

The page uses ordinary Markdown and relative download links. It can be placed in a
GitHub Pages/Jekyll site when the public repository is chosen. The grouped bar chart
contains the published reference rows, the audited QWEN and Kimi K3 Full-432
runs, the explicitly labelled v1 Claude Code + K3 row, and execution-only GPT-6
and Claude + K3 historical-v2-selection rows. Keep
the Full and Lite suites and the T0/T1 tracks distinct when interpreting it.

## Content decisions

- Attribute the upstream benchmark prominently and identify this as independent work.
- Publish metrics only after their own coverage is audited. New historical-v2-selection agent rows have 72 executions but pending judge metrics; mark the latter null/n/a. Do not call them frozen-input v2 results.
- Keep Lite-72 explicitly provisional, including its imperfect notebook-family labels.
- Mark Smoke and the portable public runner as unfinished; identify the Claude Code + K3 agent comparison as a separate T1 track.
- Describe the actual three-trial aggregation and eligible VIscore denominators.
- Distinguish requested judge identity from a verified backend snapshot.
- Avoid placeholder repository URLs, invented commands, or promises of exact cost savings.
- Keep host filesystem paths, credentials, raw prompts, and large artifacts out of the
  downloadable page data. Candidate UIDs and notebook names are sufficient here.

## Updating the content

The existing audited sources are `results/lite72-candidate-v1/`, the QWEN and Kimi K3
run manifests/provenance and the Claude Code
K3 Lite audit. Generate the
small public downloads using:

```bash
python3 scripts/prepare_pages_data.py
.astrovis-data/venvs/original-bench/bin/python scripts/build_leaderboard_assets.py
```

The first script exports the QWEN evidence; it does not rerun generation, execution, or
judging. Kimi K3 and Claude Code + K3 compact records are retained as
`docs/data/k3-audit.json` and
`docs/data/claude-k3-lite-audit.json`. The second script reads
`docs/data/leaderboard.json` and regenerates the matching SVG/PNG figure, rendering
missing metrics, including pending visualization judgments, as `n/a` rather than zero.
The prose and table cells remain deliberately easy to edit as one Markdown page. When
new scores are added, update the text, source selection, and checks together.

For the 27 October historical-selection agent scores, first run:

```bash
python scripts/prepare_v2_selection_agent_scores.py --artifacts-root /path/to/operator-project
python scripts/build_leaderboard_assets.py
```

This exports sanitized per-task scalars/checksums and the exact v2 candidate UID
manifest, preserving the older Full-432 and v1 rows. The default Lite selector
still uses v1. See [the historical-v2-selection guide](lite72-v2-historical.md).

For a fresh model evaluation, follow the repository-level
[`LITE72_RUN_GUIDE.md`](../LITE72_RUN_GUIDE.md). It validates the frozen UID
manifest and creates the 72-record input before invoking the original generation,
execution, and visualization-judge scripts.

## Before enabling additional publication

Keep the repository license/attribution aligned with the actual redistributed material,
add a link to the public runner once its installation path is verified, and configure
Pages separately if desired. Do not describe locally retained raw artifacts as publicly
downloadable until a public archive and its links exist.
