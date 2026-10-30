---
layout: default
title: Lite-72 v2 task selection — historical-input agent scores
---

# Lite-72 v2 task selection: historical-input agent scores

Snapshot: **30 October 2026**. GPT-6 + Codex, Claude + K3 and the separate
Codex + Qwen recovery track each have 72 execution records and 216 validated
visualization outcomes. **These are not official frozen-input
v2 results.** They use the new task list with historical/live-service inputs,
not the proposed frozen-file/SQLite distribution.

## Execution results

| T1 coding agent | Coverage | Processing no error | Visualization no error | VIscore | VI eligible |
|---|---:|---:|---:|---:|---:|
| GPT-6 Astra medium + Codex | 72/72 | 48/72 = 66.67% | 60/72 = 83.33% | 0.6700 | 40 |
| Claude Code + Kimi K3 | 72/72 | 44/72 = 61.11% | 62/72 = 86.11% | 0.6162 | 33 |
| Codex + Qwen3.8-27B Q4_K_M · recovery | 72/72 | 25/72 = 34.72% | 39/72 = 54.17% | 0.5789 | 19 |

Execution success is not proof of scientific correctness. The recovery row
includes two missing processing submissions as failures, not successful blanks.

## Visualization judge results

| Agent | CorrectV | Minor error | Major error | VisFail | Crash |
|---|---:|---:|---:|---:|---:|
| GPT-6 + Codex | 25.93% | 25.00% | 24.07% | 8.33% | 16.67% |
| Claude Code + K3 | 17.59% | 21.76% | 34.26% | 12.50% | 13.89% |
| Codex + Qwen · recovery | 6.94% | 9.26% | 28.24% | 9.72% | 45.83% |

Each row uses **216 valid outcomes = 72 workflows × three trials**, including
deterministic Crash/VisFail outcomes; percentages are counts divided by 216,
not majority votes or successful-plots-only scores. GPT-6's category counts
are 56/54/52/18/36; Claude's 38/47/74/27/30; Qwen's 15/20/61/21/99, in the
column order above. No invocation error is assigned a scientific category.

Judge: **GPT-6 Astra (`gpt-6-astra`), medium**, Codex CLI **0.153.4**, Python
**3.10.12**, ijson **3.5.1**. Original rubric, reference/generated image order,
code context and Crash/VisFail rules are preserved by the local provider
adapter. GPT/Claude completed on 28 October; Qwen on 30 October at 09:11
Asia/Shanghai. Claude's 65 overlapping historical judgments were retained;
the seven supplements are now judged, not extrapolated. Completed valid trials
were never rerun to improve scores. Failed invocation histories stay local.

Current Mac app version and immutable hosted judge build are unobserved.
Checkpoint/input/provenance hashes and all 72 per-task category lists are in
the scalar audits. Automated judging remains distinct from human review, and
same-model bias is possible when GPT-6 judges GPT-6-generated plots.

Downloads:

- [GPT-6 audit, per-task scalars and source checksums](data/gpt6-v2-selection-audit.json)
- [Claude + K3 audit, per-task scalars and source checksums](data/claude-k3-v2-selection-audit.json)
- [Codex + Qwen recovery audit and per-task outcomes](data/codex-qwen38-v2-selection-recovery-audit.json)
- [Exact 72-task candidate manifest](data/lite72-v2-candidate.json)
- [Leaderboard data](data/leaderboard.json)

## Selection and data status

The candidate contains 72 UIDs from 61 notebooks: 12 per provisional notebook
family, four per original short/medium/long code-length band. It retains 65
v1 UIDs and adds seven. The selection was frozen using reference code,
science anchors and data-packaging constraints **before inspecting model
results**. Code length is a proxy, not measured task difficulty; the family
labels are inherited metadata, not official task-level scientific labels.

| Pinned item | Identifier |
|---|---|
| Selection SHA-256 | `a9ed93a935b2e984e546fdebbcfef7b0f14879e3b93064db6985e34ef4541f3b` |
| Dataset SHA-256 | `c48528947378e138c8c1df26531f1fd37e96a9226a52659ea838cc543a8e22e2` |
| Upstream revision | `707657f8fac4df50a6cf6c2c4671bf6a0258a201` |

The manifest's frozen-database protocol describes the **intended new data
track**, not the inputs used for these historical scores. The full frozen
input package has not passed all 72 offline reference validations or been
released. A fixed UID list alone does not establish identical remote data.

Select these exact UIDs from the pinned original 432-record JSON:

```bash
python scripts/select_lite72_subset.py \
  --benchmark /path/to/astrovisbench_queries.json \
  --manifest docs/data/lite72-v2-candidate.json \
  --output /path/to/lite72-v2-selected-original-tasks.json
```

This selects tasks only; it does **not** install frozen data or the local
catalogue adapter. The [original run guide](../LITE72_RUN_GUIDE.md) remains
the guide to v1 and upstream evaluation. Its default selector manifest is
unchanged. T1 agent evaluation additionally requires the isolated supervised
harness; that operator-specific harness and the large raw artifacts are not
claimed as a portable one-command public release here.

## How the historical coverage was completed

GPT-6 and Claude + K3 each contain **65 unchanged baseline executions plus seven supplemental
executions**. Every selected UID remains in the denominator, including crashes.
The seven tasks were selected by the fixed UID difference, not by performance.
No best-of merging, manually repaired candidates or cross-model code mixing.

GPT-6 reused one already submitted, checked matching-version task and generated
the remaining six. A provider-capacity HTTP 429 paused generation; the resume
retained charged budgets and prior submissions. Final execution completed
normally, and exact coverage was validated at 09:31 Asia/Shanghai on 27 October.

