from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {name}")
        return list(reader.fieldnames), list(reader)


def verify_checksums() -> None:
    checksum_file = ROOT / "SHA256SUMS.txt"
    if not checksum_file.is_file():
        raise FileNotFoundError("Missing SHA256SUMS.txt")
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative_name = line.split("  ", 1)
        path = ROOT / relative_name
        if not path.is_file():
            raise FileNotFoundError(f"Missing checksummed file: {relative_name}")
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch: {relative_name}")


def verify_release() -> dict[str, int]:
    core_fields, core = read_csv("datasets_release_v1_1_core.csv")
    extended_fields, extended = read_csv("datasets_release_v1_1_extended.csv")
    _, corrections = read_csv("corrections_application_v1_1.csv")
    schema = json.loads((ROOT / "release_schema_v1_1.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / "validation_report_v1_1.json").read_text(encoding="utf-8"))

    if len(core) != 70 or len(extended) != 70:
        raise ValueError("Expected 70 rows in both core and extended tables")
    if len(core_fields) != 46 or len(extended_fields) != 87:
        raise ValueError("Unexpected core or extended field count")
    core_ids = [row["dataset_id"] for row in core]
    extended_ids = [row["dataset_id"] for row in extended]
    if len(set(core_ids)) != 70 or set(core_ids) != set(extended_ids):
        raise ValueError("Dataset IDs are not unique or core/extended IDs differ")
    if any(row["release_version"] != "v1.1" for row in extended):
        raise ValueError("Unexpected release_version value")
    if any(row["release_status"] != "final" for row in extended):
        raise ValueError("Unexpected release_status value")

    canonical = len({row["canonical_dataset_id"] for row in extended})
    contributions = Counter(row["count_in_unique_participant_total"] for row in extended)
    asd = sum(int(row["unique_asd_contribution"] or 0) for row in extended)
    controls = sum(int(row["unique_control_contribution"] or 0) for row in extended)

    if canonical != 64:
        raise ValueError("Expected 64 canonical entities")
    if contributions != Counter({"yes": 55, "no": 10, "partial": 5}):
        raise ValueError("Unexpected contribution-flag counts")
    if (asd, controls, asd + controls) != (2770, 2187, 4957):
        raise ValueError("Unexpected overlap-adjusted contribution")
    if len(corrections) != 35:
        raise ValueError("Expected 35 correction items")
    if schema.get("release_version") != "v1.1" or schema.get("release_status") != "final":
        raise ValueError("Schema release labels are not final v1.1")
    if report.get("validation_status") != "pass" or report.get("errors") or report.get("warnings"):
        raise ValueError("Canonical validation report is not a clean pass")

    return {
        "accession_records": len(extended),
        "canonical_entities": canonical,
        "correction_items": len(corrections),
        "asd_contribution": asd,
        "control_contribution": controls,
        "combined_contribution": asd + controls,
    }


def main() -> None:
    verify_checksums()
    metrics = verify_release()
    print("ASD Microbiome Atlas v1.1 verification: PASS")
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
