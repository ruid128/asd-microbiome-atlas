# ASD Microbiome Atlas Release Notes v1.1

Status: **final**, immutable publication release.

Release date: 2026-09-18.

Data snapshot date: 2026-07-22.

## Release summary

- Accession-level records: 70
- Provisional canonical dataset entities: 64
- Records with verified publication linkage: 63
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

## Material changes from v1

- Added `SCR00124 / PRJNA533120` as an overlapping resequencing release. Public
  metadata identify 82 records: 41 ASD and 41 neurotypical controls. Only its
  distinct B-series contribution is included in overlap-adjusted counts.
- Corrected `SCR00158 / PRJNA744027` to Liu et al. 2023 and resolved 101
  longitudinal BioSamples/runs to 24 ASD recipients and 14 healthy donors.
- Corrected `SCR00048 / PRJNA1057995` to metadata-only because no public SRA or
  BioSample records were verified for the represented accession.
- Added explicit canonical-dataset mapping, overlap adjudication, and
  correction-provenance fields.
- Separated study-reported participant counts, public participant counts,
  BioSample counts, and run counts.
- Retained `SCR00180 / PRJNA895487` as an aggregated multi-omic and
  multi-publication resource rather than a single-assay record.

## Counting rule

Participant, BioSample, and run counts are not interchangeable. The
overlap-adjusted contribution is 2,770 ASD plus 2,187 controls, or 4,957
combined. It is not guaranteed to represent globally unique participants
because anonymized cross-study overlap can remain undetectable.

## Known limitations

- Seven repository records do not have a verified linked publication.
- A downloadable participant-resolved ASD/control pair is unavailable for 11
  records and uncertain for 4.
- Cross-study overlap can be adjudicated only when accession, publication,
  sample, or cohort relationships are documented.
- Inclusion indicates relevance and public discoverability under the stated
  criteria, not sequence quality, biological validity, or clinical utility.

## Distribution

The final package is intended for GitHub Release tag `v1.1.0`. No Zenodo or
other DOI-generating archive is assigned to this release.
