# ASD Microbiome Atlas v1.1

This directory is the immutable final data package for ASD Microbiome Atlas
v1.1, released on 2026-09-18 from a data snapshot dated 2026-07-22.

The release contains 70 accession-level records mapping to 64 provisional
canonical dataset entities. It reports an overlap-adjusted contribution of
2,770 ASD participants and 2,187 controls (4,957 combined). This subtotal is
not guaranteed to represent globally unique participants because anonymized
cross-study overlap can remain undetectable.

The core and extended CSV files are the canonical data tables. The JSON schema
is the machine-readable data dictionary and defines field types, required and
nullable fields, controlled vocabularies, and null semantics. Validation and
provenance records are supplied with the package.

Primary sequence files are not redistributed. They remain hosted by the
originating repositories and are subject to the terms and conditions of those
repositories and data submitters.

## Version and citation

- Release version: `v1.1`
- Recommended GitHub tag: `v1.1.0`
- Release date: `2026-09-18`
- Project website: https://ruid128.github.io/asd-microbiome-atlas/
- Source repository: https://github.com/ruid128/asd-microbiome-atlas
- DOI archive: not assigned

Use the citation metadata in `CITATION.cff`. After the associated article is
published, cite the article together with the exact GitHub release version used
for analysis.

## Integrity

Run `py -3.10 code\verify_release_v1_1.py` from this directory. The verifier
checks `SHA256SUMS.txt`, table structure, release labels, canonical mapping,
correction counts, and overlap-adjusted contribution metrics. Any change to a
listed file creates a different release and must not retain the `v1.1.0` tag.
