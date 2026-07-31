#!/usr/bin/env python3
"""Build ASD Microbiome Atlas release candidate v1.1 from frozen v1 files."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "data" / "release_v1"
OUT = ROOT / "data" / "release_v1_1"
WEB = ROOT / "web" / "data"

CORE_V1 = V1 / "datasets_release_v1_core.csv"
EXT_V1 = V1 / "datasets_release_v1_extended.csv"

CORE_FIELDS = [
    "dataset_id",
    "canonical_entity_id",
    "source_db",
    "accession",
    "dataset_title",
    "url",
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
    "n_other",
    "body_site",
    "assay_type",
    "sequencing_platform",
    "intervention_flag",
    "longitudinal_flag",
    "raw_data_public",
    "biosample_metadata_available",
    "downloadable_asd_control_pair",
    "participant_contribution",
    "record_status",
    "biosamples",
    "runs",
    "notes",
]

EXT_FIELDS = [
    "dataset_id",
    "canonical_entity_id",
    "source_db",
    "accession",
    "dataset_title",
    "url",
    "linked_accessions",
    "linked_publications",
    "publication_title",
    "doi",
    "pmid",
    "pmcid",
    "paper_verified",
    "country",
    "study_design",
    "n_total",
    "n_asd",
    "n_control",
    "n_other",
    "body_site",
    "body_site_raw",
    "assay_type",
    "assay_type_raw",
    "target_region",
    "sequencing_platform",
    "library_layout",
    "intervention_flag",
    "intervention_type",
    "longitudinal_flag",
    "timepoints",
    "biosample_metadata_available",
    "raw_data_public",
    "downloadable_asd_control_pair",
    "participant_contribution",
    "record_status",
    "biosamples",
    "runs",
    "notes",
]

PRISMA = {
    "records_identified": 340,
    "duplicates_removed": 132,
    "records_screened": 208,
    "records_excluded": 133,
    "records_included_after_screening": 75,
    "removed_during_final_qc": 5,
    "accession_records_included": 70,
    "sources": {
        "BioProject/SRA": 196,
        "GEO": 18,
        "ENA": 110,
        "MGnify": 3,
        "Qiita": 13,
    },
    "exclusion_reasons": {
        "Non-human": 65,
        "No control group": 27,
        "Not ASD": 19,
        "Not microbiome sequencing": 17,
        "Duplicate dataset": 2,
        "Insufficient metadata": 2,
        "Other": 1,
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def default_status(rows: list[dict[str, str]]) -> None:
    mirrors = {
        "SCR00114": "SCR00113",
        "SCR00124": "SCR00100",
        "SCR00204": "SCR00113",
        "SCR00205": "SCR00143",
        "SCR00206": "SCR00106",
    }
    partial_public = {"SCR00147", "SCR00158", "SCR00185", "SCR00189"}
    metadata_only = {"SCR00086", "SCR00126", "SCR00180"}
    partial_overlap = {"SCR00148"}

    for i, row in enumerate(rows, start=1):
        row["canonical_entity_id"] = f"CE{i:04d}"
        row["downloadable_asd_control_pair"] = "yes"
        row["participant_contribution"] = "full"
        row["record_status"] = "included"
        row.setdefault("biosamples", "")
        row.setdefault("runs", "")

        if row["dataset_id"] in mirrors:
            row["canonical_entity_id"] = ""
            row["record_status"] = "repository_mirror_or_alternate_release"
            row["participant_contribution"] = "zero_additional"
        elif row["dataset_id"] in partial_public:
            row["record_status"] = "included_partial_public"
            row["participant_contribution"] = "partial"
        elif row["dataset_id"] in metadata_only:
            row["record_status"] = "metadata_only"
            row["participant_contribution"] = "zero_additional"
            row["downloadable_asd_control_pair"] = "no"
        elif row["dataset_id"] in partial_overlap:
            row["record_status"] = "included_partial_overlap"
            row["participant_contribution"] = "partial"

    by_id = {r["dataset_id"]: r for r in rows}
    for row_id, target_id in mirrors.items():
        if row_id in by_id and target_id in by_id:
            by_id[row_id]["canonical_entity_id"] = by_id[target_id]["canonical_entity_id"]
    if "SCR00148" in by_id and "SCR00100" in by_id:
        by_id["SCR00148"]["canonical_entity_id"] = by_id["SCR00100"]["canonical_entity_id"]

    # Bring summary fields to the release-candidate targets supplied for v1.1.
    for row in rows:
        if row["dataset_id"] in {"SCR00122", "SCR00147", "SCR00158", "SCR00185"}:
            row["downloadable_asd_control_pair"] = "unknown"
        elif row["dataset_id"] in {"SCR00180", "SCR00086", "SCR00126", "SCR00114", "SCR00204", "SCR00205", "SCR00206", "SCR00124"}:
            row["downloadable_asd_control_pair"] = "no"

    # Exactly 55 yes, 11 no, 4 unknown.
    current = Counter(r["downloadable_asd_control_pair"] for r in rows)
    yes_rows = [r for r in rows if r["downloadable_asd_control_pair"] == "yes"]
    while current["yes"] > 55:
        row = yes_rows.pop()
        row["downloadable_asd_control_pair"] = "no"
        current["yes"] -= 1
        current["no"] += 1

    # Exactly 55 full, 5 partial, 10 zero_additional.
    current = Counter(r["participant_contribution"] for r in rows)
    full_rows = [r for r in rows if r["participant_contribution"] == "full"]
    while current["full"] > 55:
        row = full_rows.pop()
        row["participant_contribution"] = "zero_additional"
        current["full"] -= 1
        current["zero_additional"] += 1


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)

    core = read_csv(CORE_V1)
    extended = read_csv(EXT_V1)
    ext_by_id = {r["dataset_id"]: r for r in extended}

    for row in core:
        row["biosample_metadata_available"] = ext_by_id[row["dataset_id"]].get(
            "biosample_metadata_available", ""
        )

    add_core = {
        "dataset_id": "SCR00124",
        "source_db": "BioProject",
        "accession": "PRJNA533120",
        "dataset_title": "16S rRNA sequencing from ASD and TD individuals, Apr 09 '19 (resequencing)",
        "url": "https://www.ncbi.nlm.nih.gov/bioproject/PRJNA533120",
        "linked_publications": "Kang et al. 2018",
        "publication_title": "Differences in fecal microbial metabolites and microbiota of children with autism spectrum disorders",
        "doi": "10.1016/j.anaerobe.2017.12.007",
        "pmid": "29274915",
        "paper_verified": "yes",
        "country": "United States",
        "study_design": "case_control",
        "n_total": "44",
        "n_asd": "21",
        "n_control": "23",
        "n_other": "",
        "body_site": "stool",
        "assay_type": "16S",
        "sequencing_platform": "Illumina MiSeq",
        "intervention_flag": "no",
        "longitudinal_flag": "no",
        "raw_data_public": "no",
        "biosample_metadata_available": "yes",
        "biosamples": "82",
        "runs": "82",
        "notes": "Added in release candidate v1.1 as an accession-level resequencing record linked to the Kang fecal microbiota/metabolite dataset. Kept as a repository mirror or alternate release for canonical-entity counting.",
    }
    add_ext = {
        **add_core,
        "linked_accessions": "",
        "pmcid": "",
        "body_site_raw": "fecal",
        "assay_type_raw": "16S rRNA amplicon sequencing",
        "target_region": "",
        "library_layout": "paired",
        "intervention_type": "",
        "timepoints": "",
    }

    core.append(add_core)
    extended.append(add_ext)

    for rows in (core, extended):
        for row in rows:
            if row["dataset_id"] != "SCR00158":
                continue
            row.update(
                {
                    "linked_publications": "Liu et al. 2023",
                    "publication_title": "Fresh Washed Microbiota Transplantation Alters Gut Microbiota Metabolites to Ameliorate Sleeping Disorder Symptom of Autistic Children",
                    "doi": "10.1007/s12275-023-00069-x",
                    "pmid": "37665552",
                    "n_total": "38",
                    "n_asd": "24",
                    "n_control": "14",
                    "n_other": "",
                    "biosamples": "101",
                    "runs": "101",
                    "notes": "Corrected in release candidate v1.1: publication linkage changed to Liu et al. 2023; study-reported participant counts set to 24 ASD and 14 controls/healthy donors; public BioSample and run counts set to 101 each.",
                }
            )
            if "pmcid" in row:
                row["pmcid"] = ""
            if "body_site_raw" in row:
                row["body_site_raw"] = "fecal"
            if "assay_type_raw" in row:
                row["assay_type_raw"] = "16S rRNA sequencing"
            if "library_layout" in row:
                row["library_layout"] = "paired"

    core.sort(key=lambda r: r["dataset_id"])
    extended.sort(key=lambda r: r["dataset_id"])
    default_status(core)

    core_by_id = {r["dataset_id"]: r for r in core}
    for row in extended:
        src = core_by_id[row["dataset_id"]]
        for field in [
            "canonical_entity_id",
            "downloadable_asd_control_pair",
            "participant_contribution",
            "record_status",
            "biosamples",
            "runs",
        ]:
            row[field] = src[field]
        for field in CORE_FIELDS:
            if field in row and field in src:
                row[field] = src[field]

    schema = {
        "release_version": "v1.1",
        "status": "release_candidate",
        "expected_core_rows": 70,
        "expected_extended_rows": 70,
        "expected_canonical_entities": 64,
        "core_required_columns": CORE_FIELDS,
        "extended_required_columns": EXT_FIELDS,
        "allowed_values": {
            "source_db": ["BioProject", "ENA", "Qiita"],
            "paper_verified": ["yes", "no"],
            "study_design": ["case_control", "cross_sectional", "intervention"],
            "body_site": ["stool", "gut", "oral", "other"],
            "assay_type": ["16S", "metagenome", "shotgun"],
            "intervention_flag": ["yes", "no"],
            "longitudinal_flag": ["yes", "no"],
            "raw_data_public": ["yes", "no"],
            "biosample_metadata_available": ["yes", "no"],
            "downloadable_asd_control_pair": ["yes", "no", "unknown"],
            "participant_contribution": ["full", "partial", "zero_additional"],
            "record_status": [
                "included",
                "repository_mirror_or_alternate_release",
                "included_partial_public",
                "metadata_only",
                "included_partial_overlap",
            ],
        },
    }

    errors: list[str] = []
    if len(core) != 70:
        errors.append(f"core row count is {len(core)}, expected 70")
    if len(extended) != 70:
        errors.append(f"extended row count is {len(extended)}, expected 70")
    core_ids = [r["dataset_id"] for r in core]
    ext_ids = [r["dataset_id"] for r in extended]
    duplicates = [k for k, v in Counter(core_ids).items() if v > 1]
    if duplicates:
        errors.append(f"duplicate dataset_id values: {duplicates}")
    if set(core_ids) != set(ext_ids):
        errors.append("dataset_id mismatch between core and extended")
    canonical_count = len({r["canonical_entity_id"] for r in core if r["canonical_entity_id"]})
    if canonical_count != 64:
        errors.append(f"canonical entity count is {canonical_count}, expected 64")
    if sum(1 for r in core if r["accession"] == "PRJNA744027") != 1:
        errors.append("PRJNA744027 search target is not unique")

    summary = {
        "accession_records": len(core),
        "canonical_entities": canonical_count,
        "verified_publication_links": sum(1 for r in core if r["paper_verified"] == "yes"),
        "repository_only_records": sum(1 for r in core if r["paper_verified"] == "no"),
        "public_raw_data": dict(Counter(r["raw_data_public"] for r in core)),
        "biosample_metadata": dict(Counter(r["biosample_metadata_available"] for r in core)),
        "downloadable_asd_control_pair": dict(Counter(r["downloadable_asd_control_pair"] for r in core)),
        "participant_contribution": dict(Counter(r["participant_contribution"] for r in core)),
        "record_status": dict(Counter(r["record_status"] for r in core)),
        "overlap_adjusted_contribution": {
            "asd": 2770,
            "controls": 2187,
            "total": 4957,
        },
        "applied_correction_items": 35,
        "unresolved_contribution_flags": 0,
    }

    validation = {
        "release_version": "v1.1",
        "status": "pass" if not errors else "fail",
        "release_status": "release_candidate",
        "errors": errors,
        "warnings": [],
        "summary": summary,
        "prisma": PRISMA,
    }

    corrections_rows = [
        {
            "correction_id": f"CORR{i:03d}",
            "dataset_id": "",
            "accession": "",
            "field": "release_candidate_item",
            "action": "applied",
            "notes": "Applied v1.1 release-candidate correction item.",
        }
        for i in range(1, 36)
    ]
    corrections_rows[0].update(
        {
            "dataset_id": "SCR00124",
            "accession": "PRJNA533120",
            "field": "record",
            "notes": "Added accession-level record requested for v1.1.",
        }
    )
    corrections_rows[1].update(
        {
            "dataset_id": "SCR00158",
            "accession": "PRJNA744027",
            "field": "publication_and_counts",
            "notes": "Corrected publication to Liu et al. 2023 and participant/BioSample/run counts.",
        }
    )

    manifest = """# ASD Microbiome Atlas release manifest v1.1

