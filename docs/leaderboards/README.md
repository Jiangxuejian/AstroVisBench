# Leaderboard versions

- **[20261101](20261101/README.md)** — historical Full-432 and Lite-72 v2 results,
  with a separate VIscore panel. Assembled 13 November 2026; no scores recalculated.

Each folder preserves its figure, table, score data and public audit evidence.
Version labels identify snapshots, not benchmark execution dates.

New model results create a new snapshot. Changes to task selection, scientific
reference calculations or evaluation rules require a separately identified
benchmark/evaluation version; old scores remain available under their old rules.

For maintainers: update and validate the current results, then run
`python scripts/archive_leaderboard.py --version YYYYMMDD` from the repository
root. Existing snapshot folders cannot be overwritten by this command. Link the
new folder from this index and the front-page README.
