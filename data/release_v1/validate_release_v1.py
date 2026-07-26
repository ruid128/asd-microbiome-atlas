import csv
import json
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "release_schema_v1.json"
CORE_PATH = BASE_DIR / "datasets_release_v1_core.csv"
EXTENDED_PATH = BASE_DIR / "datasets_release_v1_extended.csv"
REPORT_PATH = BASE_DIR / "validation_report_v1.json"


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def nonempty(value: str) -> bool:
    return str(value or "").strip() != ""


def is_int_string(value: str) -> bool:
    return str(value or "").strip().isdigit()


def validate_columns(
    rows: List[Dict[str, str]],
    required_columns: List[str],
    errors: List[str],
) -> None:
    if not rows:
        errors.append("CSV has no rows.")
        return
    cols = list(rows[0].keys())
    missing = [c for c in required_columns if c not in cols]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    fully_empty = []
    for col in cols:
        if all(not nonempty(r.get(col, "")) for r in rows):
            fully_empty.append(col)
    if fully_empty:
        errors.append(f"Fully empty columns present in release file: {fully_empty}")


def validate_dataset_ids(rows: List[Dict[str, str]], errors: List[str]) -> None:
    ids = [r["dataset_id"] for r in rows]
    if any(not nonempty(x) for x in ids):
        errors.append("Blank dataset_id values found.")
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        errors.append(f"Duplicate dataset_id values found: {dup}")


def validate_allowed(
    rows: List[Dict[str, str]],
    allowed_values: Dict[str, List[str]],
    errors: List[str],
) -> None:
    for col, allowed in allowed_values.items():
        if col not in rows[0]:
            continue
        bad = sorted(
            {
                r[col]
                for r in rows
                if nonempty(r.get(col, "")) and r[col] not in allowed
            }
        )
        if bad:
            errors.append(f"Column {col} has values outside controlled vocabulary: {bad}")


def validate_counts(rows: List[Dict[str, str]], errors: List[str]) -> None:
    for r in rows:
        sid = r["dataset_id"]
        required_numeric = ["n_total", "n_asd", "n_control"]
        for col in required_numeric:
            if not is_int_string(r.get(col, "")):
                errors.append(f"{sid}: {col} is blank or non-integer.")
        n_other = r.get("n_other", "").strip()
        if n_other and not is_int_string(n_other):
            errors.append(f"{sid}: n_other is non-integer.")
            continue
        if any(not is_int_string(r.get(c, "")) for c in required_numeric):
            continue
        total = int(r["n_total"])
        n_asd = int(r["n_asd"])
        n_control = int(r["n_control"])
        n_other_i = int(n_other) if n_other else 0
        if total != (n_asd + n_control + n_other_i):
            errors.append(
                f"{sid}: n_total mismatch ({total} != {n_asd}+{n_control}+{n_other_i})."
            )


def validate_nonblank_core_fields(rows: List[Dict[str, str]], errors: List[str]) -> None:
    key_fields = [
        "dataset_id",
        "source_db",
        "accession",
        "dataset_title",
        "url",
        "country",
        "study_design",
        "body_site",
        "assay_type",
        "release_class",
    ]
    for r in rows:
        sid = r["dataset_id"]
        for col in key_fields:
            if not nonempty(r.get(col, "")):
                errors.append(f"{sid}: required release field {col} is blank.")


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    core_rows = load_csv(CORE_PATH)
    extended_rows = load_csv(EXTENDED_PATH)

    errors: List[str] = []
    warnings: List[str] = []

    if len(core_rows) != schema["expected_core_rows"]:
        errors.append(
            f"Core row count mismatch: {len(core_rows)} != {schema['expected_core_rows']}"
        )
    if len(extended_rows) != schema["expected_extended_rows"]:
        errors.append(
            f"Extended row count mismatch: {len(extended_rows)} != {schema['expected_extended_rows']}"
        )

    validate_columns(core_rows, schema["core_required_columns"], errors)
    validate_columns(extended_rows, schema["extended_required_columns"], errors)
    if core_rows and extended_rows:
        validate_dataset_ids(core_rows, errors)
        validate_dataset_ids(extended_rows, errors)
        validate_allowed(core_rows, schema["allowed_values"], errors)
        validate_allowed(extended_rows, schema["allowed_values"], errors)
        validate_counts(core_rows, errors)
        validate_counts(extended_rows, errors)
        validate_nonblank_core_fields(core_rows, errors)

        core_ids = {r["dataset_id"] for r in core_rows}
        ext_ids = {r["dataset_id"] for r in extended_rows}
        if core_ids != ext_ids:
            errors.append("Core and extended dataset_id sets do not match.")

        release_classes = {r["release_class"] for r in core_rows}
        expected_exceptions = set(schema["accepted_exception_ids"])
        actual_exceptions = {
            r["dataset_id"] for r in core_rows if r["release_class"] != "standard"
        }
        if actual_exceptions != expected_exceptions:
            errors.append(
                f"Accepted exception dataset_id set mismatch: {sorted(actual_exceptions)} != {sorted(expected_exceptions)}"
            )
        if "needs_resolution" in release_classes:
            warnings.append("Unexpected internal QC-style label leaked into release_class.")

    report = {
        "release_version": schema["release_version"],
        "validated_at": "2026-06-05",
        "status": "pass" if not errors else "fail",
        "core_rows": len(core_rows),
        "extended_rows": len(extended_rows),
        "core_columns": list(core_rows[0].keys()) if core_rows else [],
        "extended_columns": list(extended_rows[0].keys()) if extended_rows else [],
        "accepted_exception_ids": schema["accepted_exception_ids"],
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "paper_linked_core": sum(1 for r in core_rows if nonempty(r.get("pmid", ""))),
            "repository_only_core": sum(1 for r in core_rows if not nonempty(r.get("pmid", ""))),
            "accepted_exceptions_core": sum(
                1 for r in core_rows if r.get("release_class") != "standard"
            ),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
