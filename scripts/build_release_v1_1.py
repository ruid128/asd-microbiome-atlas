#!/usr/bin/env python3
"""Validate final v1.1 and build the limited public website data projection.

The frozen files in data/release_v1_1 remain the repository source of truth.
After integrity checks pass, the script exports only fields used by the public
Atlas interface; internal curation and release documents are not published.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data" / "release_v1_1"
WEB = ROOT / "web" / "data"

FILES = (
    "datasets_release_v1_1_core.csv",
    "datasets_release_v1_1_extended.csv",
    "release_schema_v1_1.json",
    "corrections_application_v1_1.csv",
    "validation_report_v1_1.json",
    "release_manifest_v1_1.md",
)

RELEASE_DOCUMENTS = (
    "prisma_summary_v1_1.md",
    "release_notes_v1_1.md",
)

PUBLIC_FILE = "atlas_public_v1_1.json"
PUBLIC_FIELDS = (
    "dataset_id",
    "source_db",
    "accession",
    "dataset_title",
    "url",
    "linked_accessions",
    "linked_publications",
    "publication_title",
    "doi",
    "pmid",
    "paper_verified",
    "country",
    "study_design",
    "n_total",
    "n_asd",
    "n_control",
    "body_site",
    "assay_type",
    "sequencing_platform",
    "raw_data_public",
    "downloadable_asd_control_pair",
    "record_status",
    "canonical_dataset_id",
    "release_version",
    "release_status",
)

EXPECTED_SHA256 = {
    "datasets_release_v1_1_core.csv": "251553197745c1be44c5d8e5f6977999d3a3023313dfe370f696e029928910bc",
    "datasets_release_v1_1_extended.csv": "ebd3074f6d7525fa454a807795cd30b6eb5e40024677ee5d872aede64a5bc5b6",
    "release_schema_v1_1.json": "f69efcd93961a3786ded25be19589a80537f9c5e689186eb0273ab5c9a330e1a",
    "corrections_application_v1_1.csv": "01655545676c750e3dcdcaa55e1712cd9929f95b937a18e9d7cecf8afcc46fd6",
    "validation_report_v1_1.json": "8a24d5465bbc99b2a7c58d7613d9c6b6fe2dda5c8eba58e1eb7b0ea56aa6633a",
    "release_manifest_v1_1.md": "6c42cbd87cd34905e3a98ca0d79c8e7058534c49ed6efea1e9420b6aef472d78",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_release() -> dict[str, object]:
    errors: list[str] = []
    hashes: dict[str, str] = {}

    for name in FILES:
        path = RELEASE / name
        require(path.is_file(), f"Missing release file: {name}", errors)
        if not path.is_file():
            continue
        hashes[name] = sha256(path)
        require(
            hashes[name] == EXPECTED_SHA256[name],
            f"SHA-256 mismatch for {name}",
            errors,
        )

    for name in RELEASE_DOCUMENTS:
        require((RELEASE / name).is_file(), f"Missing release document: {name}", errors)

    if errors:
        return {"status": "fail", "errors": errors, "sha256": hashes}

    core, core_fields = read_csv(RELEASE / "datasets_release_v1_1_core.csv")
    extended, extended_fields = read_csv(
        RELEASE / "datasets_release_v1_1_extended.csv"
    )
    core_by_id = {row["dataset_id"]: row for row in core}
    extended_by_id = {row["dataset_id"]: row for row in extended}

    require(len(core) == 70, f"Core has {len(core)} rows; expected 70", errors)
    require(
        len(extended) == 70,
        f"Extended has {len(extended)} rows; expected 70",
        errors,
    )
    require(
        len(core_fields) == 46,
        f"Core has {len(core_fields)} columns; expected 46",
        errors,
    )
    require(
        len(extended_fields) == 87,
        f"Extended has {len(extended_fields)} columns; expected 87",
        errors,
    )
    require(
        len(core_by_id) == len(core), "Core dataset_id values are not unique", errors
    )
    require(
        len(extended_by_id) == len(extended),
        "Extended dataset_id values are not unique",
        errors,
    )
    require(
        set(core_by_id) == set(extended_by_id),
        "Core and extended dataset_id sets differ",
        errors,
    )

    canonical_count = len(
        {row["canonical_dataset_id"] for row in core if row["canonical_dataset_id"]}
    )
    require(
        canonical_count == 64,
        f"Found {canonical_count} canonical entities; expected 64",
        errors,
    )

    expected_rows = {
        "SCR00048": {
            "raw_data_public": "no",
            "record_status": "metadata_only",
            "count_in_unique_participant_total": "no",
        },
        "SCR00124": {
            "n_total": "82",
            "n_asd": "41",
            "n_control": "41",
            "raw_data_public": "yes",
            "record_status": "included_partial_overlap",
            "count_in_unique_participant_total": "partial",
        },
        "SCR00158": {
            "study_design": "intervention",
            "sequencing_platform": "Illumina MiniSeq",
            "intervention_flag": "yes",
            "longitudinal_flag": "yes",
            "downloadable_asd_control_pair": "yes",
            "record_status": "included",
            "count_in_unique_participant_total": "yes",
        },
        "SCR00180": {
            "assay_type": "multi_omic",
            "record_status": "included",
            "count_in_unique_participant_total": "yes",
        },
    }
    for dataset_id, expected in expected_rows.items():
        core_row = core_by_id.get(dataset_id)
        extended_row = extended_by_id.get(dataset_id)
        require(core_row is not None, f"Missing critical core row {dataset_id}", errors)
        require(
            extended_row is not None,
            f"Missing critical extended row {dataset_id}",
            errors,
        )
        if core_row is None or extended_row is None:
            continue
        row = {**core_row, **extended_row}
        for field, value in expected.items():
            require(
                row.get(field) == value,
                f"{dataset_id}.{field} is {row.get(field)!r}; expected {value!r}",
                errors,
            )

    report = json.loads(
        (RELEASE / "validation_report_v1_1.json").read_text(encoding="utf-8-sig")
    )
    require(report.get("validation_status") == "pass", "Frozen validation failed", errors)
    require(report.get("release_version") == "v1.1", "Unexpected release version", errors)
    require(
        report.get("release_status") == "final",
        "Unexpected release status",
        errors,
    )

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "metrics": {
            "core_rows": len(core),
            "core_columns": len(core_fields),
            "extended_rows": len(extended),
            "extended_columns": len(extended_fields),
            "canonical_entities": canonical_count,
        },
        "sha256": hashes,
    }


def main() -> None:
    result = validate_release()
    if result["status"] != "pass":
        print(json.dumps(result, indent=2))
        raise SystemExit(1)

    core, _ = read_csv(RELEASE / "datasets_release_v1_1_core.csv")
    public_records = [
        {field: row.get(field, "") for field in PUBLIC_FIELDS}
        for row in core
    ]
    public_payload = {
        "release_version": "v1.1",
        "release_status": "final",
        "metrics": {
            "records_identified": 340,
            "records_screened": 208,
            "accession_records": len(core),
            "canonical_entities": len(
                {row["canonical_dataset_id"] for row in core if row["canonical_dataset_id"]}
            ),
            "overlap_adjusted_asd": sum(
                int(row["unique_asd_contribution"] or 0) for row in core
            ),
            "overlap_adjusted_controls": sum(
                int(row["unique_control_contribution"] or 0) for row in core
            ),
        },
        "records": public_records,
    }

    WEB.mkdir(parents=True, exist_ok=True)
    destination = WEB / PUBLIC_FILE
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(public_payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    result["public_view"] = {
        "file": PUBLIC_FILE,
        "fields_per_record": len(PUBLIC_FIELDS),
        "sha256": sha256(destination),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