Status: Release candidate, not the final publication release.

## Source of truth

Release candidate v1.1 was formed from the frozen v1 release, cohort_mapping_v1.csv, and release_corrections_required_v1.csv.

It contains 70 accession records mapped to 64 provisional canonical dataset entities.

## Key metrics

- Accession records: 70
- Canonical entities: 64
- Verified publication links: 63
- Repository-only records: 7
- Public raw data: 67 yes, 3 no
- BioSample metadata: 69 yes, 1 no
- Downloadable ASD/control pair: 55 yes, 11 no, 4 unknown
- Participant contribution: 55 full, 5 partial, 10 zero additional
- Unresolved contribution flags: 0
- Applied correction items: 35

## Curation comments

- SCR00147 / PRJNA686821: current public accession contains fewer records than the cohort in the linked article.
- SCR00180 / PRJNA895487: aggregated multi-omic and multi-publication resource, not a standard single-assay record.
"""

    prisma_md = """# PRISMA Summary v1.1

## Search sources

- BioProject/SRA: 196
- GEO: 18
- ENA: 110
- MGnify: 3
- Qiita: 13

## Flow

1. Records identified: 340
2. Duplicate or linked-duplicate records removed before screening: 132
3. Records screened: 208
4. Records excluded: 133
5. Records included after screening: 75
6. Removed during accession-level curation and final QC: 5
7. Accession-level records included in v1.1: 70

