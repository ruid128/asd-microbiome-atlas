# ASD Atlas Release v1

## Canonical Release Files

- `datasets_release_v1_core.csv`
  - Canonical public-facing release file for manuscript tables, supplementary data, and the future web service.
  - Designed to be compact and low-sparsity.
- `datasets_release_v1_extended.csv`
  - Companion release file with additional sparse but useful metadata fields.
  - Intended for downstream curation, power users, and future API expansion.

## Source of Truth

Both release files were generated from:

- `Prisma Workflow/проверка пройдена 1/Data_Extraction_Template_v1.csv`

The master extraction file remains the internal curation source and was not replaced.

## Release Design Rules

1. Fully empty columns were excluded from release outputs.
2. Internal workflow/admin columns were excluded.
3. `n_total` was retained when present and otherwise derived as:
   - `n_asd + n_control + n_other`
   - with blank `n_other` treated as `0`
4. `screening_id` was promoted to `dataset_id` for release stability.
5. `canonical_accession` was dropped because it was identical to `accession` in all rows.

## Core vs Extended

### Core file includes

- stable dataset identifier
- accession/source information
- linked publication metadata
- country and study design
- participant counts
- normalized body site and assay type
- sequencing platform
- intervention/longitudinal flags
- raw-data availability
- release classification
- curator notes

### Extended file additionally includes

- linked accessions
- PMCID
- raw body-site and raw assay descriptors
- target region
- library layout
- intervention type
- timepoints
- BioSample metadata availability

## Release Classification

`release_class` values:

- `standard`
- `accepted_exception_public_subset_mismatch`
- `accepted_exception_aggregated_multiomic_dataset`

The two accepted exceptions retained in this release are:

- `SCR00147 / PRJNA686821`
  - valid linked dataset
  - public accession currently exposes a smaller subset than the linked paper cohort
- `SCR00180 / PRJNA895487`
  - valid human ASD/control dataset accession
  - aggregated multi-omic, multi-publication resource rather than a single-assay study row

## Columns Excluded from Release

### Fully empty in master

- `age_asd`
- `age_control`
- `antibiotic_metadata`
- `atlas_record_id`
- `behavioral_metadata`
- `case_definition_asd`
- `cohort_type`
- `control_definition`
- `diet_metadata`
- `gi_metadata`
- `medication_metadata`
- `microbiome_domain`
- `probiotic_metadata`
- `sex_asd`
- `sex_control`

### Internal workflow/admin fields

- `record_order`
- `screening_decision_frozen`
- `extraction_status`
- `extracted_by`
- `extraction_date`
- `qc_status`
- `qc_by`
- `host_species`
- `comparator_present`

