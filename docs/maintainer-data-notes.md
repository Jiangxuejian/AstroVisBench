# Data preparation: maintainer notes

These are optional technical instructions, not required reading for astronomers.
For downloads and scientific limitations, see the [data guide](lite72-data-release.md).

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
