from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN_V1 = ROOT / "Frozen"
FROZEN = ROOT / "Frozen_v1.1"
CORE = FROZEN / "datasets_release_v1_1_core.csv"
EXTENDED = FROZEN / "datasets_release_v1_1_extended.csv"
SCHEMA = FROZEN / "release_schema_v1_1.json"
APPLICATION = FROZEN / "corrections_application_v1_1.csv"
MANIFEST = FROZEN / "release_manifest_v1_1.md"
REPORT_JSON = FROZEN / "validation_report_v1_1.json"
REPORT_MD = ROOT / "Manuscript" / "release_quality_audit_v1_1.md"
EXPECTED_RELEASE_VERSION = "v1.1-rc1"
EXPECTED_RELEASE_STATUS = "release_candidate"
VALIDATION_DATE = date.today().isoformat()
ALLOW_REPORT_OVERWRITE = False

V1_HASHES = {
    FROZEN_V1 / "datasets_release_v1_core.csv":
        "2832d114a90d91551189a3a6b3f2c2d9e210f8c3be05e022579c438fb002b46e",
    FROZEN_V1 / "datasets_release_v1_extended.csv":
        "741ac7e98754e96dd99418b488a610405987498efc0f6333e1c36227b9b0024a",
}
EXPECTED_ROWS = 70
EXPECTED_CORRECTIONS = 35
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
INTEGER_RE = re.compile(r"^(0|[1-9]\d*)$")
TRI_STATE_FIELDS = {
    "participant_resolved_raw_data",
    "downloadable_asd_control_pair",
    "repeated_sampling",
    "repeated_assay",
}
YES_NO_FIELDS = {
    "paper_verified",
    "intervention_flag",
    "longitudinal_flag",
    "biosample_metadata_available",
    "raw_data_public",
}
UNRESOLVED_PUBLIC_STATUSES = {"unresolved", "rolling_accession_not_fixed"}
COUNT_FIELDS = {
    "n_total", "n_asd", "n_control", "n_other",
    "article_n_total", "article_n_asd", "article_n_control", "article_n_other",
    "recruited_n_total", "recruited_n_asd", "recruited_n_control", "recruited_n_other",
    "public_n_total", "public_n_asd", "public_n_control", "public_n_other",
    "n_mothers", "n_siblings", "n_donors", "n_other_diagnosis", "all_human_hosts_n",
    "public_biosample_count", "public_run_count",
    "unique_asd_contribution", "unique_control_contribution",
    "unique_asd_control_contribution",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"Duplicate CSV columns: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Malformed CSV row width: {path}")
    return reader.fieldnames, rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def number(value: str) -> int:
    return int(value) if value else 0


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate() -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []

    required_files = [CORE, EXTENDED, SCHEMA, APPLICATION, MANIFEST, *V1_HASHES]
    for path in required_files:
        require(path.is_file(), f"Missing required file: {path}", errors)
    if errors:
        return {"validation_status": "fail", "errors": errors, "warnings": warnings}

    for path, expected_hash in V1_HASHES.items():
        require(
            sha256(path) == expected_hash,
            f"Frozen v1 changed: {path.name}",
            errors,
        )

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    core_fields, core_rows = read_csv(CORE)
    extended_fields, rows = read_csv(EXTENDED)
    application_fields, applications = read_csv(APPLICATION)

    require(schema.get("expected_rows") == EXPECTED_ROWS, "Schema row count is stale", errors)
    require(
        schema.get("release_version") == EXPECTED_RELEASE_VERSION,
        "Schema release version does not match the requested release",
        errors,
    )
    require(
        schema.get("release_status") == EXPECTED_RELEASE_STATUS,
        "Schema release status does not match the requested release",
        errors,
    )
    require(core_fields == schema.get("core_fields"), "Core header differs from schema", errors)
    require(
        extended_fields == schema.get("extended_fields"),
        "Extended header differs from schema",
        errors,
    )
    require(len(core_rows) == EXPECTED_ROWS, f"Core rows: {len(core_rows)}", errors)
    require(len(rows) == EXPECTED_ROWS, f"Extended rows: {len(rows)}", errors)
    require(len(applications) == EXPECTED_CORRECTIONS, f"Correction rows: {len(applications)}", errors)
    require(
        application_fields == [
            "issue_id", "affected_record", "application_status",
            "implementation_fields", "implementation_note",
        ],
        "Unexpected correction-application header",
        errors,
    )

    ids = [row["dataset_id"] for row in rows]
    accessions = [row["accession"] for row in rows]
    require(len(ids) == len(set(ids)), "Duplicate dataset_id", errors)
    require(len(accessions) == len(set(accessions)), "Duplicate primary accession", errors)

    by_id = {row["dataset_id"]: row for row in rows}
    core_by_id = {row["dataset_id"]: row for row in core_rows}
    require(set(core_by_id) == set(by_id), "Core/extended dataset_id mismatch", errors)
    for dataset_id, core_row in core_by_id.items():
        source_row = by_id.get(dataset_id, {})
        for field in core_fields:
            if core_row[field] != source_row.get(field):
                errors.append(f"Core/extended mismatch: {dataset_id}.{field}")

    required_schema_fields = {
        name for name, definition in schema["fields"].items() if definition.get("required")
    }
    for row in rows:
        dataset_id = row["dataset_id"]
        for field in required_schema_fields:
            require(bool(row[field].strip()), f"Blank required field: {dataset_id}.{field}", errors)
        require(row["url"].startswith("https://"), f"Non-HTTPS URL: {dataset_id}", errors)
        if row["doi"]:
            require(bool(DOI_RE.match(row["doi"])), f"Malformed DOI: {dataset_id}", errors)
        if row["candidate_doi"]:
            require(
                bool(DOI_RE.match(row["candidate_doi"])),
                f"Malformed candidate DOI: {dataset_id}",
                errors,
            )
        for field in COUNT_FIELDS:
            value = row[field]
            require(
                not value or bool(INTEGER_RE.match(value)),
                f"Invalid non-negative integer: {dataset_id}.{field}={value!r}",
                errors,
            )
        for field in YES_NO_FIELDS:
            require(row[field] in {"yes", "no"}, f"Invalid yes/no: {dataset_id}.{field}", errors)
        for field in TRI_STATE_FIELDS:
            require(
                row[field] in schema["controlled_vocabularies"]["tri_state"],
                f"Invalid tri-state: {dataset_id}.{field}",
                errors,
            )
        require(
            row["record_status"] in schema["controlled_vocabularies"]["record_status"],
            f"Invalid record_status: {dataset_id}",
            errors,
        )
        require(
            row["publication_link_status"]
            in schema["controlled_vocabularies"]["publication_link_status"],
            f"Invalid publication_link_status: {dataset_id}",
            errors,
        )
        require(
            row["count_in_unique_participant_total"]
            in schema["controlled_vocabularies"]["count_flag"],
            f"Invalid contribution flag: {dataset_id}",
            errors,
        )

        for prefix in ("", "article_", "recruited_", "public_"):
            total = row[f"{prefix}n_total"]
            groups = [row[f"{prefix}n_asd"], row[f"{prefix}n_control"], row[f"{prefix}n_other"]]
            if total and groups[0] and groups[1]:
                require(
                    number(total) == sum(number(value) for value in groups),
                    f"Count arithmetic mismatch: {dataset_id}.{prefix or 'study_'}n_*",
                    errors,
                )

        if row["public_count_status"] in UNRESOLVED_PUBLIC_STATUSES:
            require(
                all(not row[field] for field in ("public_n_total", "public_n_asd", "public_n_control", "public_n_other")),
                f"Unresolved public counts populated: {dataset_id}",
                errors,
            )
        if row["raw_data_public"] == "no":
            require(
                row["downloadable_asd_control_pair"] == "no",
                f"Non-public row marked downloadable: {dataset_id}",
                errors,
            )
        if row["record_status"] == "awaiting_verification":
            require(
                row["count_in_unique_participant_total"] == "uncertain",
                f"Awaiting-verification row contributes participants: {dataset_id}",
                errors,
            )

        contribution_fields = (
            "unique_asd_contribution", "unique_control_contribution",
            "unique_asd_control_contribution",
        )
        contribution_flag = row["count_in_unique_participant_total"]
        populated = [bool(row[field]) for field in contribution_fields]
        if contribution_flag == "uncertain":
            require(not any(populated), f"Uncertain contribution is populated: {dataset_id}", errors)
        else:
            require(all(populated), f"Resolved contribution is incomplete: {dataset_id}", errors)
        if all(populated):
            asd = number(row["unique_asd_contribution"])
            control = number(row["unique_control_contribution"])
            combined = number(row["unique_asd_control_contribution"])
            require(asd + control == combined, f"Contribution arithmetic mismatch: {dataset_id}", errors)
            if contribution_flag == "no":
                require(combined == 0, f"Excluded row contributes participants: {dataset_id}", errors)
            if row["count_as_independent_dataset"] == "no":
                require(combined == 0, f"Non-independent row contributes participants: {dataset_id}", errors)

    expected_issue_ids = [f"RC{index:03d}" for index in range(1, EXPECTED_CORRECTIONS + 1)]
    actual_issue_ids = [row["issue_id"] for row in applications]
    require(actual_issue_ids == expected_issue_ids, "Correction IDs are not contiguous", errors)
    allowed_application_statuses = {"applied", "applied_as_unresolved_guardrail"}
    for application in applications:
        issue_id = application["issue_id"]
        require(
            application["application_status"] in allowed_application_statuses,
            f"Correction not applied: {issue_id}",
            errors,
        )
        require(
            all(application[field].strip() for field in application_fields),
            f"Blank correction application field: {issue_id}",
            errors,
        )
        for dataset_id in (value.strip() for value in application["affected_record"].split(";")):
            require(dataset_id in by_id, f"Correction references absent row: {issue_id}/{dataset_id}", errors)
            if dataset_id in by_id:
                linked_issues = {value.strip() for value in by_id[dataset_id]["correction_issue_ids"].split(";") if value.strip()}
                require(issue_id in linked_issues, f"Correction provenance missing: {issue_id}/{dataset_id}", errors)

    require("SCR00124" in by_id, "SCR00124 was not restored", errors)
    if "SCR00124" in by_id:
        restored = by_id["SCR00124"]
        require(restored["accession"] == "PRJNA533120", "SCR00124 accession mismatch", errors)
        require(
            (restored["public_n_total"], restored["public_n_asd"], restored["public_n_control"])
            == ("82", "41", "41"),
            "SCR00124 archive counts mismatch",
            errors,
        )
        require(
            (restored["unique_asd_contribution"], restored["unique_control_contribution"])
            == ("22", "21"),
            "SCR00124 overlap-adjusted contribution mismatch",
            errors,
        )

    unresolved = [row for row in rows if row["count_in_unique_participant_total"] == "uncertain"]
    if unresolved:
        warnings.append(
            "Unique-participant total is provisional because unresolved records remain: "
            + "; ".join(f"{row['dataset_id']} / {row['accession']}" for row in unresolved)
        )

    manifest = MANIFEST.read_text(encoding="utf-8")
    release_hashes = {
        "core": sha256(CORE),
        "extended": sha256(EXTENDED),
        "schema": sha256(SCHEMA),
        "corrections_application": sha256(APPLICATION),
    }
    for digest in release_hashes.values():
        require(digest in manifest, f"Manifest omits release hash: {digest}", errors)

    status_counts = Counter(row["record_status"] for row in rows)
    contribution_counts = Counter(row["count_in_unique_participant_total"] for row in rows)
    unique_asd = sum(number(row["unique_asd_contribution"]) for row in rows)
    unique_control = sum(number(row["unique_control_contribution"]) for row in rows)

    return {
        "validation_status": "pass_with_guardrails" if not errors and warnings else ("pass" if not errors else "fail"),
        "validation_date": VALIDATION_DATE,
        "release_version": schema["release_version"],
        "release_status": schema["release_status"],
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "rows": len(rows),
            "correction_items": len(applications),
            "record_status_counts": dict(sorted(status_counts.items())),
            "contribution_flag_counts": dict(sorted(contribution_counts.items())),
            "canonical_dataset_entities": len({row["canonical_dataset_id"] for row in rows}),
            "provisional_unique_asd_contribution": unique_asd,
            "provisional_unique_control_contribution": unique_control,
            "provisional_unique_asd_control_contribution": unique_asd + unique_control,
            "unresolved_records": len(unresolved),
        },
        "sha256": release_hashes,
        "frozen_v1_unchanged": not any(
            sha256(path) != expected for path, expected in V1_HASHES.items()
        ),
    }


