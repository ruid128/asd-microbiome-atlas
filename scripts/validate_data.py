#!/usr/bin/env python3
"""Validate datasets.csv and screening_log.csv against JSON schemas and business rules."""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_schema(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_enum(value: str, allowed: list[str], field: str, row_id: str) -> list[str]:
    if value and value not in allowed:
        return [f"{row_id}: {field}='{value}' not in {allowed}"]
    return []


def validate_datasets(rows: list[dict], schema: dict) -> list[str]:
    errors = []
    props = schema.get("properties", {})
    seen_ids = set()

    for i, row in enumerate(rows, 1):
        rid = row.get("dataset_id", f"row_{i}")

        # Required fields
        for field in schema.get("required", []):
            if not row.get(field):
                errors.append(f"{rid}: missing required field '{field}'")

        # Enum validation
        for field, spec in props.items():
            if "enum" in spec and row.get(field):
                errors.extend(validate_enum(row[field], spec["enum"], field, rid))

        # Duplicate IDs
        if rid in seen_ids:
            errors.append(f"{rid}: duplicate dataset_id")
        seen_ids.add(rid)

        # n_total check
        try:
            n_asd = int(row.get("n_asd") or 0)
            n_ctrl = int(row.get("n_control") or 0)
            n_total = int(row.get("n_total") or 0)
            if n_total and n_total != n_asd + n_ctrl:
                errors.append(f"{rid}: n_total ({n_total}) != n_asd ({n_asd}) + n_control ({n_ctrl})")
        except ValueError:
            pass  # non-numeric is ok for unknown

        # At least one accession
        accession_fields = [
            "bioproject_accession", "study_accession", "geo_accession",
            "mgnify_accession", "qiita_study_id",
        ]
        if not any(row.get(f) for f in accession_fields):
            errors.append(f"{rid}: no accession in any identifier field")

    return errors


def validate_screening(rows: list[dict], schema: dict) -> list[str]:
    errors = []
    props = schema.get("properties", {})
    seen_ids = set()

    for i, row in enumerate(rows, 1):
        rid = row.get("screening_id", f"row_{i}")

        for field in schema.get("required", []):
            if not row.get(field):
                errors.append(f"{rid}: missing required field '{field}'")

        for field, spec in props.items():
            if "enum" in spec and row.get(field):
                errors.extend(validate_enum(row[field], spec["enum"], field, rid))

        # exclusion_reason only when excluded
        decision = row.get("decision", "")
        reason = row.get("exclusion_reason", "")
        if decision == "exclude" and not reason:
            errors.append(f"{rid}: decision=exclude but no exclusion_reason")
        if decision == "include" and reason:
            errors.append(f"{rid}: decision=include but exclusion_reason='{reason}'")
        if decision == "maybe":
            errors.append(f"{rid}: unresolved 'maybe' decision")

        if rid in seen_ids:
            errors.append(f"{rid}: duplicate screening_id")
        seen_ids.add(rid)

    return errors


def check_referential_integrity(
    datasets: list[dict], screening: list[dict]
) -> list[str]:
    errors = []

    included_accessions = {
        row["accession"]
        for row in screening
        if row.get("decision") == "include" and row.get("accession")
    }

    dataset_accessions = set()
    for row in datasets:
        for field in ["bioproject_accession", "study_accession", "geo_accession",
                       "mgnify_accession", "qiita_study_id"]:
            if row.get(field):
                dataset_accessions.add(row[field])

    for acc in included_accessions:
        if acc not in dataset_accessions:
            errors.append(f"Screening include '{acc}' has no matching datasets.csv row")

    return errors


def completeness_report(rows: list[dict]) -> None:
    if not rows:
        print("\nNo datasets to report on.")
        return

    fields = list(rows[0].keys())
    print(f"\n{'Field':<30} {'Filled':>6} {'Total':>6} {'%':>6}")
    print("-" * 52)
    for field in fields:
        total = len(rows)
        filled = sum(1 for r in rows if r.get(field) and r[field] != "unknown")
        pct = (filled / total * 100) if total else 0
        print(f"{field:<30} {filled:>6} {total:>6} {pct:>5.1f}%")


def prisma_counts(search_dir: Path, screening: list[dict]) -> None:
    print("\n=== PRISMA Flow Counts ===\n")

    # Identification
    total_hits = 0
    print("IDENTIFICATION")
    for csv_file in sorted(search_dir.glob("*.csv")):
        rows = load_csv(csv_file)
        n = len(rows)
        total_hits += n
        print(f"  {csv_file.stem:<20} {n:>5}")
    print(f"  {'Total':<20} {total_hits:>5}")

    # Duplicates
    dupes = sum(1 for r in screening if r.get("exclusion_reason") == "duplicate_dataset")
    print(f"\n  Duplicates removed:  {dupes}")

    # Screening
    screened = len(screening)
    excluded = sum(1 for r in screening if r.get("decision") == "exclude")
    included = sum(1 for r in screening if r.get("decision") == "include")

    print(f"\nSCREENING")
    print(f"  Records screened:    {screened}")
    print(f"  Records excluded:    {excluded}")

    reasons = {}
    for r in screening:
        if r.get("decision") == "exclude":
            reason = r.get("exclusion_reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1
    for reason, count in sorted(reasons.items()):
        print(f"    - {reason:<35} {count:>4}")

    print(f"\nINCLUDED")
    print(f"  Studies in atlas:    {included}")


def main():
    datasets = load_csv(DATA / "datasets.csv")
    screening = load_csv(DATA / "screening_log.csv")
    ds_schema = load_schema(SCHEMAS / "datasets_schema.json")
    sl_schema = load_schema(SCHEMAS / "screening_log_schema.json")

    all_errors = []
    all_errors.extend(validate_datasets(datasets, ds_schema))
    all_errors.extend(validate_screening(screening, sl_schema))
    all_errors.extend(check_referential_integrity(datasets, screening))

    print("=== Validation Report ===\n")
    if all_errors:
        print(f"ERRORS ({len(all_errors)}):")
        for e in all_errors:
            print(f"  - {e}")
    else:
        print("No validation errors found.")

    completeness_report(datasets)
    prisma_counts(DATA / "search_results", screening)

    print("\n" + "=" * 40)
    if all_errors:
        print(f"RESULT: FAIL ({len(all_errors)} errors)")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
