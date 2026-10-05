# GitHub Pages content draft

`index.md` is the one-page public content for the Jiangxuejian fork. Working title:
**AstroVisBench — Independent Model Evaluations**. The files are published in the
repository's `main` branch; GitHub Pages configuration, a custom domain, and a
separate public raw-artifact archive remain optional and are not assumed here.

The page uses ordinary Markdown and relative download links. It can be placed in a
GitHub Pages/Jekyll site when the public repository is chosen. The grouped bar chart
contains the published reference rows plus the audited QWEN and Kimi K3 Full-432
runs. Keep the Full and Lite results visually separate; STEP3-VL is currently
published only as a Lite-72 processing record.

## Content decisions

- Attribute the upstream benchmark prominently and identify this as independent work.
- Publish only scores audited from complete, frozen records. QWEN and Kimi K3 are Full-432 local rows; STEP3-VL is a processing-only Lite-72 row.
- Keep Lite-72 explicitly provisional, including its imperfect notebook-family labels.
- Mark Smoke, the portable public runner, and the agent comparison track as unfinished.
- Describe the actual three-trial aggregation and eligible VIscore denominators.
- Distinguish requested judge identity from a verified backend snapshot.
- Avoid placeholder repository URLs, invented commands, or promises of exact cost savings.
- Keep host filesystem paths, credentials, raw prompts, and large artifacts out of the
  downloadable page data. Candidate UIDs and notebook names are sufficient here.

## Updating the content

The existing audited sources are `results/lite72-candidate-v1/`, the QWEN and Kimi K3
run manifests/provenance, and the STEP3-VL Lite processing summary. Generate the
small public downloads using:

```bash
python3 scripts/prepare_pages_data.py
.astrovis-data/venvs/original-bench/bin/python scripts/build_leaderboard_assets.py
```

The first script exports the QWEN evidence; it does not rerun generation, execution, or
judging. Kimi K3 and STEP3-VL compact records are retained as
`docs/data/k3-audit.json` and `docs/data/step3-lite-processing.json`. The second
script reads `docs/data/leaderboard.json` and regenerates the matching SVG/PNG figure.
The prose and table cells remain deliberately easy to edit as one Markdown page. When
new scores are added, update the text, source selection, and checks together.

## Before enabling additional publication

Keep the repository license/attribution aligned with the actual redistributed material,
add a link to the public runner once its installation path is verified, and configure
Pages separately if desired. Do not describe locally retained raw artifacts as publicly
downloadable until a public archive and its links exist.