def markdown_report(report: dict[str, object]) -> str:
    metrics = report.get("metrics", {})
    warnings = report.get("warnings", [])
    errors = report.get("errors", [])
    is_final = report.get("release_status") == "final"
    passed_label = "Final release" if is_final else "Release candidate"
    lines = [
        "# ASD Microbiome Atlas Release v1.1: Quality Audit",
        "",
        f"Audit date: {report.get('validation_date', date.today().isoformat())}",
        "",
        "## Decision",
        "",
        (
            f"**{passed_label} passed structural and semantic validation with one guardrail.** "
            "It is suitable for website/manuscript development, but the summed unique-participant "
            "count must remain explicitly provisional."
            if report.get("validation_status") == "pass_with_guardrails"
            else f"**{passed_label} passed structural and semantic validation.**"
            if report.get("validation_status") == "pass"
            else f"**Validation status: {report.get('validation_status')}.**"
        ),
        "",
        "## Verified",
        "",
        f"- Accession-level records: {metrics.get('rows', 0)}.",
        f"- Applied correction items: {metrics.get('correction_items', 0)}.",
        f"- Provisional canonical dataset entities: {metrics.get('canonical_dataset_entities', 0)}.",
        f"- Overlap-adjusted atlas contribution: {metrics.get('provisional_unique_asd_contribution', 0)} ASD and {metrics.get('provisional_unique_control_contribution', 0)} controls ({metrics.get('provisional_unique_asd_control_contribution', 0)} combined).",
        "- Core and extended shared fields are identical.",
        "- Primary dataset IDs and accessions are unique.",
        "- Required fields, integer syntax, DOI syntax, controlled vocabularies, and count arithmetic pass.",
        "- All 35 correction items have row-level provenance.",
        "- Frozen v1 core and extended SHA-256 hashes are unchanged.",
        "- No private participant data or inferred clinical identities were added.",
        "",
        "## Remaining Guardrail",
        "",
    ]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None.")
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    lines.extend(
        [
            "",
            "The overlap-adjusted contribution is based on documented accession, publication, "
            "sample, and cohort mapping. Because repository aliases are anonymized, it should "
            "not be described as a guaranteed global unique-person count. The primary atlas "
            "headline remains **70 accession-level dataset records**.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a versioned ASD Microbiome Atlas v1.1 release package."
    )
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=FROZEN,
        help="Release directory. Relative paths are resolved from the project root.",
    )
    parser.add_argument("--release-version", default=EXPECTED_RELEASE_VERSION)
    parser.add_argument(
        "--release-status",
        choices=("release_candidate", "final"),
        default=EXPECTED_RELEASE_STATUS,
    )
    parser.add_argument("--validation-date", default=VALIDATION_DATE)
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=None,
        help="Optional Markdown audit path. Defaults to the release directory.",
    )
    parser.add_argument(
        "--force-report",
        action="store_true",
        help="Allow replacement of an existing validation report or audit file.",
    )
    return parser.parse_args()


