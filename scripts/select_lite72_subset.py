#!/usr/bin/env python3
"""Create the frozen Lite-72 benchmark JSON from a UID manifest.

The selector is deliberately model-agnostic. It preserves the source
benchmark order, checks UID coverage, and verifies the dataset checksum stored
in the candidate manifest before writing a plain JSON list accepted by the
upstream generation and execution scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("docs/data/lite72-candidate-v1.json")
DEFAULT_COUNT = 72


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def uid_list(records: Any, *, path: Path, field: str) -> list[str]:
    if not isinstance(records, list):
        raise ValueError(f"{path} must contain a JSON list")
    uids: list[str] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict) or not isinstance(record.get(field), str):
            raise ValueError(f"{path}: record {index} has no string {field!r}")
        uids.append(record[field])
    duplicates = sorted({uid for uid in uids if uids.count(uid) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicate UIDs: {', '.join(duplicates[:5])}")
    return uids


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select the frozen Lite-72 workflows by UID and validate coverage."
    )
    parser.add_argument(
        "--benchmark", type=Path, required=True,
        help="full upstream benchmark JSON (432 records)",
    )
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST,
        help=f"frozen UID manifest (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="output JSON path for the selected records",
    )
    parser.add_argument(
        "--expected-count", type=int, default=DEFAULT_COUNT,
        help=f"expected selected workflow count (default: {DEFAULT_COUNT})",
    )
    parser.add_argument(
        "--allow-dataset-mismatch", action="store_true",
        help="write despite a manifest/source SHA-256 mismatch; not comparable to the published subset",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="overwrite an existing output file",
    )
    args = parser.parse_args()

    try:
        if args.expected_count <= 0:
            raise ValueError("--expected-count must be positive")
        benchmark = load_json(args.benchmark)
        manifest = load_json(args.manifest)
        if not isinstance(manifest, dict) or not isinstance(manifest.get("tasks"), list):
            raise ValueError(f"{args.manifest} must contain a top-level tasks list")

        source_uids = uid_list(benchmark, path=args.benchmark, field="uid")
        manifest_uids = uid_list(manifest["tasks"], path=args.manifest, field="uid")
        if len(manifest_uids) != args.expected_count:
            raise ValueError(
                f"manifest contains {len(manifest_uids)} workflows; expected {args.expected_count}"
            )
        if len(source_uids) != 432:
            raise ValueError(
                f"source benchmark contains {len(source_uids)} records; expected the full 432"
            )

        source_set = set(source_uids)
        manifest_set = set(manifest_uids)
        missing = sorted(manifest_set - source_set)
        if missing:
            raise ValueError(
                f"{len(missing)} manifest UIDs are absent from the source benchmark; first: {missing[0]}"
            )

        source_sha = sha256(args.benchmark)
        expected_sha = manifest.get("dataset_sha256")
        if expected_sha and source_sha != expected_sha and not args.allow_dataset_mismatch:
            raise ValueError(
                "source dataset SHA-256 does not match the manifest: "
                f"expected {expected_sha}, got {source_sha}. "
                "Use the pinned upstream JSON or explicitly pass --allow-dataset-mismatch."
            )

        selected = [record for record in benchmark if record["uid"] in manifest_set]
        if len(selected) != args.expected_count:
            raise ValueError(
                f"selected {len(selected)} workflows; expected {args.expected_count}"
            )

        if args.output.resolve() == args.benchmark.resolve():
            raise ValueError("output must not overwrite the full source benchmark")
        if args.output.exists() and not args.force:
            raise ValueError(f"output exists: {args.output}; use --force to replace it")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(selected, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

        output_sha = sha256(args.output)
        status = "verified" if expected_sha == source_sha else "override"
        print(f"Selected {len(selected)} workflows from {len(benchmark)} source records.")
        print(f"Manifest: {args.manifest} ({len(manifest_uids)} UIDs)")
        print(f"Dataset SHA-256: {source_sha} ({status})")
        print(f"Output: {args.output}")
        print(f"Output SHA-256: {output_sha}")
        print("Order: source benchmark order; selection is UID-based, not first-N.")
        return 0
    except ValueError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
