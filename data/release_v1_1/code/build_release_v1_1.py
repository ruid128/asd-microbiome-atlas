from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Frozen" / "datasets_release_v1_extended.csv"
MAPPING = ROOT / "Manuscript" / "cohort_mapping_v1.csv"
CORRECTIONS = ROOT / "Manuscript" / "release_corrections_required_v1.csv"
OUTPUT_DIR = ROOT / "Frozen_v1.1"
CORE = OUTPUT_DIR / "datasets_release_v1_1_core.csv"
EXTENDED = OUTPUT_DIR / "datasets_release_v1_1_extended.csv"
SCHEMA = OUTPUT_DIR / "release_schema_v1_1.json"
APPLICATIONS = OUTPUT_DIR / "corrections_application_v1_1.csv"
MANIFEST = OUTPUT_DIR / "release_manifest_v1_1.md"

RELEASE_VERSION = "v1.1-rc1"
RELEASE_STATUS = "release_candidate"
SNAPSHOT_DATE = "2026-07-22"
RELEASE_DATE = ""
ALLOW_OVERWRITE = False

BASE_FIELDS = [
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
    "release_class",
    "notes",
]

ADDED_FIELDS = [
    "release_version",
    "release_status",
    "record_status",
    "publication_link_status",
    "candidate_publication_title",
    "candidate_doi",
    "candidate_pmid",
    "candidate_pmcid",
    "participant_count_scope",
    "article_count_status",
    "article_n_total",
    "article_n_asd",
    "article_n_control",
    "article_n_other",
    "recruited_count_status",
    "recruited_n_total",
    "recruited_n_asd",
    "recruited_n_control",
    "recruited_n_other",
    "public_count_status",
    "public_n_total",
    "public_n_asd",
    "public_n_control",
    "public_n_other",
    "n_mothers",
    "n_siblings",
    "n_donors",
    "n_other_diagnosis",
    "all_human_hosts_n",
    "public_biosample_count",
    "public_run_count",
    "raw_data_granularity",
    "participant_resolved_raw_data",
    "participant_resolution_source",
    "downloadable_asd_control_pair",
    "repeated_sampling",
    "repeated_assay",
    "specimen_type",
    "anatomical_site",
    "assay_layers",
    "archive_library_strategy",
    "archive_metadata_conflict",
    "canonical_dataset_id",
    "dataset_role",
    "participant_overlap",
    "count_as_independent_dataset",
    "count_in_unique_participant_total",
    "unique_asd_contribution",
    "unique_control_contribution",
    "unique_asd_control_contribution",
    "participant_count_basis",
    "mapping_status",
    "correction_issue_ids",
    "curator_evidence",
]

EXTENDED_FIELDS = BASE_FIELDS + ADDED_FIELDS
CORE_FIELDS = [
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
    "publication_link_status",
    "country",
    "study_design",
    "n_total",
    "n_asd",
    "n_control",
    "n_other",
    "participant_count_scope",
    "public_count_status",
    "public_n_total",
    "public_n_asd",
    "public_n_control",
    "body_site",
    "specimen_type",
    "anatomical_site",
    "assay_type",
    "assay_layers",
    "sequencing_platform",
    "raw_data_public",
    "raw_data_granularity",
    "participant_resolved_raw_data",
    "downloadable_asd_control_pair",
    "record_status",
    "release_class",
    "canonical_dataset_id",
    "dataset_role",
    "count_as_independent_dataset",
    "count_in_unique_participant_total",
    "unique_asd_contribution",
    "unique_control_contribution",
    "mapping_status",
    "correction_issue_ids",
    "notes",
    "release_version",
    "release_status",
]

