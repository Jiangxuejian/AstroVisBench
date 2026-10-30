# GitHub Pages content draft

`index.md` is the one-page public content for the Jiangxuejian fork. Working title:
**AstroVisBench — Independent Model Evaluations**. The files are published in the
repository's `main` branch; GitHub Pages configuration, a custom domain, and a
separate public raw-artifact archive remain optional and are not assumed here.

The page uses ordinary Markdown and relative download links. It can be placed in a
GitHub Pages/Jekyll site when the public repository is chosen. The portrait horizontal bar chart
contains the published reference rows, the audited QWEN and Kimi K3 Full-432
runs and completed GPT-6,
Claude + K3 and Codex + Qwen recovery historical-v2-selection rows. Keep
the Full and Lite suites and the T0/T1 tracks distinct when interpreting it.
Only Full-432 and the historical Lite-72 v2 selection appear in the current
figure/table. Lite-72 v1 is retained as historical audit data, not displayed.
The figure additionally omits no-tool Qwen while retaining that table/audit row.
Its labels contain model/harness names and only `(lite-bench)` for Lite-72 v2;
suite/tool/recovery qualifications remain in the caption and detailed table.

## Content decisions

- Attribute the upstream benchmark prominently and identify this as independent work.
- Publish metrics only after their own coverage is audited. Historical-v2-selection agent rows now have 72 records and 216 valid judge outcomes each. Qwen is a separately labelled supplemental recovery, not the original capped T1 baseline. Do not call any of these frozen-input v2 results.
- Keep Lite-72 explicitly provisional, including its imperfect notebook-family labels.
- Mark Smoke and the portable public runner as unfinished; identify the Claude Code + K3 agent comparison as a separate T1 track.
- Describe the actual three-trial aggregation and eligible VIscore denominators.
- Distinguish requested judge identity from a verified backend snapshot.
- Avoid placeholder repository URLs, invented commands, or promises of exact cost savings.
- Keep host filesystem paths, credentials, raw prompts, and large artifacts out of the
  downloadable page data. Candidate UIDs and notebook names are sufficient here.

## Updating the content

For contributor-side generation/execution and compressed submissions, link to
[`LITE72_AGENT_PROMPT.md`](../LITE72_AGENT_PROMPT.md), not the old v1 default guide.
The packager is `scripts/package_lite72_submission.py`; its offline tests are
`python -m unittest discover -s scripts -p test_lite72_submission.py`.
It does not invoke a judge or upload packages. Maintainer-side safety and
eligibility checks still apply before common judging/publication.

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
`docs/data/leaderboard.json` and regenerates `leaderboard-portrait.svg` and
`leaderboard-portrait.png` (and the matching `leaderboard-full.*` compatibility
aliases), rendering
missing metrics, including pending visualization judgments, as `n/a` rather than zero.
The prose and table cells remain deliberately easy to edit as one Markdown page. When
new scores are added, update the text, source selection, and checks together.

The initial 27 October execution-only export is retained for provenance as
`scripts/prepare_v2_selection_agent_scores.py`. It refuses to overwrite
completed judge scores. To refresh the completed 30 October scores, run:

```bash
python scripts/publish_completed_v2_scores.py --artifacts-root /path/to/operator-project
python scripts/order_leaderboard.py
python scripts/build_leaderboard_assets.py
python -m unittest discover -s scripts -p test_v2_selection_publication.py
```

This exports sanitized per-task scalars/checksums and the exact v2 candidate UID
manifest, preserving Full-432 scores and archived v1 rows. The default Lite selector
still uses v1. See [the historical-v2-selection guide](lite72-v2-historical.md).

`leaderboard_order.py` defines the shared display policy: Full-432/v2 only,
CorrectV descending across all displayed rows, missing metrics last, ties by
model ID. Suite/track classifications remain in labels, not sorting groups.
`order_leaderboard.py` moves existing table lines verbatim, orders the JSON,
and preserves excluded v1 rows under `archived_rows`; it does not change scores.
Run it after any data export, then
rebuild both figure formats. `python scripts/order_leaderboard.py --check`
verifies that the committed table and data already follow this policy.

For a fresh model evaluation, follow the repository-level
[`LITE72_RUN_GUIDE.md`](../LITE72_RUN_GUIDE.md). It validates the frozen UID
manifest and creates the 72-record input before invoking the original generation,
execution, and visualization-judge scripts.

## Before enabling additional publication

Keep the repository license/attribution aligned with the actual redistributed material,
add a link to the public runner once its installation path is verified, and configure
Pages separately if desired. Do not describe locally retained raw artifacts as publicly
downloadable until a public archive and its links exist.
