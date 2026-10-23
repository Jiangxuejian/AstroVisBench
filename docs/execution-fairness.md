---
layout: default
title: Execution fairness audit
---

# Execution fairness audit

Snapshot: **23 October 2026**. This is an audit of existing results, not a new
benchmark protocol or a claim that cross-model environmental differences have
been resolved.

## Kimi K3 correction — complete

The earlier report combined an older execution file with repaired execution
records already used for judging. We retained records 1–300 and selected the
existing repaired records 301–432. All UIDs and generated/reference code were
checked against the original generation file. All three judge trials agree
with execution Crash status for every record: **zero mismatches**.

| Metric | Previous report | Reconciled |
| --- | ---: | ---: |
| Processing No Error | 63.89% | 48.15% |
| Visualization No Error | 84.95% | 76.85% |
| VIscore | 0.72205 | 0.73090 |

VIscore uses 113 eligible inspections. Judge category percentages, including
CorrectV, are unchanged. Original artifacts are preserved; the new execution
checksum and old values are recorded in [K3 provenance](data/k3-audit.json).
Raw execution artifacts remain local; no public download is claimed.

## Shared reference preflight — in progress

A diagnostic for the fixed Lite-72 UIDs across QWEN, K3, and GPT-6 is preparing
checksummed copies of input archives and a dependency-version inventory.
It executes the original reference setup, processing, and visualization code.
Every code cell must have executed without an error: an empty or unexecuted
notebook cannot count as a success. Reference readiness failures are recorded
separately from model failures.

This diagnostic still uses live services. Archive copies and a dependency list
alone do not freeze remote downloads or API responses. GPT-6 is not being added
to the leaderboard by this update.

## Controlled reruns — not started

Before rerunning model submissions, external input files/responses and caches
must be captured, checksummed, and validated through reference replay without
external network access. Any necessary replay adapter must be explicit and
identical for all models. The pinned upstream executor and generated code
remain unchanged; no new generations or manual candidate repairs are needed.

Each model must then receive independent copies of the same verified inputs,
the same environment, seeds, limits, and fresh execution caches. Report all 72
readiness statuses and the common valid denominator. An incomplete subset must
not be labelled a complete Lite-72 result, and historical scores must not be
silently overwritten by reruns.

[Back to results](index.md)
