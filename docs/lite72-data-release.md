---
layout: default
title: Lite-72 data
---

# Get the Lite-72 data

The **~9.9 GB download** supports all **72 workflows / 144 tasks** across
61 astronomy notebooks. It includes notebook data and shared calibration files;
you will still need a scientific Python environment.

[Download from GitHub](https://github.com/Jiangxuejian/AstroVisBench/releases/tag/lite72-data-20261109) ·
[GitLab mirror](https://gitlab.zhejianglab.com/jiangxuejian/astrovisbench-lite/-/tree/data/lite72-20261109-curated-v1/lite72-data/20261109-curated-v1) ·
[Benchmark prompt for your agent](../LITE72_AGENT_PROMPT.md)

## Start here

Ask your coordinating agent to download and prepare the bundle, then follow the
benchmark prompt. Allow **at least 50 GB free**, plus space for software and
execution outputs. Downloads are public; no account is needed.

<details>
<summary>Download and preparation commands for you or your agent</summary>

Requires Python 3.10+. Choose one download source; do not use the automatically
generated Source code ZIP. Start in a new directory.

**GitHub:** download the release files without installing Git LFS.

```bash
mkdir astrovisbench-data && cd astrovisbench-data
base=https://github.com/Jiangxuejian/AstroVisBench/releases/download/lite72-data-20261109
for file in README.md BUNDLE.sha256 SHA256SUMS UPLOAD_READY.json \
    INSTALLER_REVIEW.json NIRISS_INTEGRITY.json PAYLOAD_REVIEW.json \
    RESTORE_HEADER_REVIEW.json lite72_share_bundle.py \
    lite72-share.tar.xz.part-{00..04}; do
  curl --fail --location --retry 3 --output "$file" "$base/$file" || exit 1
done
```

**GitLab alternative:** requires Git and [Git LFS](https://git-lfs.com/).

```bash
git lfs install
git clone --single-branch --branch data/lite72-20261109-curated-v1 \
  https://gitlab.zhejianglab.com/jiangxuejian/astrovisbench-lite.git astrovisbench-data
cd astrovisbench-data
git lfs pull
cd lite72-data/20261109-curated-v1
```

**After either download:**

```bash
sha256sum -c SHA256SUMS
cat lite72-share.tar.xz.part-00 lite72-share.tar.xz.part-01 \
    lite72-share.tar.xz.part-02 lite72-share.tar.xz.part-03 \
    lite72-share.tar.xz.part-04 > lite72-share.tar.xz
sha256sum -c BUNDLE.sha256
python3 lite72_share_bundle.py verify lite72-share.tar.xz
python3 lite72_share_bundle.py restore lite72-share.tar.xz restored-lite72
```

Use a new restore directory. Point the run prompt's `BENCH_ENV` at
`restored-lite72/bench_env` and `FULL_BENCHMARK_JSON` at
`restored-lite72/operator/astrovisbench_queries.json`.
Choose input version `20261109-curated-v1`; the prompt selects the current v2 tasks.

</details>

## What matters scientifically

- **Not fully offline:** some catalogue queries and other downloads still need internet access. Record service failures separately from scientific errors.
- **Keep answers hidden:** the bundle includes reference material. Only the coordinating operator—not the evaluated model—may access the complete bundle.
- **Declared input variant:** compact NIRISS files retain all 70 science image arrays and scientific primary metadata, but omit unused FITS extensions. Unused installer copies are removed; expanded calibration data remain. Record this version rather than treating it as identical to earlier inputs.
- **Not new validation:** download verification does not establish scientific correctness or completion of all offline reference tests. Existing leaderboard scores are unchanged.
- **Attribution:** retain source/component notices. File-level third-party redistribution review remains incomplete.

[Results and methods](lite72-v2-historical.md) ·
[Download verification](data/lite72-share-publication.json) ·
[Maintainer preparation notes](maintainer-data-notes.md)
