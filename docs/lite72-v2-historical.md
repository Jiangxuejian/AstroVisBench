---
layout: default
title: Lite-72 v2 task selection — historical-input agent scores
---

# Lite-72 v2 task selection: historical-input agent scores

Snapshot: **27 October 2026**. Both agents have completed generation and
execution for all 72 selected workflows. **These are not official frozen-input
v2 results.** They use the new task list with historical/live-service inputs,
not the proposed frozen-file/SQLite distribution.

## Execution results

| T1 coding agent | Coverage | Processing no error | Visualization no error | VIscore | VI eligible |
|---|---:|---:|---:|---:|---:|
| GPT-6 Astra medium + Codex | 72/72 | 48/72 = 66.67% | 60/72 = 83.33% | 0.6700 | 40 |
| Claude Code + Kimi K3 | 72/72 | 44/72 = 61.11% | 62/72 = 86.11% | 0.6162 | 33 |

Execution success is not proof of scientific correctness. Complete-72
CorrectV, VisFail and minor/major-error aggregates are **not available** and
are represented as `null` / `n/a`, never zero. No new judge trials were run:
GPT-6 is unjudged; Claude's 65 overlapping historical judgments are not
extrapolated to its seven new plots.

Downloads:

- [GPT-6 audit, per-task scalars and source checksums](data/gpt6-v2-selection-audit.json)
- [Claude + K3 audit, per-task scalars and source checksums](data/claude-k3-v2-selection-audit.json)
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

Each result contains **65 unchanged baseline executions plus seven supplemental
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

for name in ("gpt6-v2-selection-audit", "claude-k3-v2-selection-audit"):
    audit = json.loads(Path(f"docs/data/{name}.json").read_text())
    rows = audit["records"]
    assert len(rows) == len({r["uid"] for r in rows}) == 72
    vi = [r["vi_score"] for r in rows
          if r["processing_success"] and r["vi_score"] is not None]
    print(name,
          100 * sum(r["processing_success"] for r in rows) / 72,
          100 * sum(r["visualization_success"] for r in rows) / 72,
          mean(vi), len(vi))
```

`scripts/prepare_v2_selection_agent_scores.py --artifacts-root <operator-project>`
rebuilds these sanitized downloads from the completed local coverage reports,
verifies source execution checksums, and checks 65+7 origins and all 72 UIDs.
Raw artifact availability is separate; hashes do not imply a public download.

[Back to results](index.md)
