# AstroVisBench Lite-72 subset run guide

This guide makes the **Lite-72 subset (candidate v1)** reproducible for a
different model or harness while preserving the original AstroVisBench workflow:

**Prepare → Generate → Execute → Judge → Aggregate**

Lite-72 is a complete evaluation of a fixed sampled subset. It is **not** an
incomplete or partially finished Full-432 run.

## 1. What is fixed

| Item | Lite-72 candidate v1 |
|---|---|
| Workflows | 72 of 432 |
| Generation stages | 144 (72 processing + 72 visualization) |
| Visualization trials | 3 per workflow, up to 216 outcomes |
| Source notebooks | 62 |
| Selection seed | `astrovis-lite72-candidate-v1-20260930` |
| Manifest SHA-256 | `25a97c7deae01f4590cd5d14d0d77a170a7be2a46f2d50a972eac4fe5a1d4d2e` |
| Dataset SHA-256 | `c48528947378e138c8c1df26531f1fd37e96a9226a52659ea838cc543a8e22e2` |
| Upstream source | `707657f8fac4df50a6cf6c2c4671bf6a0258a201` |

The selection allocates 12 workflows to each provisional source-notebook family:

- Spectroscopy
- Photometry
- Image processing
- Time-series analysis
- Cosmology and spatial structure
- Simulation and modeling

Within each family, four workflows are selected from each of three ground-truth
code-length bands (short, medium, long). Code length is only a complexity proxy;
the family labels are not official per-task scientific classifications. Selection
is result-blind and uses deterministic SHA-256 tie-breaking plus notebook
diversity. Do not replace this selection with the first 72 records.

The manifest is the authority for the subset:

- [`docs/data/lite72-candidate-v1.json`](docs/data/lite72-candidate-v1.json)
- [`docs/data/lite72-qwen-tasks.csv`](docs/data/lite72-qwen-tasks.csv)

## 2. Pin the repository and obtain upstream inputs

Use a repository commit, not an unrecorded moving working tree. For the current
public results page:

```bash
git clone https://github.com/Jiangxuejian/AstroVisBench.git
cd AstroVisBench
git checkout 7a1a655a24f8e664d6e311ce9241a4eb8b1baf8c
```

Follow the upstream [environment setup](README.md#environment-setup) to obtain:

1. the full `astrovisbench_queries.json` (432 records),
2. the benchmark environment archive, and
3. the optional ground-truth cache.

Keep these large inputs outside the Git repository when possible. Do not commit
model weights, credentials, caches, generated images, or raw benchmark outputs.

## 3. Create the selected benchmark JSON

Run the repository selector against the **full** upstream JSON:

```bash
python scripts/select_lite72_subset.py \
  --benchmark /path/to/astrovisbench_queries.json \
  --manifest docs/data/lite72-candidate-v1.json \
  --output /path/to/lite72-candidate-v1.json
```

The selector checks that:

- the source contains 432 unique UIDs;
- the manifest contains exactly 72 unique UIDs;
- every manifest UID is present in the source;
- the source SHA-256 matches the manifest;
- records are emitted in source-benchmark order; and
- selection is UID-based, not a first-N slice.

The output is an ordinary JSON list and can be passed to the original
generation script. The selector refuses to overwrite an existing output unless
`--force` is supplied. Do not use `--allow-dataset-mismatch` for a comparable
benchmark; that option is only for explicitly documented development work.

## 4. Generate code using the original protocol

For the standard no-tool model track, use the original generator and prompts:

```bash
python generate_code/generate_code.py \
  /path/to/lite72-candidate-v1.json \
  /path/to/lite72-generated.json \
  <MODEL_NAME> <LIBRARY>
```

Optional stage flags are documented by the original script, including
`--generate-pro-only` and `--generate-vis-only`. Generation must be checkpointed
without changing the task list. In the standard track, the evaluated model gets
no tools, no execution feedback, and no iterative code repair. Do not manually
repair generated code before execution.

Coding-agent experiments are a separate track. Record the model, harness
version, permitted tools, correction loop, token/call limits, and wall-clock
budget. Do not compare a T1/T2 agent row directly with a T0 no-tool row.

## 5. Execute with the original executor

Use the original `exec_bench.py` command and a fresh set of Lite cache/output
paths. A typical invocation is:

```bash
python exec_bench.py \
  /path/to/lite72-generated.json \
  /path/to/bench_env \
  --true-cache /path/to/lite72-true-cache \
  --gen-cache /path/to/lite72-generated-processing-cache \
  --vis-cache /path/to/lite72-generated-visualization-cache \
  --outfile /path/to/lite72-executed.json \
  --temp-caching \
  --min-diff-only
```

Do not use `--skip-test` if you need the normal processing execution and VIscore
metrics. Preserve the executed JSON, executor revision, environment identifier,
hardware, cache settings, exit status, and a SHA-256 checksum.

## 6. Judge after execution

Only after execution has completed, run the original visualization-evaluation
step:

```bash
python vis_evaluation/vis_evaluation.py \
  /path/to/lite72-executed.json \
  /path/to/lite72-judged.json
```

Retain three trial outcomes per workflow, the judge model and settings, the
transport/tool policy, and any invocation failures. A judge invocation failure is
pending—not a model error—and must be resolved or reported separately. Crashes
and VisFail outcomes must remain distinguishable from LLM-judge categories.

The original `aggregate_results.py` consumes the upstream-compatible result
field. If you publish a three-trial mean, state that explicitly and preserve the
per-trial records; do not silently present a first-trial score as a three-trial
mean.

## 7. Validate before publishing

Every Lite-72 result should include a compact run manifest with at least:

- repository/upstream commit and dataset SHA-256;
- Lite manifest SHA-256 and selected UID count (`72`);
- model repository/revision, parameter size, and quantization;
- generation model/harness, prompt settings, and tool policy;
- execution environment, executor checksum, and output checksum;
- judge model, reasoning setting, trial count, transport, and invocation status;
- processing/visualization denominators and VIscore eligibility count; and
- known limitations or protocol deviations.

Before comparing two Lite results, verify that they use the same manifest and
the same task-stage protocol. Report Full-432 and Lite-72 in separate tables.
Lite percentages are screening results for this sampled mixture, not replacements
for the official Full-432 leaderboard.

## 8. Interpretation limits

The candidate is provisional. Equal family allocation changes the task mixture
relative to Full-432, and the family labels are operator-assigned proxies. Lite
results should be used for lower-cost screening and pipeline checks; ranking
stability should be tested across additional models before calling the subset a
validated replacement for the full benchmark.

For the selection rationale and current audited comparison, see the [Lite-72
section in the results page](docs/index.md#lite-72-candidate-v1).
