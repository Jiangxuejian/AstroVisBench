# Documentation

For astronomers:

- [Results and score interpretation](index.md)
- [Dated leaderboard snapshots](leaderboards/README.md)
- [Download and prepare Lite-72 data](lite72-data-release.md)
- [Run the benchmark with your agent](../LITE72_AGENT_PROMPT.md)
- [T1: checks, revisions and final execution](T1_PROTOCOL.md)
- [Package and submit results for scoring](SUBMIT_RESULTS.md)

For reproducibility and maintenance:

- [Detailed methods and historical run records](lite72-v2-historical.md)
- [Execution and network-fairness audit](execution-fairness.md)
- [Data preparation notes](maintainer-data-notes.md)
- [Machine-readable scores and provenance](data/)
- [Archived v1 guide](archive/lite72-v1/README.md)

Folder map: `leaderboards/` holds frozen results; `data/` holds current public
score/evidence exports; `assets/` keeps compatibility figure URLs; `archive/`
holds superseded guides. Upstream workflow folders and `submission/` stay in
their original locations. Scientific data packages are distributed separately,
not copied into the documentation.

New runs use the current v2 task selection; the fully offline benchmark is
not yet released. GitHub Pages hosting is not enabled; these pages are readable
in the repository.
