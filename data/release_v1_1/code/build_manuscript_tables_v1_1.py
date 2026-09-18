from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Frozen_v1.1" / "datasets_release_v1_1_extended.csv"
STATISTICS = ROOT / "Manuscript" / "descriptive_statistics_v1_1.csv"
OUTPUT_DIR = ROOT / "Manuscript" / "Tables_v1_1"

EXPECTED_SOURCE_SHA256 = (
    "3cee4b050d9419005ded700b5116d1d2ab9cbdb4f17381587449b16ee7c75f6f"
)
EXPECTED_STATISTICS_SHA256 = (
    "733a3ea22fb5cb3f2942e7a05fbed26d42b9292a570163994416b3af258993f3"
)
ACCESSION_N = 70
CANONICAL_N = 64

TABLE_FILES = (
    "Table_1_atlas_characteristics_v1_1.md",
    "Table_2_data_availability_v1_1.md",
    "Table_S1_dataset_catalog_v1_1.md",
    "Table_S2_canonical_mapping_v1_1.md",
    "Table_S3_metadata_completeness_v1_1.md",
    "Table_S4_PRISMA_counts_v1_1.md",
)

DISPLAY_CATEGORIES = {
    "yes": "Yes",
    "no": "No",
    "partial": "Partial",
    "unknown": "Unknown",
    "case_control": "Case-control",
    "cross_sectional": "Cross-sectional",
    "intervention": "Intervention",
    "stool": "Stool",
    "oral": "Oral",
    "gut": "Gut",
    "gut;oral": "Gut and oral",
    "metagenome": "Metagenome",
    "multi_amplicon": "Multi-amplicon",
    "multi_assay": "Multi-assay",
    "multi_omic": "Multi-omic",
    "shotgun": "Shotgun",
    "verified": "Verified",
    "not_linked": "Not linked",
    "candidate_unverified": "Candidate, unverified",
    "included": "Included",
    "repository_mirror_or_alternate_release": "Repository mirror or alternate release",
    "included_partial_public": "Included, partial public release",
    "metadata_only": "Metadata only",
    "awaiting_verification": "Awaiting verification",
    "included_partial_overlap": "Included, partial cohort overlap",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Malformed CSV: {path}")
    return rows


def md(value: str, *, missing: str = "NR") -> str:
    text = value.strip() if value else ""
    if not text:
        return missing
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def display_category(value: str) -> str:
    return DISPLAY_CATEGORIES.get(value, value)


def write_table(filename: str, lines: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / filename).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def statistics_index(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str, str], dict[str, str]]:
    index = {
        (row["analysis_level"], row["domain"], row["category"]): row
        for row in rows
    }
    if len(index) != len(rows):
        raise ValueError("Duplicate descriptive-statistic key")
    return index


def categories_for_domain(
    rows: list[dict[str, str]], domain: str
) -> list[str]:
    accession = [
        row
        for row in rows
        if row["analysis_level"] == "accession_level" and row["domain"] == domain
    ]
    canonical_only = sorted(
        {
            row["category"]
            for row in rows
            if row["analysis_level"] == "canonical_level" and row["domain"] == domain
        }
        - {row["category"] for row in accession},
        key=str.casefold,
    )
    return [row["category"] for row in accession] + canonical_only


def paired_distribution_rows(
    statistics: list[dict[str, str]],
    index: dict[tuple[str, str, str], dict[str, str]],
    domains: tuple[tuple[str, str], ...],
) -> list[str]:
    lines: list[str] = []
    for domain, label in domains:
        categories = categories_for_domain(statistics, domain)
        for position, category in enumerate(categories):
            accession = index.get(("accession_level", domain, category))
            canonical = index.get(("canonical_level", domain, category))
            lines.append(
                "| "
                + " | ".join(
                    (
                        label if position == 0 else "",
                        md(display_category(category), missing="Not reported"),
                        accession["count"] if accession else "0",
                        accession["percent"] if accession else "0.0",
                        canonical["count"] if canonical else "0",
                        canonical["percent"] if canonical else "0.0",
                    )
                )
                + " |"
            )
    return lines


def build_table_1(
    statistics: list[dict[str, str]],
    index: dict[tuple[str, str, str], dict[str, str]],
) -> list[str]:
    domains = (
        ("source_db", "Data source"),
        ("study_design", "Study design"),
        ("body_site", "Normalized body site"),
        ("assay_type", "Assay classification"),
        ("country", "Study country"),
    )
    return [
        "# Table 1. Characteristics of ASD microbiome atlas records",
        "",
        "| Characteristic | Category | Accession records, n | Accession records, % | Canonical entities, n | Canonical entities, % |",
        "|---|---|---:|---:|---:|---:|",
        *paired_distribution_rows(statistics, index, domains),
        "",
        f"*Denominators are {ACCESSION_N} accession-level records and {CANONICAL_N} canonical representative entities. Categories correspond directly to the controlled atlas values; the combined `gut;oral` category is displayed as `Gut and oral`.*",
    ]


