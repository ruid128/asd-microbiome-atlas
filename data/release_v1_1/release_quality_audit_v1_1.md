# ASD Microbiome Atlas Release v1.1: Quality Audit

Audit date: 2026-09-18

## Decision

**Final release passed structural and semantic validation.**

## Verified

- Accession-level records: 70.
- Applied correction items: 35.
- Provisional canonical dataset entities: 64.
- Overlap-adjusted atlas contribution: 2770 ASD and 2187 controls (4957 combined).
- Core and extended shared fields are identical.
- Primary dataset IDs and accessions are unique.
- Required fields, integer syntax, DOI syntax, controlled vocabularies, and count arithmetic pass.
- All 35 correction items have row-level provenance.
- Frozen v1 core and extended SHA-256 hashes are unchanged.
- No private participant data or inferred clinical identities were added.

## Remaining Guardrail

- None.

The overlap-adjusted contribution is based on documented accession, publication, sample, and cohort mapping. Because repository aliases are anonymized, it should not be described as a guaranteed global unique-person count. The primary atlas headline remains **70 accession-level dataset records**.
