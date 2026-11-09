---
layout: default
title: Lite-72 data sharing
---

# Lite-72 data sharing

**Status: GitLab sharing candidate prepared on 9 November 2026;
not uploaded and not a complete offline release.**
The fixed v2 selection has 72 workflows / 144 generation stages, drawn from
61 notebooks. The original selected environment archives total 13.95 GiB;
this excludes additional runtime downloads and is not a final bundle size.

The maintainer selected [GitLab Zhejiang Lab](https://gitlab.zhejianglab.com/jiangxuejian/astrovisbench-lite/)
for convenient file sharing, not a formal ScienceDB publication. Scripts and
public instructions remain on GitHub; no data package is committed there.
The GitLab code mirror and the data download are separate: package upload
awaits registry authentication and confirmation of recipient access. The code
repository is currently anonymously readable; do not assume its package storage
is private. File-level redistribution review remains incomplete.
Do not tar the workspace or expose the original archives wholesale to agents:
some archives contain HTML/notebooks or other possible solution material.
Scientific model files used as task inputs (for example trained flare models)
are distinct from the evaluated language-model weights and may be necessary.

## Two distinct releases

- **Historical-input convenience bundle:** preserves the original data and
  layout, but may still need live services. It must not be advertised as offline.
- **Frozen-input benchmark:** local files plus executable read-only catalogue
  snapshots/adapters, validated offline for all 72 workflows. Its data-contract
  hash and results are separate from historical leaderboard results.

There are 55 file-strategy workflows, 15 SQL workflows and two catalogue-API
workflows. Recorded offline reference validation currently covers only four
workflows, not the full suite. These are previous validation records, not a
fresh validation performed by the packaging audit.

## Maintainer audit

Use Python 3.10+ from a normal unprivileged environment; no model calls or
scientific code execution occurs. Substitute actual quoted paths:

```bash
python scripts/prepare_lite72_data.py audit \
  --benchmark /path/to/astrovisbench_queries.json \
  --bench-env /path/to/bench_env \
  --output /path/to/new-audit-directory
```

Optionally pass `--readiness /path/to/packaging_status.json` to record prior
validation evidence and known additional assets. The tool checks pinned source
and selection hashes; hashes and streams all 61 selected archives without
extracting them; inventories member names/types/sizes; and emits:

- `inventory.json`: exact archive identities, task coverage and review flags;
- `review.template.json`: unapproved source/licence/content review records;
- `REPORT.md`: readable inventory and remaining gates;
- `status.json`: progress and completion state.

Flags include unsafe paths, links/devices, solution-like or executable files,
possible reference images/secrets, nested archives and platform sidecars.
These conservative heuristics are **not a content, secret or licence audit**.
An unflagged archive still requires review of every member and its provenance.
Private audit reports can include source filenames; review before sharing.

After changing name/type heuristics, `refresh-flags --audit-dir OLD --output NEW`
can reclassify a completed inventory without rereading payloads. It retains the
original inventory checksum, resets approvals and explicitly records that no
source rescan occurred; packaging still rechecks every source hash.

## Private sharing transport (under 10 GB target)

The reviewed compressed archive is **9,879,775,056 bytes (9.8798 GB)**. Its
five upload parts plus helper, guide, review records and checksums total
**9,879,807,635 bytes**, below 10,000,000,000 bytes. All 2,860 payload hashes
and the reassembled-parts SHA256 were verified; 37 tooling/publication tests
pass. These checks do not imply all 72 references have been validated offline.
No live download URL is available yet. The intended destination is the project's
[Generic Package registry](https://gitlab.zhejianglab.com/jiangxuejian/astrovisbench-lite/-/packages),
with package name `lite72-share` and version `20261109-curated-v1`.

Archive SHA256:
`3c529d7f389db96d7d652f9749391c443c4b5fad4e8e96c96b88fbaffb9dc06a`.
Download **all 14 files** of the version into one directory, not both the
unsplit archive and its parts. After downloading, use Python 3.10+:

```bash
sha256sum -c SHA256SUMS
cat lite72-share.tar.xz.part-00 lite72-share.tar.xz.part-01 \
    lite72-share.tar.xz.part-02 lite72-share.tar.xz.part-03 \
    lite72-share.tar.xz.part-04 > lite72-share.tar.xz
sha256sum -c BUNDLE.sha256
python3 lite72_share_bundle.py verify lite72-share.tar.xz
python3 lite72_share_bundle.py restore lite72-share.tar.xz restored-lite72
```

Use a new restore directory and allow at least **50 GB free** for download,
restoration and retained staging, plus space for dependencies/execution caches.
The restored `bench_env/` supplies notebook archives, while
`operator/astrovisbench_queries.json` is the full pinned source benchmark.
Use `operator/lite72-v2-candidate.json` explicitly with the selector; its default
is legacy v1. Follow the [current operator prompt](../LITE72_AGENT_PROMPT.md) for
generation and execution, then submit unjudged outputs to the maintainer.
The bundle's ready marker records preparation-time state, not upload completion.

`scripts/lite72_share_bundle.py` stages selected environment members by SHA256,
stores identical file payloads once, and compresses them using standard XZ.
It includes a standalone verifier/restorer that recreates the original
`bench_env/<notebook>/*_comped.tar.gz` layout without modifying the evaluator.
Regular-file contents and member metadata are preserved; regenerated gzip/tar
hashes differ and are recorded separately. No original paths or links are
extracted directly onto the host. Transport verification is not scientific
reference validation, redistribution clearance or a complete offline release.

The size gate is **10,000,000,000 bytes for the whole archive**, not 10 GiB and
not a claim that splitting reduces total storage. The optional compact NIRISS
asset keeps all 70 SCI arrays and scientific primary metadata, with prior
two-pass offline reference validation. Unused HDUs, old FITS checksum cards
and an existing generated CSV are omitted; this variant is explicit in the
manifest and must not be represented as identical full-HDU historical inputs.
No image cropping, resampling, precision reduction or task deletion is used.

The reviewed variant also omits three unused compressed installer copies:
MIRI's `synphot5.tar.gz` and WebbPSF installer, plus NIRCam's WebbPSF installer.
Both WebbPSF installers match their expanded files exactly. The synphot
installer is truncated in the original input; its readable data match the
expanded calibration tree. All expanded calibration inputs remain unchanged;
five readable unique documentation files are retained under `operator/`.
The manifest records original installer hashes, byte counts and review results.
`curate-installers OLD_WORK NEW_WORK` performs this bounded review/curation;
it does not prune arbitrary files, repair arrays or change historical scores.

The private transport may retain original solution-like files, plots and
helpers to avoid unvalidated input deletion. It is **operator-only**, not a
clean raw-input bundle to expose to task-solving agents. T1 runs still require
audited per-stage allowlists and source/reference separation. Scientific CNN
input images/weights may be included as downloads with original URLs; live
catalogue services and other uncached dependencies remain possible.

On 9 November 2026 the selected GitLab instance's public
[configuration](https://gitlab.zhejianglab.com/help/instance_configuration)
reported 5 GiB per Generic Package file and about 4.883 GiB per attachment.
This does not establish the project's storage quota. Prefer Generic Package
uploads in modest parts rather than repeated large Git commits; no upload or
account/billing change is performed by these tools.

## Packaging gate

Complete a copy of the review template only after confirming rights and raw
input content, with licence notices/evidence covering all included members.
Unresolved flags cannot be waived by ticking approval fields. Quarantine
solutions/evaluation material separately; any cleaned/repacked archive needs
new hashes and reference validation, not an edited inventory to hide flags.

```bash
python scripts/prepare_lite72_data.py package-reviewed \
  --audit-dir /path/to/audit-directory \
  --bench-env /path/to/bench_env \
  --review /path/to/completed-review.json \
  --output /path/to/new-lite72-historical-inputs.tar.gz
```

This limited packager only accepts the exact 61 original archive paths when
all checks pass. It preserves archive bytes, writes deterministic gzip/tar
metadata and an internal manifest, verifies hashes during copying, and creates
an outer `.sha256`. Already-compressed payloads are stored without another
expensive compression pass. It does **not** assemble the future frozen-input
or evaluation bundle, certify science, install anything or upload files.
Existing output paths are refused; an interrupted/failed archive is incomplete.

## Future frozen-release gates

1. Resolve each file's provenance, licence and redistribution permission;
   retain upstream attribution and component-specific notices. Do not assume
   the code repository licence covers every scientific input. The
   [upstream README](https://github.com/NSF-Simons-CosmicAI-Institute/AstroVisBench#citation--license)
   declares CC BY-SA 4.0 for the benchmark; this is recorded provenance, not
   automatic clearance of every third-party payload.
2. Package all required files, shared assets and calibration resources once.
   Preserve paths and scientific scope; do not shrink images or sky footprints
   merely to make the package smaller.
3. Freeze raw source tables with rejected rows, join keys, units, metadata,
   footprint and acquisition records. Preserve real SQL/query reasoning;
   do not cache only the reference answer. Validate API/SQL semantics explicitly.
4. Run every unchanged reference twice with networking externally disabled in
   a clean environment. Check data products, plots and repeatability; record
   environment/adapter/data-contract hashes. Candidate code is not repaired.
5. Build `lite72-inputs-v1.tar.gz`, separate operator/evaluation assets, hashes
   and a short README. Audit archive paths/member types before extraction and
   test fresh downloads. Keep evaluation material outside solver sandboxes.
6. The maintainer approves component rights, recipients and access controls
   before external sharing. Keep version/hash identifiers and network caveats
   alongside every package. Do not default the whole mixed dataset to CC BY.

A formal ScienceDB deposit/DOI is optional and is not required for the chosen
GitLab file-sharing workflow. See [historical results and caveats](lite72-v2-historical.md) and the
[contributor generation/execution prompt](../LITE72_AGENT_PROMPT.md).
