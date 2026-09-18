# Reproducibility code

This directory contains the project-authored Python scripts used for release
construction, structural and semantic validation, descriptive analysis,
manuscript-table generation, and Figure 2 generation. It also contains the
recorded prompts used to specify Figures 1-3.

The final CSV and JSON artifacts in the parent directory are authoritative.
The archived build, analysis, table, and original validation scripts retain the
paths used in the complete project workspace. In particular, the original
validator also checks the separately preserved frozen v1 source. These scripts
are included for provenance and exact workflow disclosure, not as a claim that
all upstream curation inputs are duplicated inside this release package.

For a standalone integrity and release-metric check, run this command from the
release directory:

```powershell
py -3.10 code\verify_release_v1_1.py
```

This command is read-only and does not replace release files.