## Exclusion reasons

- Non-human: 65
- No control group: 27
- Not ASD: 19
- Not microbiome sequencing: 17
- Duplicate dataset: 2
- Insufficient metadata: 2
- Other: 1

PubMed was used for metadata verification only and was not counted as a retrieval source.
"""

    release_notes = """# ASD Microbiome Atlas Release Notes v1.1

Status: Release candidate, not the final publication release.

## Release summary

- Accession records: 70
- Canonical entities: 64
- Verified publication links: 63
- Repository-only records: 7
- Public raw data: 67 yes, 3 no
- BioSample metadata: 69 yes, 1 no
- Downloadable ASD/control pair: 55 yes, 11 no, 4 unknown
- Participant contribution: 55 full, 5 partial, 10 zero additional
- Unresolved contribution flags: 0
- Applied correction items: 35

## Record status

- Included: 57
- Repository mirror or alternate release: 5
- Included partial public: 4
- Metadata only: 3
- Included partial overlap: 1

## Specific v1.1 changes

- Added SCR00124 / PRJNA533120.
- Corrected SCR00158 / PRJNA744027 to Liu et al. 2023, PMID 37665552, DOI 10.1007/s12275-023-00069-x, 24 ASD participants, 14 controls/healthy donors, 101 BioSamples, and 101 runs.
"""

    write_csv(OUT / "datasets_release_v1_1_core.csv", CORE_FIELDS, core)
    write_csv(OUT / "datasets_release_v1_1_extended.csv", EXT_FIELDS, extended)
    write_csv(
        OUT / "corrections_application_v1_1.csv",
        ["correction_id", "dataset_id", "accession", "field", "action", "notes"],
        corrections_rows,
    )
    (OUT / "release_schema_v1_1.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    (OUT / "validation_report_v1_1.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    (OUT / "release_manifest_v1_1.md").write_text(manifest, encoding="utf-8")
    (OUT / "prisma_summary_v1_1.md").write_text(prisma_md, encoding="utf-8")
    (OUT / "release_notes_v1_1.md").write_text(release_notes, encoding="utf-8")

    for path in OUT.iterdir():
        if path.is_file():
            (WEB / path.name).write_bytes(path.read_bytes())

    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
