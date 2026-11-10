# Submit your Lite-72 results for scoring

After execution, send the maintainer **two files**: your result archive
(`my-run.tar.gz`) and its checksum (`my-run.tar.gz.sha256`).
You do **not** need to run a judge or provide judge credentials.

## Let your agent do it

Copy this message to the coordinating agent that ran the benchmark:

```text
Package my completed Lite-72 run for maintainer-side scoring.
Read docs/SUBMIT_RESULTS.md and use scripts/package_lite72_submission.py.
Locate the run directory and original full benchmark JSON; ask if uncertain.
First run --check-only. Preserve generated code, failed tasks, inspection
results, reference plots and all generated plots exactly as recorded.
Check the run metadata and review included files for secrets/private data.
Do not invent missing records or usage counters, repair code, retry tasks,
or run judges. If evidence is missing, report it before proceeding.
After privacy review, package to a new path outside the run directory.
Return the archive and .sha256 paths, model/harness/input version, coverage
and any missing stages or deviations. Do not upload anything automatically.
```

## What is included?

The existing packager selects only the evidence needed for scoring:

| Evidence | Files in the run directory |
|---|---|
| Tasks, submitted code and execution results, including embedded plots | `selected_benchmark.json`, `generated_benchmark.json`, `executed_benchmark.json` |
| Model, harness, input version and stage history | `run_manifest.json`, `stage_ledger.json` |
| Environment and execution notes | `requirements.freeze.txt`, `execution.log`, `RUN_NOTES.md` |
| Agent evidence, where applicable | `generation_events.jsonl` (required for T1); optional generation/execution adapters |

Use the [manifest template](../submission/run_manifest.example.json) and
[run prompt](../LITE72_AGENT_PROMPT.md) when preparing these records.
Failed tasks must stay included; an interrupted run is not a completed submission.
For new T1 runs, retain the [protocol version and freeze evidence](T1_PROTOCOL.md#evidence-for-new-runs).
Do not reconstruct missing budgets or relabel a legacy run as the new protocol.

<details>
<summary>Commands for your agent or manual use</summary>

Run from the repository checkout with Python 3.10+, substituting actual paths.
The full source JSON is checked locally but is not included in the archive.

```bash
python scripts/package_lite72_submission.py \
  --run-dir /path/to/my-run \
  --benchmark /path/to/astrovisbench_queries.json \
  --check-only

# After reviewing included files for secrets and private material:
python scripts/package_lite72_submission.py \
  --run-dir /path/to/my-run \
  --benchmark /path/to/astrovisbench_queries.json \
  --output /path/to/submissions/my-run.tar.gz --reviewed
```

The checker requires the current v2 selection: 72 workflows / 144 stage records.
It preserves raw results and plots, flags missing code, and refuses incomplete
coverage or overwritten outputs. It does not evaluate science or certify privacy.

</details>

## Send to the maintainer

Send **both files** through your agreed private channel, with the model/harness
name and any known limitations. If too large for an attachment, send a private
download link. Do not post raw submissions in public issues or releases.

Do not send the input data bundle, model weights, caches, Python environment
or entire workspace. The maintainer will review the submission and run the
common visualization judge; successful packaging is not itself a score.