def build_table_2(
    statistics: list[dict[str, str]],
    index: dict[tuple[str, str, str], dict[str, str]],
) -> list[str]:
    domains = (
        ("raw_data_public", "Public raw data"),
        ("biosample_metadata_available", "BioSample metadata available"),
        ("participant_resolved_raw_data", "Participant resolution"),
        ("downloadable_asd_control_pair", "Downloadable ASD/control pair"),
        ("publication_link_status", "Publication linkage"),
        ("record_status", "Curation status"),
    )
    return [
        "# Table 2. Public data availability and curation status",
        "",
        "| Characteristic | Category | Accession records, n | Accession records, % | Canonical entities, n | Canonical entities, % |",
        "|---|---|---:|---:|---:|---:|",
        *paired_distribution_rows(statistics, index, domains),
        "",
        "*Canonical-level values use the representative record for each mapped entity. `Unknown` denotes unresolved availability; it is not equivalent to `no`. Participant, BioSample, and sequencing-run counts are not interchangeable.*",
    ]


def build_table_s1(rows: list[dict[str, str]]) -> list[str]:
    columns = (
        ("dataset_id", "Dataset ID"),
        ("accession", "Accession"),
        ("source_db", "Source"),
        ("dataset_title", "Dataset title"),
        ("country", "Country"),
        ("study_design", "Design"),
        ("n_total", "Total n"),
        ("n_asd", "ASD n"),
        ("n_control", "Control n"),
        ("n_other", "Other n"),
        ("body_site", "Body site"),
        ("specimen_type", "Specimen"),
        ("assay_type", "Assay"),
        ("sequencing_platform", "Platform"),
        ("raw_data_public", "Raw data public"),
        ("downloadable_asd_control_pair", "ASD/control pair"),
        ("publication_link_status", "Publication link"),
        ("doi", "DOI"),
        ("pmid", "PMID"),
        ("canonical_dataset_id", "Canonical ID"),
        ("record_status", "Record status"),
        ("url", "Repository URL"),
    )
    lines = [
        "# Supplementary Table S1. Accession-level ASD microbiome dataset catalog",
        "",
        "| " + " | ".join(label for _, label in columns) + " |",
        "|" + "|".join("---" if index < 6 else "---:" if index < 10 else "---" for index, _ in enumerate(columns)) + "|",
    ]
    for row in sorted(rows, key=lambda item: item["dataset_id"]):
        lines.append("| " + " | ".join(md(row[field]) for field, _ in columns) + " |")
    lines.extend(
        [
            "",
            "*NR indicates not reported, unresolved, or not applicable and never denotes zero. Counts follow `participant_count_scope` in the extended release; repository BioSample and run counts are not shown as participant counts. `Other n` is heterogeneous and may include mothers, siblings, donors, or participants with other diagnoses.*",
        ]
    )
    return lines


def build_table_s2(rows: list[dict[str, str]]) -> list[str]:
    columns = (
        ("dataset_id", "Dataset ID"),
        ("accession", "Accession"),
        ("canonical_dataset_id", "Canonical ID"),
        ("dataset_role", "Dataset role"),
        ("participant_overlap", "Participant overlap"),
        ("count_as_independent_dataset", "Independent dataset"),
        ("count_in_unique_participant_total", "Contribution flag"),
        ("unique_asd_contribution", "ASD contribution"),
        ("unique_control_contribution", "Control contribution"),
        ("unique_asd_control_contribution", "Combined contribution"),
        ("mapping_status", "Mapping status"),
    )
    lines = [
        "# Supplementary Table S2. Canonical mapping and overlap-adjusted contributions",
        "",
        "| " + " | ".join(label for _, label in columns) + " |",
        "|" + "|".join("---" if index < 7 or index == 10 else "---:" for index, _ in enumerate(columns)) + "|",
    ]
    for row in sorted(rows, key=lambda item: item["dataset_id"]):
        lines.append("| " + " | ".join(md(row[field]) for field, _ in columns) + " |")

    asd = sum(int(row["unique_asd_contribution"] or 0) for row in rows)
    control = sum(int(row["unique_control_contribution"] or 0) for row in rows)
    lines.extend(
        [
            "",
            f"*The overlap-adjusted fields sum to {asd} ASD and {control} control participants ({asd + control} combined). This count reflects documented accession-level cohort adjudication; anonymized cross-study overlap may remain undetectable, so it is not a guaranteed global unique-person count.*",
        ]
    )
    return lines


