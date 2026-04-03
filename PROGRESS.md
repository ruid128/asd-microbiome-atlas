# ASD Microbiome Atlas — Progress Log

## Session: 2026-04-02

### Phase 1: Systematic Search — COMPLETE

Searched 5 public databases for ASD microbiome sequencing datasets using
standardized queries defined in `config/search_config.yaml`.

| Database | Records found |
|---|---|
| NCBI BioProject / SRA | 183 |
| ENA | 243 |
| GEO | 19 |
| MGnify | 3 |
| Qiita | 6 |
| **Total** | **454** |

Results written to `data/search_results/<source>.csv`.

---

### Phase 2: Screening — COMPLETE

Applied inclusion criteria I1–I6 and exclusion criteria E1–E8 to all 454 records.
Initial pass (round 1) + resolution of 12 ambiguous "maybe" entries (round 2).

**Final screening decisions:**

| Decision | Count |
|---|---|
| Include | 93 |
| Exclude | 361 |
| Maybe (unresolved) | 0 |

**Exclusion breakdown:**

| Reason | Count |
|---|---|
| duplicate_dataset | 155 |
| non_human | 91 |
| not_microbiome_sequencing | 74 |
| not_asd | 23 |
| no_control_group | 16 |
| no_public_data_link | 1 |
| other | 1 |

Results written to `data/screening_log.csv` (PRISMA-compliant, 454 rows).

---

### Phase 3: Metadata Extraction — COMPLETE

Fetched detailed metadata for all 93 included datasets from BioProject landing
pages and linked publications. Fields normalized to controlled vocabularies
defined in `config/controlled_vocab.yaml`.

**Atlas summary (93 datasets):**

| Field | Stats |
|---|---|
| Body site | 89 stool, 3 oral, 1 gut |
| Sequencing type | 69 × 16S, 16 × shotgun, 8 × metagenome |
| Publications linked | 61/93 (65.6%) |
| Countries with data | 88/93 filled (94.6%) |
| n_asd / n_control filled | ~52% of datasets |

Results written to `data/datasets.csv` (93 rows, 23 columns).

---

### Phase 4: Quality Control — PASS

Validated `datasets.csv` and `screening_log.csv` against JSON schemas in
`schemas/`. All checks passed after fixing DS0089 (n_total corrected from 79
BioSamples to 38 unique subjects due to longitudinal timepoints).

Script: `python3 scripts/validate_data.py` → **PASS, 0 errors**

---

## Current State

| File | Status |
|---|---|
| `data/datasets.csv` | 93 curated datasets, ready for analysis |
| `data/screening_log.csv` | 454 PRISMA-valid screening records |
| `data/search_results/` | Raw hits per source (5 files) |

## What's Next

- Manual review of datasets flagged in notes (potential cohort overlaps, ITS mycobiome entries)
- Resolve ~32 datasets with no linked publication (n_asd/n_control unknown)
- Cross-dataset analysis
- Web interface for scientists to browse and access the atlas