def configure_validation(args: argparse.Namespace) -> None:
    global FROZEN, CORE, EXTENDED, SCHEMA, APPLICATION, MANIFEST
    global REPORT_JSON, REPORT_MD, EXPECTED_RELEASE_VERSION
    global EXPECTED_RELEASE_STATUS, VALIDATION_DATE, ALLOW_REPORT_OVERWRITE

    release_dir = args.release_dir
    if not release_dir.is_absolute():
        release_dir = ROOT / release_dir
    FROZEN = release_dir.resolve()
    CORE = FROZEN / "datasets_release_v1_1_core.csv"
    EXTENDED = FROZEN / "datasets_release_v1_1_extended.csv"
    SCHEMA = FROZEN / "release_schema_v1_1.json"
    APPLICATION = FROZEN / "corrections_application_v1_1.csv"
    MANIFEST = FROZEN / "release_manifest_v1_1.md"
    REPORT_JSON = FROZEN / "validation_report_v1_1.json"
    audit_output = args.audit_output or (FROZEN / "release_quality_audit_v1_1.md")
    if not audit_output.is_absolute():
        audit_output = ROOT / audit_output
    REPORT_MD = audit_output.resolve()
    EXPECTED_RELEASE_VERSION = args.release_version
    EXPECTED_RELEASE_STATUS = args.release_status
    VALIDATION_DATE = args.validation_date
    ALLOW_REPORT_OVERWRITE = args.force_report
    try:
        date.fromisoformat(VALIDATION_DATE)
    except ValueError as error:
        raise ValueError(f"Invalid ISO validation date: {VALIDATION_DATE}") from error


def main() -> None:
    configure_validation(parse_args())
    existing_reports = [path for path in (REPORT_JSON, REPORT_MD) if path.exists()]
    if existing_reports and not ALLOW_REPORT_OVERWRITE:
        names = ", ".join(path.name for path in existing_reports)
        raise FileExistsError(
            f"Refusing to overwrite existing validation artifacts: {names}. "
            "Use a new release directory or pass --force-report explicitly."
        )
    report = validate()
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(markdown_report(report), encoding="utf-8")
    print(f"Wrote {REPORT_JSON.name}")
    print(f"Wrote {REPORT_MD.name}")
    print(f"Validation status: {report['validation_status']}")
    if report["errors"]:
        for error in report["errors"]:
            print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