APPLICATION_FIELDS = [
    "issue_id",
    "affected_record",
    "application_status",
    "implementation_fields",
    "implementation_note",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def merge_tokens(*values: str) -> str:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for token in value.split(";"):
            token = token.strip()
            if token and token not in seen:
                seen.add(token)
                result.append(token)
    return "; ".join(result)


def count_values(total: int, asd: int, control: int, other: int = 0) -> dict[str, str]:
    return {
        "article_n_total": str(total),
        "article_n_asd": str(asd),
        "article_n_control": str(control),
        "article_n_other": str(other) if other else "",
        "article_count_status": "verified",
    }


def public_values(
    total: int,
    asd: int | None = None,
    control: int | None = None,
    other: int | None = None,
) -> dict[str, str]:
    group_counts_known = asd is not None and control is not None
    return {
        "public_n_total": str(total),
        "public_n_asd": "" if asd is None else str(asd),
        "public_n_control": "" if control is None else str(control),
        "public_n_other": "" if not other else str(other),
        "public_count_status": (
            "verified_group_counts" if group_counts_known else "verified_total_only"
        ),
    }


ARTICLE_COUNTS = {
    "SCR00013": (80, 40, 40, 0),
    "SCR00015": (74, 43, 31, 0),
    "SCR00018": (60, 25, 35, 0),
    "SCR00020": (25, 11, 14, 0),
    "SCR00026": (92, 54, 38, 0),
    "SCR00041": (138, 96, 42, 0),
    "SCR00046": (68, 38, 30, 0),
    "SCR00054": (18, 9, 9, 0),
    "SCR00071": (46, 30, 16, 0),
    "SCR00082": (71, 38, 33, 0),
    "SCR00092": (429, 242, 133, 54),
    "SCR00109": (59, 32, 27, 0),
    "SCR00116": (178, 59, 30, 89),
    "SCR00132": (127, 77, 50, 0),
    "SCR00140": (50, 30, 20, 0),
    "SCR00150": (95, 23, 17, 55),
    "SCR00158": (38, 24, 14, 0),
    "SCR00159": (59, 30, 29, 0),
    "SCR00162": (76, 41, 35, 0),
    "SCR00180": (196, 98, 98, 0),
    "SCR00202": (8, 4, 4, 0),
}

RECRUITED_COUNTS = {
    "SCR00026": (93, 54, 39, 0),
    "SCR00159": (60, 30, 30, 0),
}

PUBLIC_OVERRIDES = {
    "SCR00013": (71, 40, 31, 0),
    "SCR00018": (58, 27, 31, 0),
    "SCR00046": (10, 10, 0, 0),
    "SCR00054": (18, 9, 9, 0),
    "SCR00071": (46, 30, 16, 0),
    "SCR00082": (76, None, None, None),
    "SCR00092": (423, None, None, None),
    "SCR00109": (59, 32, 27, 0),
    "SCR00118": (78, 55, 23, 0),
    "SCR00130": (96, 48, 48, 0),
    "SCR00140": (49, 29, 20, 0),
    "SCR00147": (128, None, None, None),
    "SCR00158": (38, 24, 14, 0),
    "SCR00162": (41, 41, 0, 0),
    "SCR00180": (196, 98, 98, 0),
    "SCR00194": (58, 30, 28, 0),
    "SCR00202": (8, 4, 4, 0),
}

PUBLIC_ARCHIVE_COUNTS = {
    "SCR00013": (71, 142),
    "SCR00041": (1, 2),
    "SCR00046": (10, 10),
    "SCR00054": (90, 90),
    "SCR00071": (92, 92),
    "SCR00082": (76, 76),
    "SCR00092": (423, 380),
    "SCR00109": (111, 111),
    "SCR00116": (1, 2),
    "SCR00118": (78, 98),
    "SCR00130": (1, 96),
    "SCR00140": (49, ""),
    "SCR00147": (128, 128),
    "SCR00150": (1, 104),
    "SCR00158": (101, 101),
    "SCR00162": (41, 41),
    "SCR00180": (483, 883),
    "SCR00194": (1, 58),
    "SCR00202": (16, 16),
}

TECHNICAL_OVERRIDES: dict[str, dict[str, str]] = {
    "SCR00006": {
        "raw_data_granularity": "participant_resolved_cross_registry",
        "participant_resolution_source": "gsa_sample_alias",
    },
    "SCR00013": {
        "assay_type": "multi_amplicon",
        "assay_layers": "16S; ITS1",
        "repeated_assay": "yes",
        "raw_data_granularity": "multi_assay_participant_resolved",
    },
    "SCR00041": {
        "raw_data_granularity": "pooled",
        "participant_resolved_raw_data": "no",
        "participant_resolution_source": "article_only",
        "downloadable_asd_control_pair": "no",
        "public_count_status": "not_participant_resolved",
    },
    "SCR00046": {
        "raw_data_granularity": "partial_public_subset",
        "participant_resolved_raw_data": "partial",
        "downloadable_asd_control_pair": "no",
    },
    "SCR00048": {
        "raw_data_public": "no",
        "raw_data_granularity": "metadata_only",
        "participant_resolved_raw_data": "no",
        "participant_resolution_source": "none",
        "downloadable_asd_control_pair": "no",
        "public_count_status": "not_available",
    },
    "SCR00054": {
        "raw_data_granularity": "participant_resolved_with_multisite_samples",
        "repeated_sampling": "yes",
        "specimen_type": "mucosal_biopsy",
        "anatomical_site": "antrum; distal_duodenum; terminal_ileum; right_colon; rectum",
    },
    "SCR00055": {
        "archive_library_strategy": "RNA-Seq",
        "archive_metadata_conflict": "ENA library_strategy conflicts with article 16S method",
    },
    "SCR00066": {
        "archive_library_strategy": "OTHER",
        "archive_metadata_conflict": "ENA library_strategy conflicts with article shotgun metagenome method",
    },
    "SCR00071": {
        "assay_type": "multi_amplicon",
        "assay_layers": "16S; ITS",
        "raw_data_granularity": "multi_assay_participant_resolved",
        "repeated_assay": "yes",
    },
    "SCR00082": {
        "raw_data_granularity": "participant_resolved_group_crosswalk_incomplete",
        "participant_resolved_raw_data": "partial",
        "participant_resolution_source": "article_and_unmapped_run_aliases",
        "downloadable_asd_control_pair": "unknown",
    },
    "SCR00086": {
        "raw_data_granularity": "metadata_only",
        "participant_resolved_raw_data": "no",
        "participant_resolution_source": "none",
        "downloadable_asd_control_pair": "no",
        "public_count_status": "not_available",
    },
    "SCR00092": {
        "raw_data_granularity": "incomplete_public_cohort",
        "participant_resolved_raw_data": "partial",
        "participant_resolution_source": "article_and_partial_biosamples",
        "downloadable_asd_control_pair": "unknown",
    },
    "SCR00109": {
        "raw_data_granularity": "participant_resolved_with_multisite_samples",
        "repeated_sampling": "yes",
        "specimen_type": "oral_sample",
        "anatomical_site": "saliva; dental_plaque",
    },
    "SCR00116": {
        "raw_data_granularity": "pooled",
        "participant_resolved_raw_data": "no",
        "participant_resolution_source": "article_only",
        "downloadable_asd_control_pair": "no",
        "public_count_status": "not_participant_resolved",
    },
    "SCR00118": {
        "assay_type": "multi_assay",
        "assay_layers": "16S; shotgun_metagenome",
        "raw_data_granularity": "multi_assay_participant_resolved",
        "repeated_assay": "yes",
    },
    "SCR00122": {
        "n_mothers": "15",
        "n_donors": "7",
        "all_human_hosts_n": "60",
    },
    "SCR00126": {
        "raw_data_granularity": "metadata_only",
        "participant_resolved_raw_data": "no",
        "participant_resolution_source": "biosample_metadata_only",
        "downloadable_asd_control_pair": "no",
        "public_count_status": "metadata_only",
    },
    "SCR00130": {
        "raw_data_granularity": "shared_biosample_run_resolved",
        "participant_resolution_source": "run_alias",
    },
    "SCR00132": {
        "target_region": "V4",
        "archive_library_strategy": "Targeted-Capture",
        "archive_metadata_conflict": "ENA library_strategy conflicts with article 16S amplicon method",
    },
    "SCR00147": {
        "raw_data_granularity": "partial_public_subset",
        "participant_resolved_raw_data": "partial",
        "participant_resolution_source": "public_subset_without_complete_group_crosswalk",
        "downloadable_asd_control_pair": "unknown",
    },
    "SCR00150": {
        "raw_data_granularity": "shared_biosample_group_unresolved",
        "participant_resolved_raw_data": "partial",
        "participant_resolution_source": "article_only_run_crosswalk_missing",
        "downloadable_asd_control_pair": "unknown",
        "public_count_status": "unresolved",
    },
    "SCR00158": {
        "record_status": "included",
        "publication_link_status": "verified",
        "raw_data_granularity": "participant_resolved_longitudinal_with_donor_controls",
        "participant_resolved_raw_data": "yes",
        "participant_resolution_source": "run_alias_article_and_supplement_crosswalk",
        "downloadable_asd_control_pair": "yes",
        "public_count_status": "verified_group_counts",
        "archive_library_strategy": "AMPLICON",
    },
    "SCR00162": {
        "raw_data_granularity": "partial_public_subset",
        "participant_resolved_raw_data": "partial",
        "downloadable_asd_control_pair": "no",
    },
    "SCR00180": {
        "assay_type": "multi_omic",
        "assay_layers": "16S; shotgun_metagenome; metatranscriptome; metabolomics",
        "raw_data_granularity": "longitudinal_multiomic",
        "participant_resolved_raw_data": "partial",
        "participant_resolution_source": "biosample_and_article_multiomic_mapping",
        "repeated_sampling": "yes",
        "repeated_assay": "yes",
    },
    "SCR00189": {
        "raw_data_granularity": "rolling_repository",
        "participant_resolved_raw_data": "partial",
        "participant_resolution_source": "paper_anchored_rolling_accession",
        "public_count_status": "rolling_accession_not_fixed",
    },
    "SCR00194": {
        "raw_data_granularity": "shared_biosample_run_resolved",
        "participant_resolution_source": "run_alias",
    },
    "SCR00202": {
        "body_site": "gut;oral",
        "specimen_type": "stool; oral_sample",
        "anatomical_site": "fecal; oral",
        "raw_data_granularity": "participant_resolved_with_multisite_samples",
        "repeated_sampling": "yes",
    },
}

REPEATED_SAMPLING_IDS = {
    "SCR00024",
    "SCR00040",
    "SCR00054",
    "SCR00077",
    "SCR00109",
    "SCR00135",
    "SCR00158",
    "SCR00163",
    "SCR00180",
    "SCR00202",
}

CORRECTION_IMPLEMENTATION = {
    "RC001": ("linked_accessions", "Added complementary ASD accession PRJNA518760."),
    "RC002": ("participant_count_scope;n_mothers;n_donors;all_human_hosts_n", "Separated primary child count from ancillary human hosts."),
    "RC003": ("new_record_SCR00124;participant_overlap;unique_contribution", "Added 82-record resequencing dataset and counted only its distinct B cohort."),
    "RC004": ("dataset_role;raw_data_granularity;participant_resolved_raw_data", "Marked BioSample metadata-only record."),
    "RC005": ("assay_layers;public_biosample_count;public_run_count;repeated_assay", "Represented 16S and shotgun layers without duplicating participants."),
    "RC006": ("article_n_*;public_n_*;downloadable_asd_control_pair", "Separated 68-person article cohort from ten public ASD records."),
    "RC007": ("article_n_*;public_n_*;downloadable_asd_control_pair", "Marked public ASD-only subset with no downloadable controls."),
    "RC008": ("canonical_dataset_id;participant_overlap;unique_contribution", "Encoded prior-cohort reuse and zero contribution for SCR00147."),
    "RC009": ("article_n_*;public_biosample_count;public_run_count;raw_data_granularity", "Separated 429-person article cohort from current public exposure."),
    "RC010": ("article_n_*;public_n_*;assay_layers;repeated_assay", "Separated article/public counts and bacterial/fungal assays."),
    "RC011": ("article_n_*;public_n_*;linked_accessions", "Stored article and repository group counts separately."),
    "RC012": ("article_n_*;public_n_*;public_biosample_count", "Stored 30/20 article and 29/20 public counts separately."),
    "RC013": ("raw_data_public;raw_data_granularity;record_status", "Corrected false-positive raw-data availability."),
    "RC014": ("raw_data_granularity;participant_resolved_raw_data;public_run_count", "Marked pooled release and two archive records."),
    "RC015": ("raw_data_granularity;participant_resolved_raw_data;public_run_count", "Marked pooled mother-child release."),
    "RC016": ("record_status;raw_data_granularity;public_count_status", "Marked awaiting-data BioProject metadata record."),
    "RC017": ("participant_resolution_source;public_n_*;public_run_count", "Resolved 96 participants from run aliases."),
    "RC018": ("participant_resolution_source;public_n_*;public_run_count", "Resolved 58 participants from run aliases."),
    "RC019": ("article_n_*;public_run_count;participant_resolution_source", "Preserved article cohort while blocking unsupported run labels."),
    "RC020": ("linked_accessions", "Added PRJCA020304 and CRA013154."),
    "RC021": ("canonical_dataset_id;dataset_role;unique_contribution", "Encoded complete cross-registry duplicate."),
    "RC022": ("article_n_*;linked_accessions;participant_count_basis", "Retained supplement-supported 43/31 and ERP104786."),
    "RC023": ("linked_accessions;target_region;library_layout", "Added ERP111721 and V3-V4 paired assay details."),
    "RC024": ("article_n_*;recruited_n_*", "Separated recruited 54/39 from analyzed 54/38."),
    "RC025": ("public_biosample_count;public_run_count;specimen_type;anatomical_site", "Encoded 18 participants and five GI biopsy sites."),
    "RC026": ("archive_library_strategy;archive_metadata_conflict", "Preserved article 16S classification and exposed ENA conflict."),
    "RC027": ("archive_library_strategy;archive_metadata_conflict", "Preserved shotgun classification and exposed ENA conflict."),
    "RC028": ("assay_type;assay_layers;public_run_count;repeated_assay", "Encoded paired 16S/ITS records for 46 participants."),
    "RC029": ("article_n_*;public_n_total;public_run_count;participant_resolution_source", "Kept five extra archive records diagnostically unassigned."),
    "RC030": ("public_n_*;public_biosample_count;anatomical_site;repeated_sampling", "Encoded 59 participants across 111 saliva/plaque samples."),
    "RC031": ("target_region;archive_library_strategy;archive_metadata_conflict", "Preserved V4 16S method and exposed archive conflict."),
    "RC032": ("publication_link_status;n_*;public_n_*;n_donors;longitudinal_fields;sequencing_platform;unique_contribution", "Replaced the incorrect Ye et al. linkage with Liu et al. 2023 and resolved 101 records to 24 ASD recipients plus 14 healthy donors."),
    "RC033": ("article_n_*;recruited_n_*", "Separated recruited 30/30 from analyzed 30/29."),
    "RC034": ("assay_type;assay_layers;public_biosample_count;public_run_count;repeated_sampling", "Encoded 196-person longitudinal multi-omic structure."),
    "RC035": ("linked_accessions;body_site;public_n_*;public_biosample_count;repeated_sampling", "Exposed existing PRJNA1433220 link and fecal/oral repeated samples in core/API fields."),
}


def default_added(row: dict[str, str], mapping: dict[str, str]) -> dict[str, str]:
    role = mapping["dataset_role"]
    if role in {"bioproject_metadata_only", "repository_metadata_only"}:
        record_status = "metadata_only"
    elif mapping["count_as_independent_dataset"] == "no":
        record_status = "repository_mirror_or_alternate_release"
    elif mapping["count_in_unique_participant_total"] in {"uncertain", "pending_review"}:
        record_status = "awaiting_verification"
    elif mapping["count_in_unique_participant_total"] == "partial":
        record_status = "included_partial_public"
    else:
        record_status = "included"

    if row["paper_verified"] == "yes":
        publication_link_status = "verified"
    else:
        publication_link_status = "not_linked"

    if role in {"bioproject_metadata_only", "repository_metadata_only"}:
        granularity = "metadata_only"
        participant_resolved = "no"
        resolution_source = "none"
    elif role == "pooled_raw_release":
        granularity = "pooled"
        participant_resolved = "no"
        resolution_source = "article_only"
    elif role == "participant_runs_shared_biosample":
        granularity = "shared_biosample_run_resolved"
        participant_resolved = "yes"
        resolution_source = "run_alias"
    elif role in {"aggregated_repository_record", "primary_multi_amplicon"}:
        granularity = "multi_assay_participant_resolved"
        participant_resolved = "yes"
        resolution_source = "biosample"
    elif role == "aggregated_longitudinal_multiomic":
        granularity = "longitudinal_multiomic"
        participant_resolved = "partial"
        resolution_source = "biosample_and_article_multiomic_mapping"
    elif role == "primary_public_subset":
        granularity = "partial_public_subset"
        participant_resolved = "partial"
        resolution_source = "biosample_or_run_alias"
    else:
        granularity = "participant_resolved"
        participant_resolved = "yes"
        resolution_source = "biosample"

    raw_public = row["raw_data_public"] == "yes"
    downloadable_pair = "yes" if raw_public and participant_resolved == "yes" else "no"
    if not raw_public:
        public_count_status = "not_available"
    elif participant_resolved == "no":
        public_count_status = "not_participant_resolved"
    else:
        public_count_status = "verified_group_counts"

    specimen_type = {
        "stool": "stool",
        "gut": "gastrointestinal_sample_unspecified",
        "oral": "oral_sample",
        "other": "mixed_or_other",
    }.get(row["body_site"], "mixed_or_other")

    result = {field: "" for field in ADDED_FIELDS}
    result.update(
        {
            "release_version": RELEASE_VERSION,
            "release_status": RELEASE_STATUS,
            "record_status": record_status,
            "publication_link_status": publication_link_status,
            "participant_count_scope": mapping["participant_count_scope"],
            "article_count_status": (
                "not_curated" if row["paper_verified"] == "yes" else "not_applicable"
            ),
            "recruited_count_status": "not_curated",
            "public_count_status": public_count_status,
            "raw_data_granularity": granularity,
            "participant_resolved_raw_data": participant_resolved,
            "participant_resolution_source": resolution_source,
            "downloadable_asd_control_pair": downloadable_pair,
            "repeated_sampling": (
                "yes" if row["dataset_id"] in REPEATED_SAMPLING_IDS else "no"
            ),
            "repeated_assay": "no",
            "specimen_type": specimen_type,
            "anatomical_site": row["body_site"],
            "assay_layers": row["assay_type"],
            "canonical_dataset_id": mapping["canonical_dataset_id"],
            "dataset_role": role,
            "participant_overlap": mapping["participant_overlap"],
            "count_as_independent_dataset": mapping["count_as_independent_dataset"],
            "count_in_unique_participant_total": mapping[
                "count_in_unique_participant_total"
            ],
            "unique_asd_contribution": mapping["unique_asd_contribution"],
            "unique_control_contribution": mapping["unique_control_contribution"],
            "unique_asd_control_contribution": mapping[
                "unique_asd_control_contribution"
            ],
            "participant_count_basis": mapping["participant_count_basis"],
            "mapping_status": mapping["mapping_status"],
            "curator_evidence": mapping["evidence"],
        }
    )
    if public_count_status == "verified_group_counts":
        result.update(
            public_values(
                int(row["n_total"]),
                int(row["n_asd"]),
                int(row["n_control"]),
                int(row["n_other"] or 0),
            )
        )
    return result


def new_scr00124() -> tuple[dict[str, str], dict[str, str]]:
    row = {field: "" for field in BASE_FIELDS}
    row.update(
        {
            "dataset_id": "SCR00124",
            "source_db": "BioProject",
            "accession": "PRJNA533120",
            "dataset_title": "16S rRNA MiSeq resequencing of two Arizona ASD/NT cohorts",
            "url": "https://www.ncbi.nlm.nih.gov/bioproject/PRJNA533120",
            "linked_accessions": "SRP192904; PRJNA168470",
            "linked_publications": "Kang et al. 2013; Kang et al. 2018",
            "publication_title": "Resequencing release combining the Kang 2013 and fecal-metabolite cohorts",
            "paper_verified": "yes",
            "country": "United States",
            "study_design": "case_control",
            "n_total": "82",
            "n_asd": "41",
            "n_control": "41",
            "body_site": "stool",
            "assay_type": "16S",
            "assay_type_raw": "AMPLICON",
            "sequencing_platform": "Illumina MiSeq",
            "library_layout": "PAIRED",
            "intervention_flag": "no",
            "longitudinal_flag": "no",
            "biosample_metadata_available": "yes",
            "raw_data_public": "yes",
            "release_class": "accepted_exception_overlapping_resequencing",
            "notes": (
                "Public BioSample host_phenotype gives 41 ASD and 41 NT records. "
                "The 39 P-series records reproduce SCR00100 (19 ASD/20 NT); the "
                "43 B-series records are a distinct public cohort (22 ASD/21 NT)."
            ),
        }
    )
    mapping = {
        "participant_count_scope": "public_repository_participant_records",
        "canonical_dataset_id": "SCR00124",
        "dataset_role": "overlapping_resequencing_release",
        "participant_overlap": "contains_scr00100_p_series_plus_distinct_b_series",
        "count_as_independent_dataset": "yes",
        "count_in_unique_participant_total": "partial",
        "unique_asd_contribution": "22",
        "unique_control_contribution": "21",
        "unique_asd_control_contribution": "43",
        "participant_count_basis": "ena_82_biosamples_41_asd_41_nt_minus_scr00100_p_series",
        "mapping_status": "confirmed_overlapping_resequencing_components",
        "evidence": (
            "ENA SRP192904 exposes 82 unique paired MiSeq BioSamples. Official "
            "host_phenotype attributes classify 41 ASD and 41 NT. P-series aliases "
            "exactly reproduce the 19/20 SCR00100 cohort; B-series aliases contain "
            "22 ASD and 21 NT records and add 43 public participants."
        ),
        "curator_notes": "Count only the B-series contribution; retain all 82 records for download.",
        "related_accessions": "SRP192904; PRJNA168470",
    }
    return row, mapping


def apply_special_cases(row: dict[str, str], added: dict[str, str]) -> None:
    dataset_id = row["dataset_id"]
    if dataset_id in ARTICLE_COUNTS:
        added.update(count_values(*ARTICLE_COUNTS[dataset_id]))
    if dataset_id in RECRUITED_COUNTS:
        total, asd, control, other = RECRUITED_COUNTS[dataset_id]
        added.update(
            {
                "recruited_count_status": "verified",
                "recruited_n_total": str(total),
                "recruited_n_asd": str(asd),
                "recruited_n_control": str(control),
                "recruited_n_other": str(other) if other else "",
            }
        )
    if dataset_id in PUBLIC_OVERRIDES:
        added.update(public_values(*PUBLIC_OVERRIDES[dataset_id]))
    if dataset_id in PUBLIC_ARCHIVE_COUNTS:
        biosamples, runs = PUBLIC_ARCHIVE_COUNTS[dataset_id]
        added["public_biosample_count"] = str(biosamples)
        added["public_run_count"] = str(runs)
    added.update(TECHNICAL_OVERRIDES.get(dataset_id, {}))

    if dataset_id in {"SCR00150", "SCR00189"}:
        # These accessions do not currently support a fixed, participant-level
        # ASD/control composition of the public archive.
        for field in ("public_n_total", "public_n_asd", "public_n_control", "public_n_other"):
            added[field] = ""

    if dataset_id == "SCR00020":
        row["target_region"] = "V3-V4"
        row["library_layout"] = "PAIRED"
    if dataset_id == "SCR00158":
        row["linked_publications"] = "Liu et al. 2023"
        row["publication_title"] = (
            "Fresh Washed Microbiota Transplantation Alters Gut Microbiota "
            "Metabolites to Ameliorate Sleeping Disorder Symptom of Autistic Children"
        )
        row["doi"] = "10.1007/s12275-023-00069-x"
        row["pmid"] = "37665552"
        row["pmcid"] = ""
        row["paper_verified"] = "yes"
        row["study_design"] = "intervention"
        row["n_total"] = "38"
        row["n_asd"] = "24"
        row["n_control"] = "14"
        row["n_other"] = ""
        row["assay_type_raw"] = "AMPLICON"
        row["target_region"] = ""
        row["sequencing_platform"] = "Illumina MiniSeq"
        row["library_layout"] = "PAIRED"
        row["intervention_flag"] = "yes"
        row["intervention_type"] = "fresh washed microbiota transplantation"
        row["longitudinal_flag"] = "yes"
        row["timepoints"] = "ASD baseline; WMT1; WMT2; WMT3; WMT4"
        row["notes"] = (
            "Liu et al. 2023 explicitly links PRJNA744027 in Data Availability. "
            "NCBI/ENA expose 101 paired-end MiniSeq 16S amplicon runs from stool: "
            "87 records resolve to 24 ASD recipients across baseline and up to four "
            "post-WMT groups (24/24/18/13/8), and 14 NO-coded singleton records "
            "resolve to the healthy-donor comparator group. Count 24 ASD and 14 "
            "healthy donors once; donors are not documented as age-matched TD controls."
        )
        added.update(
            {
                "participant_count_scope": "unique_asd_recipients_and_healthy_donors",
                "n_donors": "14",
                "all_human_hosts_n": "38",
            }
        )
    if dataset_id == "SCR00124":
        added.update(public_values(82, 41, 41, 0))
        added.update(
            {
                "public_biosample_count": "82",
                "public_run_count": "82",
                "article_count_status": "multiple_publications_not_combined",
                "record_status": "included_partial_overlap",
            }
        )


def build_schema() -> dict[str, object]:
    integer_fields = {
        field
        for field in EXTENDED_FIELDS
        if field.startswith(("n_", "article_n_", "recruited_n_", "public_n_"))
        or field in {
            "all_human_hosts_n",
            "public_biosample_count",
            "public_run_count",
            "unique_asd_contribution",
            "unique_control_contribution",
            "unique_asd_control_contribution",
        }
    }
    required = {
        "dataset_id",
        "source_db",
        "accession",
        "dataset_title",
        "url",
        "country",
        "study_design",
        "body_site",
        "assay_type",
        "raw_data_public",
        "release_class",
        "release_version",
        "release_status",
        "record_status",
        "publication_link_status",
        "participant_count_scope",
        "public_count_status",
        "raw_data_granularity",
        "participant_resolved_raw_data",
        "downloadable_asd_control_pair",
        "canonical_dataset_id",
        "dataset_role",
        "count_as_independent_dataset",
        "count_in_unique_participant_total",
        "mapping_status",
    }
    descriptions = {
        "n_total": "Primary harmonized study-level count; interpret with participant_count_scope.",
        "article_n_total": "Verified analyzed publication cohort total when separately curated.",
        "recruited_n_total": "Verified pre-QC recruited cohort total when distinct from analyzed data.",
        "public_n_total": "Verified unique public participant total, not BioSample or run count.",
        "public_biosample_count": "Current public BioSample count at the audit snapshot.",
        "public_run_count": "Current public sequencing run count at the audit snapshot.",
        "correction_issue_ids": "Semicolon-delimited correction tracker IDs applied to the row.",
        "curator_evidence": "Aggregate non-identifying evidence supporting cohort mapping.",
    }
    fields = {}
    for field in EXTENDED_FIELDS:
        fields[field] = {
            "type": "integer" if field in integer_fields else "string",
            "required": field in required,
            "nullable": field not in required,
            "description": descriptions.get(field, field.replace("_", " ").capitalize() + "."),
        }
    return {
        "release_version": RELEASE_VERSION,
        "release_status": RELEASE_STATUS,
        "snapshot_date": SNAPSHOT_DATE,
        "primary_key": "dataset_id",
        "expected_rows": 70,
        "null_policy": (
            "Blank numeric values mean unknown, not curated, or not applicable as "
            "specified by the adjacent status/scope field; blanks never mean zero."
        ),
        "core_fields": CORE_FIELDS,
        "extended_fields": EXTENDED_FIELDS,
        "fields": fields,
        "controlled_vocabularies": {
            "release_status": [RELEASE_STATUS],
            "record_status": [
                "included",
                "included_partial_public",
                "included_partial_overlap",
                "metadata_only",
                "repository_mirror_or_alternate_release",
                "awaiting_verification",
            ],
            "tri_state": ["yes", "no", "partial", "unknown"],
            "count_flag": ["yes", "no", "partial", "uncertain"],
            "publication_link_status": ["verified", "not_linked", "candidate_unverified"],
        },
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a versioned ASD Microbiome Atlas v1.1 release package."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Release output directory. Relative paths are resolved from the project root.",
    )
    parser.add_argument("--release-version", default=RELEASE_VERSION)
    parser.add_argument(
        "--release-status",
        choices=("release_candidate", "final"),
        default=RELEASE_STATUS,
    )
    parser.add_argument("--snapshot-date", default=SNAPSHOT_DATE)
    parser.add_argument(
        "--release-date",
        default=RELEASE_DATE,
        help="ISO release date. Required when --release-status final.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of release artifacts already present in the output directory.",
    )
    return parser.parse_args()


def configure_release(args: argparse.Namespace) -> None:
    global OUTPUT_DIR, CORE, EXTENDED, SCHEMA, APPLICATIONS, MANIFEST
    global RELEASE_VERSION, RELEASE_STATUS, SNAPSHOT_DATE, RELEASE_DATE
    global ALLOW_OVERWRITE

    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    OUTPUT_DIR = output_dir.resolve()
    CORE = OUTPUT_DIR / "datasets_release_v1_1_core.csv"
    EXTENDED = OUTPUT_DIR / "datasets_release_v1_1_extended.csv"
    SCHEMA = OUTPUT_DIR / "release_schema_v1_1.json"
    APPLICATIONS = OUTPUT_DIR / "corrections_application_v1_1.csv"
    MANIFEST = OUTPUT_DIR / "release_manifest_v1_1.md"
    RELEASE_VERSION = args.release_version
    RELEASE_STATUS = args.release_status
    SNAPSHOT_DATE = args.snapshot_date
    RELEASE_DATE = args.release_date
    ALLOW_OVERWRITE = args.force

    if RELEASE_STATUS == "final" and not RELEASE_DATE:
        raise ValueError("--release-date is required for a final release")
    for label, value in (("snapshot date", SNAPSHOT_DATE), ("release date", RELEASE_DATE)):
        if value:
            try:
                date.fromisoformat(value)
            except ValueError as error:
                raise ValueError(f"Invalid ISO {label}: {value}") from error


def main() -> None:
    configure_release(parse_args())
    source_rows = read_csv(SOURCE)
    mapping_rows = read_csv(MAPPING)
    correction_rows = read_csv(CORRECTIONS)
    if len(source_rows) != 69 or len(mapping_rows) != 69 or len(correction_rows) != 35:
        raise ValueError("Unexpected v1 source, mapping, or correction row count")

    mapping_by_id = {row["dataset_id"]: row for row in mapping_rows}
    correction_ids: dict[str, list[str]] = defaultdict(list)
    for correction in correction_rows:
        for dataset_id in correction["affected_record"].split(";"):
            correction_ids[dataset_id.strip()].append(correction["issue_id"])

    new_row, new_mapping = new_scr00124()
    source_rows.append(new_row)
    mapping_by_id["SCR00124"] = new_mapping

    output_rows: list[dict[str, str]] = []
    for source_row in sorted(source_rows, key=lambda row: row["dataset_id"]):
        row = dict(source_row)
        mapping = mapping_by_id[row["dataset_id"]]
        row["linked_accessions"] = merge_tokens(
            row["linked_accessions"], mapping.get("related_accessions", "")
        )
        if mapping.get("curator_notes"):
            row["notes"] = " | ".join(
                value for value in (row["notes"], mapping["curator_notes"]) if value
            )

        added = default_added(row, mapping)
        added["correction_issue_ids"] = "; ".join(
            correction_ids.get(row["dataset_id"], [])
        )
        apply_special_cases(row, added)
        row.update(added)
        output_rows.append(row)

    existing_artifacts = [
        path for path in (CORE, EXTENDED, SCHEMA, APPLICATIONS, MANIFEST) if path.exists()
    ]
    if existing_artifacts and not ALLOW_OVERWRITE:
        names = ", ".join(path.name for path in existing_artifacts)
        raise FileExistsError(
            f"Refusing to overwrite existing release artifacts in {OUTPUT_DIR}: {names}. "
            "Use a new output directory or pass --force explicitly."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(EXTENDED, output_rows, EXTENDED_FIELDS)
    write_csv(CORE, output_rows, CORE_FIELDS)

    applications = []
    correction_by_id = {row["issue_id"]: row for row in correction_rows}
    for issue_id in sorted(CORRECTION_IMPLEMENTATION):
        fields, note = CORRECTION_IMPLEMENTATION[issue_id]
        applications.append(
            {
                "issue_id": issue_id,
                "affected_record": correction_by_id[issue_id]["affected_record"],
                "application_status": "applied",
                "implementation_fields": fields,
                "implementation_note": note,
            }
        )
    write_csv(APPLICATIONS, applications, APPLICATION_FIELDS)

    SCHEMA.write_text(
        json.dumps(build_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    status_text = (
        "**final**, immutable publication release."
        if RELEASE_STATUS == "final"
        else "**release candidate**, not yet the final publication release."
    )
    release_date_text = (
        f"\nRelease date: {RELEASE_DATE}.\n" if RELEASE_DATE else ""
    )
    manifest = f"""# ASD Microbiome Atlas Release {RELEASE_VERSION}

Status: {status_text}
{release_date_text}
Data snapshot date: {SNAPSHOT_DATE}.

## Canonical files

- `datasets_release_v1_1_core.csv`: compact website/manuscript table ({len(output_rows)} rows).
- `datasets_release_v1_1_extended.csv`: complete curation and API table ({len(output_rows)} rows).
- `release_schema_v1_1.json`: field types, null policy, and controlled vocabularies.
- `corrections_application_v1_1.csv`: application record for all 35 v1 correction items.
- `validation_report_v1_1.json`: generated by `Manuscript/validate_release_v1_1.py`.
- `release_quality_audit_v1_1.md`: human-readable validation summary.

## Provenance

- Frozen v1 extended SHA-256: `{sha256(SOURCE)}`.
- Cohort mapping SHA-256: `{sha256(MAPPING)}`.
- Correction tracker SHA-256: `{sha256(CORRECTIONS)}`.
- Core v1.1 SHA-256: `{sha256(CORE)}`.
- Extended v1.1 SHA-256: `{sha256(EXTENDED)}`.
- Schema v1.1 SHA-256: `{sha256(SCHEMA)}`.
- Correction application SHA-256: `{sha256(APPLICATIONS)}`.

## Material changes from v1

- Added `SCR00124 / PRJNA533120` as an overlapping resequencing release.
- Separated study, article, recruited, public-participant, BioSample, and run counts.
- Added explicit raw-data granularity, participant-resolution, specimen, assay-layer,
  canonical-dataset, overlap, and correction-provenance fields.
- Corrected `SCR00158 / PRJNA744027` to Liu et al. 2023 and resolved its 101
  longitudinal/donor records to 24 ASD recipients and 14 healthy donors.
- Corrected `SCR00048` raw-data availability without altering Frozen v1.

## Counting rule

Do not sum `n_total`, `public_n_total`, BioSamples, or runs as interchangeable units.
Use `unique_asd_contribution` and `unique_control_contribution` only with the cohort
mapping. The resulting overlap-adjusted count is not a guaranteed global unique-person
count because anonymized cross-study overlap can remain undetectable.
"""
    MANIFEST.write_text(manifest, encoding="utf-8")

    print(f"Wrote {CORE.relative_to(ROOT)}")
    print(f"Wrote {EXTENDED.relative_to(ROOT)}")
    print(f"Wrote {SCHEMA.relative_to(ROOT)}")
    print(f"Wrote {APPLICATIONS.relative_to(ROOT)}")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")
    print(f"Rows: {len(output_rows)}")


if __name__ == "__main__":
    main()
