# PRISMA Summary v1

## Scope

This document fixes the auditable PRISMA-style screening summary for the ASD Microbiome Atlas frozen release v1.0.

It is intended for:
- website PRISMA flow
- release documentation
- manuscript drafting support

It is **not** a replacement for the full screening sheets or the frozen dataset release.

## Recommended PRISMA counts

### Databases searched

- BioProject
- GEO
- ENA
- MGnify
- Qiita

**Total databases searched: 5**

### Records identified from databases

- BioProject: 196
- GEO: 18
- ENA: 110
- MGnify: 3
- Qiita: 13

**Total records identified from databases: 340**

### Duplicate or linked-duplicate records removed before screening

**132**

### Records screened

**208**

### Records excluded at screening

- non_human: 65
- no_control_group: 27
- not_asd: 19
- not_microbiome_sequencing: 17
- duplicate_dataset: 3
- insufficient_metadata: 2
- other: 1

**Total records excluded at screening: 134**

### Records included after screening

**74**

### Records removed during accession-level curation and final QC

**5**

Removed after screening include:
- SCR00053 / PRJNA1085546
- SCR00142 / PRJNA644730
- SCR00154 / PRJNA715668
- SCR00181 / PRJNA910918
- SCR00190 / PRJNA952791

### Datasets included in final frozen atlas

**69**

## Recommended website PRISMA chain

1. Databases searched: 5
2. Records identified from databases: 340
3. Duplicate records removed: 132
4. Records screened: 208
5. Records excluded: 134
6. Records included after screening: 74
7. Records removed during final curation/QC: 5
8. Datasets included in final atlas release: 69

## Provenance

The counts above were reconstructed from the following local project files:

- [Combined_Retrieval_Summary_v1.md](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Prisma Workflow/Combined_Retrieval_Summary_v1.md>)
- [Final_Dedup_QC_Summary_v1.md](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Prisma Workflow/Final_Dedup_QC_Summary_v1.md>)
- [All_Database_Retrieval_Log_Reviewer_A_v1.csv](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Prisma Workflow/All_Database_Retrieval_Log_Reviewer_A_v1.csv>)
- [Main_Screening_Reviewer_A_v1.csv](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Prisma Workflow/проверка пройдена 1/Main_Screening_Reviewer_A_v1.csv>)
- [Screening_Candidate_Set_v1.csv](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Prisma Workflow/проверка пройдена 1/Screening_Candidate_Set_v1.csv>)
- [datasets_release_v1_core.csv](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Frozen/datasets_release_v1_core.csv>)

## Important interpretation notes

- The value **340** is the correct PRISMA retrieval count for the current project workflow because it reflects the merged database-level retrieval layer before cross-database exact deduplication.
- The retrieval log contains **23 query runs** and **689 summed query-level hits**, but those query-level hits are not PRISMA counts because the same record can appear in multiple queries within the same database.
- The old website values **454 / 155 / 299 / 93** should not be used as production PRISMA values for the frozen release.

## Limitations

- The auditable final screening decisions currently come from Reviewer_A screening sheets.
- [Main_Screening_Reviewer_B_v1.csv](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Prisma Workflow/проверка пройдена 1/Main_Screening_Reviewer_B_v1.csv>) does not contain completed final decisions.
- [Adjudication_Table_v1.0.csv](</C:/Users/rusla/Desktop/Ruslan/EB-1A/5. Публикации статей/ASD_atlas/Prisma Workflow/Adjudication_Table_v1.0.csv>) is currently a template, not a completed adjudication record.
- Therefore, these counts are suitable for website documentation and release notes, but any manuscript wording should avoid overstating a fully documented dual-independent adjudicated screening workflow unless additional files are completed.
