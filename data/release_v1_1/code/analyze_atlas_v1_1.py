from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Frozen_v1.1" / "datasets_release_v1_1_extended.csv"
VALIDATION = ROOT / "Frozen_v1.1" / "validation_report_v1_1.json"
OUTPUT_CSV = ROOT / "Manuscript" / "descriptive_statistics_v1_1.csv"
OUTPUT_MD = ROOT / "Manuscript" / "descriptive_statistics_v1_1.md"

EXPECTED_SOURCE_SHA256 = (
    "3cee4b050d9419005ded700b5116d1d2ab9cbdb4f17381587449b16ee7c75f6f"
)
EXPECTED_ACCESSION_RECORDS = 70
EXPECTED_CANONICAL_ENTITIES = 64
ANALYSIS_DATE = "2026-07-22"

DISTRIBUTION_FIELDS = (
    "source_db",
    "country",
    "body_site",
    "specimen_type",
    "assay_type",
    "sequencing_platform",
    "study_design",
    "raw_data_public",
    "biosample_metadata_available",
    "downloadable_asd_control_pair",
    "participant_resolved_raw_data",
    "record_status",
    "publication_link_status",
    "release_class",
    "count_as_independent_dataset",
    "count_in_unique_participant_total",
)

OUTPUT_FIELDS = (
    "analysis_level",
    "domain",
    "category",
    "count",
    "denominator",
    "percent",
    "unit",
    "counting_rule",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Malformed CSV rows: {path}")
    return reader.fieldnames, rows


def integer(value: str) -> int:
    return int(value) if value else 0


def percent(count: int, denominator: int) -> str:
    return f"{100 * count / denominator:.1f}" if denominator else ""


def append_metric(
    output: list[dict[str, str]],
    *,
    analysis_level: str,
    domain: str,
    category: str,
    count: int,
    denominator: int | None,
    unit: str,
    counting_rule: str,
) -> None:
    output.append(
        {
            "analysis_level": analysis_level,
            "domain": domain,
            "category": category,
            "count": str(count),
            "denominator": "" if denominator is None else str(denominator),
            "percent": "" if denominator is None else percent(count, denominator),
            "unit": unit,
            "counting_rule": counting_rule,
        }
    )


def add_distribution(
    output: list[dict[str, str]],
    rows: list[dict[str, str]],
    *,
    level: str,
    field: str,
    rule: str,
) -> None:
    counts = Counter(row[field].strip() or "not_reported" for row in rows)
    denominator = len(rows)
    for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold())):
        append_metric(
            output,
            analysis_level=level,
            domain=field,
            category=category,
            count=count,
            denominator=denominator,
            unit="records" if level == "accession_level" else "canonical_entities",
            counting_rule=rule,
        )


def add_multivalue_distribution(
    output: list[dict[str, str]],
    rows: list[dict[str, str]],
    *,
    level: str,
    field: str,
    domain: str,
    rule: str,
) -> None:
    counts: Counter[str] = Counter()
    for row in rows:
        categories = {
            value.strip()
            for value in row[field].split(";")
            if value.strip()
        }
        for category in categories:
            counts[category] += 1
    denominator = len(rows)
    for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold())):
        append_metric(
            output,
            analysis_level=level,
            domain=domain,
            category=category,
            count=count,
            denominator=denominator,
            unit="records" if level == "accession_level" else "canonical_entities",
            counting_rule=rule,
        )