Claude generated all seven tasks using project-local CLI 2.1.285. Its outer
executor segfaulted after saving three records. Those records and the original
partial file were preserved. The remaining four records completed using the
**same upstream executor in fresh processes**, with the original inspection
tests and flags. No native thread-setting override or candidate-code change
was needed. Exact coverage was validated at 09:15 Asia/Shanghai on 27 October.
The audit records identify the separate recovered execution checksum; an outer
process crash is not silently converted into a synthetic model score.

## Qwen supplemental recovery

This is **not an original capped T1 baseline**. The original Qwen run finished
144 terminal stages but lacked processing code for selection tasks 17/51/52.
Only 51/52 were authorized one fresh bounded processing attempt each. Task 51
submitted code; task 52 again exhausted 20 requests without a candidate. Only
task 51's processing code was substituted; no visualization code was changed.
Original capped results, failed attempts and charged budgets remain preserved.
Task 52's original compaction-adapter fault is recorded, not attributed solely
to model science capability; its separate corrected retry was fault-free.

All 72 UIDs remain in execution/judge denominators. Missing processing 17/52
are marked failures and removed from VI eligibility only in a separate
accounting view. The raw pristine executor output remains untouched: upstream
can report blank cells as non-crashing, which must not inflate success here.
WSL interrupted execution; 11 completed records were preserved, and the
unchanged executor resumed missing UIDs after quarantining an empty interrupted
reference cache. No candidate or reference code was manually repaired.
Network-download timeouts still affected these historical-input scores.

| Qwen generation component | Recorded version |
|---|---|
| Model | Qwen3.8-27B Q4_K_M |
| Weights repository | `ggml-org/Qwen3.8-27B-GGUF` |
| HF revision | `0669b98607d47046c7c2b3f801011d54a08cfccf` |
| Weights SHA-256 | `31629f53165ab6a7dad8c9847dcfd1fdf55829dac1e6e748f4a68581b0033d34` |
| Generation CLI | Codex `0.162.1` |
| Model server | llama.cpp `b10679`, commit `50f068fff` |
| Responses adapter | `qwen-responses-context-compaction-v5-20261028` |
| Context / temperature / seed | 32,768 / 0 / 42; reasoning disabled |

The original T1 per-stage limits below also applied to each supplemental
attempt. This extra retry allowance is why recovery is labelled separately,
not silently ranked against single-budget runs.

## Model, harness and budgets

| Component | GPT-6 + Codex | Claude Code + K3 |
|---|---|---|
| Requested model | `gpt-6-astra` | `k3` |
| Reasoning | medium | original low-effort target |
| Baseline CLI | Codex `0.162.1` | Claude `2.1.285` / `2.1.289` |
| Supplemental CLI | Codex `0.162.1` | Claude `2.1.285` |
| Profile | T1 | T1 |
| Own/reference image viewing | Not allowed | Not allowed |

Each processing/visualization stage has its own session: 20 model requests,
32,768 total output tokens, 8,192 per response, three candidate checks (two
feedback corrections), 600 seconds per check, and 2,400 seconds wall time.
Tools are limited to listing/reading approved inputs, writing a candidate,
running a candidate check, and submitting. No subagents or human hints.
The original visualization-stage reference-processing context is retained;
hidden inspection scores and judge feedback are not exposed to the agent.

Final evaluation keeps the original executor and processing equivalence tests.
The serial MPI-import launcher and CPU TensorFlow runtime settings are recorded
operator adaptations, not changes to candidate code. Hosted aliases cannot
pin an immutable backend model build. Claude baseline version drift, different
run dates and live input availability are explicit reproducibility limitations.

## Recalculate the published scalar metrics

The public audits contain all 72 per-task scalar records, without host paths,
credentials, raw prompts, model transcripts, or large notebook outputs:

```python
import json
from pathlib import Path
from statistics import mean

for name in ("gpt6-v2-selection-audit", "claude-k3-v2-selection-audit",
             "codex-qwen38-v2-selection-recovery-audit"):
    audit = json.loads(Path(f"docs/data/{name}.json").read_text())
    rows = audit["records"]
    assert len(rows) == len({r["uid"] for r in rows}) == 72
    vi = [r["vi_score"] for r in rows
          if r["processing_success"] and r["vi_score"] is not None]
    print(name,
          100 * sum(r["processing_success"] for r in rows) / 72,
          100 * sum(r["visualization_success"] for r in rows) / 72,
          mean(vi), len(vi))
    from collections import Counter
    counts = Counter(outcome for r in rows for outcome in r["judge_outcomes"])
    assert sum(counts.values()) == 216
    print({category: 100 * n / 216 for category, n in counts.items()})
```

`scripts/prepare_v2_selection_agent_scores.py --artifacts-root <operator-project>`
rebuilds these sanitized downloads from the completed local coverage reports,
verifies source execution checksums, and checks 65+7 origins and all 72 UIDs.
Then run `scripts/publish_completed_v2_scores.py --artifacts-root <operator-project>`
to validate completed checkpoints, export all three agents' scalar categories,
apply Qwen's explicit missing-submission accounting and update leaderboard data.
Run `python scripts/order_leaderboard.py` to keep the JSON/table display grouped
by suite/track and sorted by CorrectV within each group. Then run
`python scripts/build_leaderboard_assets.py` to regenerate SVG and PNG, and
`python -m unittest discover -s scripts -p 'test_v2_selection_publication.py'`
to check metrics, coverage, track labels, sanitization and local links.
Raw artifact availability is separate; hashes do not imply a public download.

[Back to results](index.md)