def build_table_s3(
    statistics: list[dict[str, str]],
) -> list[str]:
    selected_fields = (
        "dataset_id",
        "accession",
        "dataset_title",
        "country",
        "study_design",
        "n_total",
        "n_asd",
        "n_control",
        "body_site",
        "specimen_type",
        "assay_type",
        "sequencing_platform",
        "raw_data_public",
        "biosample_metadata_available",
        "public_n_total",
        "publication_title",
        "doi",
        "pmid",
        "downloadable_asd_control_pair",
        "participant_resolved_raw_data",
        "canonical_dataset_id",
        "mapping_status",
        "notes",
    )
    complete = {
        row["category"]: row
        for row in statistics
        if row["analysis_level"] == "accession_level"
        and row["domain"] == "field_completeness"
    }
    lines = [
        "# Supplementary Table S3. Completeness of key atlas metadata fields",
        "",
        "| Field | Complete, n | Complete, % | Missing, n | Missing, % |",
        "|---|---:|---:|---:|---:|",
    ]
    for field in selected_fields:
        row = complete[field]
        count = int(row["count"])
        missing = ACCESSION_N - count
        lines.append(
            f"| {field} | {count} | {row['percent']} | {missing} | {100 * missing / ACCESSION_N:.1f} |"
        )
    lines.extend(
        [
            "",
            "*Completeness means a nonblank curated value. Blank values indicate unknown, not curated, or not applicable according to the adjacent status field; they are not converted to zero.*",
        ]
    )
    return lines


def build_table_s4() -> list[str]:
    exclusion_reasons = (
        ("Non-human", 65),
        ("No control group", 27),
        ("Not ASD", 19),
        ("Not microbiome sequencing", 17),
        ("Duplicate dataset", 2),
        ("Insufficient metadata", 2),
        ("Other", 1),
    )
    excluded = sum(count for _, count in exclusion_reasons)
    identified = 340
    duplicates_removed = 132
    screened = 208
    included_after_screening = 75
    final_qc_removed = 5
    final_atlas = 70
    if identified - duplicates_removed != screened:
        raise ValueError("PRISMA identification arithmetic mismatch")
    if screened - excluded != included_after_screening:
        raise ValueError("PRISMA screening arithmetic mismatch")
    if included_after_screening - final_qc_removed != final_atlas:
        raise ValueError("PRISMA final-QC arithmetic mismatch")

    lines = [
        "# Supplementary Table S4. PRISMA-informed dataset identification and selection counts",
        "",
        "| Stage | Item | Count, n |",
        "|---|---|---:|",
        "| Identification | Databases searched | 5 |",
        "| Identification | Records identified | 340 |",
        "| Deduplication | Duplicate or linked-duplicate records removed before screening | 132 |",
        "| Screening | Records screened | 208 |",
        f"| Screening | Records excluded | {excluded} |",
    ]
    lines.extend(
        f"| Exclusion reason | {reason} | {count} |"
        for reason, count in exclusion_reasons
    )
    lines.extend(
        [
            f"| Eligibility | Records included after screening | {included_after_screening} |",
            f"| Final curation | Records removed during accession-level curation and QC | {final_qc_removed} |",
            f"| Included | Accession-level records in atlas v1.1 | {final_atlas} |",
            "",
            "*The five searched databases were BioProject/SRA, GEO, ENA, MGnify, and Qiita. PubMed was used only for metadata verification. Relative to v1.0, `SCR00124 / PRJNA533120` was restored after re-adjudication, reducing duplicate-dataset exclusions from three to two and increasing the final atlas from 69 to 70 records.*",
        ]
    )
    return lines


def validate_outputs() -> None:
    expected_data_rows = {
        TABLE_FILES[0]: 35,
        TABLE_FILES[1]: 17,
        TABLE_FILES[2]: 70,
        TABLE_FILES[3]: 70,
        TABLE_FILES[4]: 23,
        TABLE_FILES[5]: 15,
    }
    for filename in TABLE_FILES:
        path = OUTPUT_DIR / filename
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# ") or "|" not in text:
            raise ValueError(f"Malformed Markdown table: {filename}")
        normalized = text.casefold()
        if "| none |" in normalized or "| nan |" in normalized:
            raise ValueError(f"Invalid placeholder in table: {filename}")
        data_rows = [line for line in text.splitlines() if line.startswith("| ")][1:]
        if len(data_rows) != expected_data_rows[filename]:
            raise ValueError(
                f"Unexpected data-row count in {filename}: {len(data_rows)}"
            )


def main() -> None:
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise ValueError("Frozen v1.1 source hash changed")
    if sha256(STATISTICS) != EXPECTED_STATISTICS_SHA256:
        raise ValueError("Descriptive statistics hash changed")

    source_rows = read_csv(SOURCE)
    statistics = read_csv(STATISTICS)
    if len(source_rows) != ACCESSION_N:
        raise ValueError(f"Expected {ACCESSION_N} source rows")
    if len({row["canonical_dataset_id"] for row in source_rows}) != CANONICAL_N:
        raise ValueError(f"Expected {CANONICAL_N} canonical entities")

    index = statistics_index(statistics)
    tables = {
        TABLE_FILES[0]: build_table_1(statistics, index),
        TABLE_FILES[1]: build_table_2(statistics, index),
        TABLE_FILES[2]: build_table_s1(source_rows),
        TABLE_FILES[3]: build_table_s2(source_rows),
        TABLE_FILES[4]: build_table_s3(statistics),
        TABLE_FILES[5]: build_table_s4(),
    }
    for filename, lines in tables.items():
        write_table(filename, lines)
    validate_outputs()
    for filename in TABLE_FILES:
        print(f"Wrote {filename}")


if __name__ == "__main__":
    main()
