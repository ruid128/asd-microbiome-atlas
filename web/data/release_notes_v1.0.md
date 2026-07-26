# ASD Microbiome Atlas Release Notes v1.0

Release date: 2026-06-05

## Scope

This release contains a curated atlas of human ASD/control microbiome datasets suitable for publication-facing summary tables and downstream web-service development.

The release is dataset-oriented rather than article-oriented. Each row represents a curated dataset/accession-level record retained after screening, de-duplication, manual adjudication, and extraction QC.

## Canonical files

- `datasets_release_v1_core.csv`
  - canonical public-facing release file
- `datasets_release_v1_extended.csv`
  - companion file with additional sparse metadata
- `datasets_release_v1_manifest.md`
  - release structure and field-selection rationale
- `release_schema_v1.json`
  - machine-readable schema used by validator
- `validate_release_v1.py`
  - validation script
- `validation_report_v1.json`
  - saved validation output for this release

## Source of truth

This release was generated from the internal curated master:

- `Prisma Workflow/проверка пройдена 1/Data_Extraction_Template_v1.csv`

The master curation file remains internal and was not replaced by the release files.

## Release summary

- total datasets: 69
- core release columns: 24
- extended release columns: 33
- paper-linked datasets: 62
- repository-only datasets: 7
- accepted exceptions retained in QC context: 2

## Accepted exceptions

### SCR00147 / PRJNA686821

Retained as a valid paper-linked public dataset. The linked paper reports 146 children (72 ASD, 74 TD), while the currently exposed public accession contains only 128 runs/BioSamples. The row is retained as a dataset-level exception because the accession is valid and explicitly linked by the paper, but the currently public subset is smaller than the paper cohort.

### SCR00180 / PRJNA895487

Retained as an aggregated multi-omic dataset accession. The accession contains 16S, shotgun metagenomic, shotgun metatranscriptomic, and metabolomic stool data and is linked to multiple related publications. The row is retained because the accession is a valid human ASD/control resource, but it should not be interpreted as a single-assay study row.

## Design decisions for release

1. Fully empty columns were removed.
2. Internal workflow/admin columns were removed.
3. `dataset_id` was set to `screening_id`.
4. `n_total` was retained when present and otherwise deterministically derived from participant counts.
5. `canonical_accession` was omitted because it matched `accession` in all rows.
6. `release_class` was added to distinguish standard rows from accepted exceptions.

## Known limitations

- Some repository-only datasets have blank `doi`, `pmid`, and `linked_publications` because no reliable publication linkage was identified.
- Two rows remain as accepted exceptions due to accession-level complexity rather than unresolved extraction errors.
- `sequencing_platform` remains blank for two repository-only rows because no reliable platform metadata were publicly exposed.
- `gut` and `stool` are not forced into one label; `gut` is retained only where source metadata were too general to justify a `stool` normalization.

