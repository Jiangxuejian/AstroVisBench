# GitHub Pages content draft

`index.md` is the proposed one-page public content. It is ready for editorial review,
not a deployment. Working title: **AstroVisBench — Independent Model Evaluations**.
No GitHub repository, Pages configuration, custom domain, or publication was created.

The page uses ordinary Markdown and relative download links. It can be placed in a
GitHub Pages/Jekyll site when the public repository is chosen. Presentation and the
grouped bar chart can be added after the content is approved. Keep the Full and Lite
results visually separate.

## Content decisions

- Attribute the upstream benchmark prominently and identify this as independent work.
- Publish only the QWEN scores audited in this session; do not infer other runs' readiness.
- Keep Lite-72 explicitly provisional, including its imperfect notebook-family labels.
- Mark Smoke, the portable public runner, and the agent comparison track as unfinished.
- Describe the actual three-trial aggregation and eligible VIscore denominators.
- Distinguish requested judge identity from a verified backend snapshot.
- Avoid placeholder repository URLs, invented commands, or promises of exact cost savings.
- Keep host filesystem paths, credentials, raw prompts, and large artifacts out of the
  downloadable page data. Candidate UIDs and notebook names are sufficient here.

## Updating the content

The existing audited sources are `results/lite72-candidate-v1/` and the QWEN run
manifest/provenance. Generate the small public downloads using:

```bash
python3 scripts/prepare_pages_data.py
.astrovis-data/venvs/original-bench/bin/python scripts/build_leaderboard_assets.py
```

The first script exports evidence; it does not rerun generation, execution, or judging.
It also checks numeric values displayed on the page against the audited scores. The
second script reads `docs/data/leaderboard.json` and regenerates the matching SVG/PNG
figure. The prose and table cells remain deliberately easy to edit as one Markdown page.
When new scores are added, update the text, source selection, and checks together.

## Before publication

Choose the repository name and website title, add a link to the public runner once
its installation path is verified, and check the repository license/attribution for
the actual redistributed material. Add presentation and Pages deployment separately.
Do not describe locally retained raw artifacts as publicly downloadable until a
public archive and its links exist.