def metric_index(metrics: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {
        (row["analysis_level"], row["domain"], row["category"]): row
        for row in metrics
    }


def metric_text(
    index: dict[tuple[str, str, str], dict[str, str]],
    level: str,
    domain: str,
    category: str,
) -> str:
    row = index[(level, domain, category)]
    return f"{row['count']} ({row['percent']}%)"


def distribution_table(
    metrics: list[dict[str, str]],
    *,
    level: str,
    domain: str,
) -> list[str]:
    selected = [
        row
        for row in metrics
        if row["analysis_level"] == level and row["domain"] == domain
    ]
    lines = ["| Category | n | % |", "|---|---:|---:|"]
    lines.extend(
        f"| {row['category'].replace('|', '/')} | {row['count']} | {row['percent']} |"
        for row in selected
    )
    return lines


def validate_source(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise ValueError("Unexpected source hash; review release changes before analysis")
    if len(rows) != EXPECTED_ACCESSION_RECORDS:
        raise ValueError(f"Expected 70 accession records, found {len(rows)}")
    if len({row["dataset_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate dataset_id")
    if len({row["accession"] for row in rows}) != len(rows):
        raise ValueError("Duplicate primary accession")

    by_id = {row["dataset_id"]: row for row in rows}
    unknown_canonical = sorted(
        row["canonical_dataset_id"]
        for row in rows
        if row["canonical_dataset_id"] not in by_id
    )
    if unknown_canonical:
        raise ValueError(f"Unknown canonical IDs: {unknown_canonical}")

    canonical_rows = [
        row for row in rows if row["dataset_id"] == row["canonical_dataset_id"]
    ]
    canonical_ids = {row["canonical_dataset_id"] for row in rows}
    if len(canonical_ids) != EXPECTED_CANONICAL_ENTITIES:
        raise ValueError(f"Expected 64 canonical entities, found {len(canonical_ids)}")
    if {row["dataset_id"] for row in canonical_rows} != canonical_ids:
        raise ValueError("Canonical representative rows are incomplete")

    unresolved = [
        row for row in rows if row["count_in_unique_participant_total"] == "uncertain"
    ]
    if unresolved:
        raise ValueError("Unexpected unresolved-record set")

    contribution_asd = sum(integer(row["unique_asd_contribution"]) for row in rows)
    contribution_control = sum(integer(row["unique_control_contribution"]) for row in rows)
    contribution_combined = sum(
        integer(row["unique_asd_control_contribution"]) for row in rows
    )
    if contribution_asd + contribution_control != contribution_combined:
        raise ValueError("Contribution arithmetic mismatch")

    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    if validation.get("validation_status") != "pass":
        raise ValueError("Release validation status is not pass")
    if validation.get("sha256", {}).get("extended") != EXPECTED_SOURCE_SHA256:
        raise ValueError("Validation report and analysis source hash differ")
    return canonical_rows


def build_metrics(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    canonical_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    levels = (
        (
            "accession_level",
            rows,
            "One count per accession-level atlas record.",
        ),
        (
            "canonical_level",
            canonical_rows,
            "One count per canonical representative where dataset_id equals canonical_dataset_id.",
        ),
    )

    for level, level_rows, rule in levels:
        append_metric(
            output,
            analysis_level=level,
            domain="atlas_size",
            category="all_records",
            count=len(level_rows),
            denominator=len(level_rows),
            unit="records" if level == "accession_level" else "canonical_entities",
            counting_rule=rule,
        )
        for field in DISTRIBUTION_FIELDS:
            add_distribution(output, level_rows, level=level, field=field, rule=rule)
        add_multivalue_distribution(
            output,
            level_rows,
            level=level,
            field="body_site",
            domain="body_site_component",
            rule=rule + " Multi-valued records may contribute to more than one category.",
        )
        add_multivalue_distribution(
            output,
            level_rows,
            level=level,
            field="specimen_type",
            domain="specimen_type_component",
            rule=rule + " Multi-valued records may contribute to more than one category.",
        )
        add_multivalue_distribution(
            output,
            level_rows,
            level=level,
            field="assay_layers",
            domain="assay_layer_component",
            rule=rule + " Multi-assay records may contribute to more than one category.",
        )

    for field in fieldnames:
        complete = sum(bool(row[field].strip()) for row in rows)
        append_metric(
            output,
            analysis_level="accession_level",
            domain="field_completeness",
            category=field,
            count=complete,
            denominator=len(rows),
            unit="records_with_nonblank_value",
            counting_rule="Blank means unknown, not curated, or not applicable; it never means zero.",
        )

    noncanonical = sum(row["dataset_id"] != row["canonical_dataset_id"] for row in rows)
    append_metric(
        output,
        analysis_level="crosswalk",
        domain="deduplication",
        category="noncanonical_accession_records",
        count=noncanonical,
        denominator=len(rows),
        unit="records",
        counting_rule="Records whose canonical_dataset_id differs from dataset_id.",
    )

    contribution_asd = sum(integer(row["unique_asd_contribution"]) for row in rows)
    contribution_control = sum(integer(row["unique_control_contribution"]) for row in rows)
    for category, count in (
        ("ASD", contribution_asd),
        ("control", contribution_control),
        ("ASD_and_control", contribution_asd + contribution_control),
    ):
        append_metric(
            output,
            analysis_level="overlap_adjusted",
            domain="participant_contribution",
            category=category,
            count=count,
            denominator=None,
            unit="participants",
            counting_rule=(
                "Sum of curated unique contribution fields after accession-level "
                "cohort-overlap adjudication."
            ),
        )
    return output


def build_report(metrics: list[dict[str, str]]) -> str:
    index = metric_index(metrics)
    accession_n = index[("accession_level", "atlas_size", "all_records")]["count"]
    canonical_n = index[("canonical_level", "atlas_size", "all_records")]["count"]
    overlap_asd = index[("overlap_adjusted", "participant_contribution", "ASD")]["count"]
    overlap_control = index[("overlap_adjusted", "participant_contribution", "control")]["count"]
    overlap_total = index[("overlap_adjusted", "participant_contribution", "ASD_and_control")]["count"]

    lines = [
        "# ASD Microbiome Atlas v1.1: Descriptive Statistics",
        "",
        f"Analysis date: {ANALYSIS_DATE}",
        f"Source SHA-256: `{EXPECTED_SOURCE_SHA256}`",
        "",
        "## Counting Units",
        "",
        f"The atlas contains **{accession_n} accession-level records** and "
        f"**{canonical_n} provisional canonical dataset entities**. Accession-level "
        "statistics describe repository discovery and data availability. Canonical-level "
        "statistics use the representative row for each mapped entity and avoid counting "
        "repository mirrors or alternate releases as separate entities.",
        "",
        "## Accession-Level Results",
        "",
        f"BioProject contributed {metric_text(index, 'accession_level', 'source_db', 'BioProject')} "
        f"records, Qiita {metric_text(index, 'accession_level', 'source_db', 'Qiita')}, and ENA "
        f"{metric_text(index, 'accession_level', 'source_db', 'ENA')}. China was the most "
        f"frequent study country ({metric_text(index, 'accession_level', 'country', 'China')}).",
        "",
        f"Stool was the normalized body-site label for "
        f"{metric_text(index, 'accession_level', 'body_site', 'stool')} records. The predominant "
        f"assay classification was 16S sequencing "
        f"({metric_text(index, 'accession_level', 'assay_type', '16S')}), followed by metagenome "
        f"sequencing ({metric_text(index, 'accession_level', 'assay_type', 'metagenome')}). "
        f"Case-control studies accounted for "
        f"{metric_text(index, 'accession_level', 'study_design', 'case_control')} records.",
        "",
        "### Data Source",
        "",
        *distribution_table(metrics, level="accession_level", domain="source_db"),
        "",
        "### Study Design",
        "",
        *distribution_table(metrics, level="accession_level", domain="study_design"),
        "",
        "### Body Site",
        "",
        *distribution_table(metrics, level="accession_level", domain="body_site"),
        "",
        "### Assay Type",
        "",
        *distribution_table(metrics, level="accession_level", domain="assay_type"),
        "",
        "## Data Availability",
        "",
        f"Public raw data were recorded for "
        f"{metric_text(index, 'accession_level', 'raw_data_public', 'yes')} records, and "
        f"BioSample-level metadata were available for "
        f"{metric_text(index, 'accession_level', 'biosample_metadata_available', 'yes')}. "
        f"A participant-resolved downloadable ASD/control pair was confirmed for "
        f"{metric_text(index, 'accession_level', 'downloadable_asd_control_pair', 'yes')} records; "
        f"it was unavailable for "
        f"{metric_text(index, 'accession_level', 'downloadable_asd_control_pair', 'no')} and "
        f"uncertain for {metric_text(index, 'accession_level', 'downloadable_asd_control_pair', 'unknown')}.",
        "",
        "### Downloadable ASD/Control Pair",
        "",
        *distribution_table(
            metrics,
            level="accession_level",
            domain="downloadable_asd_control_pair",
        ),
        "",
        "### Participant Resolution",
        "",
        *distribution_table(
            metrics,
            level="accession_level",
            domain="participant_resolved_raw_data",
        ),
        "",
        "## Canonical-Level Results",
        "",
        f"After cross-accession mapping, {canonical_n} canonical entities remained. "
        f"Among their representative records, public raw data were available for "
        f"{metric_text(index, 'canonical_level', 'raw_data_public', 'yes')}, and a confirmed "
        f"downloadable ASD/control pair was available for "
        f"{metric_text(index, 'canonical_level', 'downloadable_asd_control_pair', 'yes')}.",
        "",
        "## Overlap-Adjusted Participant Contribution",
        "",
        f"The overlap-adjusted contribution fields sum to **{overlap_asd} ASD** "
        f"and **{overlap_control} control** participants (**{overlap_total} combined**). "
        "This count reflects documented accession-level overlap adjudication. It is not a "
        "guaranteed global unique-person count because anonymized cross-study overlap may be "
        "undetectable.",
        "",
        "## Interpretation Rules",
        "",
        "- Percentages use the stated accession-level or canonical-level denominator.",
        "- Multi-valued body-site, specimen, and assay-layer categories may sum to more than 100%.",
        "- Blank values are treated as unknown or not applicable, never as zero.",
        "- No inferential statistical tests were performed; results are descriptive.",
        "- Participant, BioSample, and run counts are not interchangeable.",
        "",
    ]
    return "\n".join(lines)


def validate_metrics(metrics: list[dict[str, str]]) -> None:
    keys = [
        (row["analysis_level"], row["domain"], row["category"])
        for row in metrics
    ]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate descriptive-statistic key")

    for row in metrics:
        count = int(row["count"])
        if count < 0:
            raise ValueError(f"Negative metric count: {row}")
        if row["denominator"]:
            denominator = int(row["denominator"])
            if count > denominator:
                raise ValueError(f"Metric exceeds denominator: {row}")
            if row["percent"] != percent(count, denominator):
                raise ValueError(f"Metric percentage mismatch: {row}")

    expected_denominators = {
        "accession_level": EXPECTED_ACCESSION_RECORDS,
        "canonical_level": EXPECTED_CANONICAL_ENTITIES,
    }
    for level, denominator in expected_denominators.items():
        for domain in DISTRIBUTION_FIELDS:
            selected = [
                row
                for row in metrics
                if row["analysis_level"] == level and row["domain"] == domain
            ]
            if sum(int(row["count"]) for row in selected) != denominator:
                raise ValueError(f"Distribution does not sum to {denominator}: {level}/{domain}")

    index = metric_index(metrics)
    asd = int(index[("overlap_adjusted", "participant_contribution", "ASD")]["count"])
    control = int(index[("overlap_adjusted", "participant_contribution", "control")]["count"])
    combined = int(index[("overlap_adjusted", "participant_contribution", "ASD_and_control")]["count"])
    if asd + control != combined:
        raise ValueError("Overlap-adjusted participant metric arithmetic mismatch")


def write_metrics(metrics: list[dict[str, str]]) -> None:
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(metrics)


def main() -> None:
    fieldnames, rows = read_csv(SOURCE)
    canonical_rows = validate_source(rows)
    metrics = build_metrics(fieldnames, rows, canonical_rows)
    validate_metrics(metrics)
    write_metrics(metrics)
    OUTPUT_MD.write_text(build_report(metrics), encoding="utf-8")
    print(f"Wrote {OUTPUT_CSV.name}")
    print(f"Wrote {OUTPUT_MD.name}")
    print(f"Metrics: {len(metrics)}")


if __name__ == "__main__":
    main()
