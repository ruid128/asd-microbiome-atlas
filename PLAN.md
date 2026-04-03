# ASD Microbiome Atlas — Work Plan

## Goal

Build a systematized, PRISMA-compliant catalog of public human ASD microbiome
sequencing datasets with unified metadata, suitability scoring, and a
reproducible screening pipeline — ready for cross-dataset meta-analysis.

---

## Phase 1: Systematic Search (databases → raw hits)

| Step | Action |
|------|--------|
| 1.1  | Define standardized search queries per database (see `config/search_config.yaml`) |
| 1.2  | Run exhaustive searches across **BioProject / SRA**, **ENA**, **GEO**, **MGnify**, **Qiita** |
| 1.3  | Record every hit in `data/search_results/<source>.csv` with accession, title, date |
| 1.4  | Log search parameters (query, date, result count) for PRISMA reproducibility |

**Deliverable:** Raw hit lists per source database.

---

## Phase 2: Screening (raw hits → include / exclude / maybe)

| Step | Action |
|------|--------|
| 2.1  | Apply **inclusion criteria I1–I6** and **exclusion criteria E1–E8** to each hit |
| 2.2  | Record decision (`include` / `exclude` / `maybe`) + reason in `data/screening_log.csv` |
| 2.3  | Resolve all `maybe` entries (check BioSample, linked papers) |
| 2.4  | Cross-check for duplicates across sources (E5) |

**Deliverable:** Completed `screening_log.csv` with PRISMA-valid audit trail.

---

## Phase 3: Metadata Extraction & Normalization (included → datasets.csv)

| Step | Action |
|------|--------|
| 3.1  | For each included dataset, extract metadata into `data/datasets.csv` |
| 3.2  | Normalize body site, sequencing type, age group to controlled vocabularies |
| 3.3  | Retrieve sample counts (n_asd, n_control) from BioSample / paper |
| 3.4  | Link PubMed IDs and DOIs where available |

**Deliverable:** Curated `datasets.csv` with unified schema.

---

## Phase 4: Quality Control & Validation

| Step | Action |
|------|--------|
| 4.1  | Validate `datasets.csv` and `screening_log.csv` against JSON schemas |
| 4.2  | Check completeness (unknown fields, missing accessions) |
| 4.3  | Generate PRISMA flow counts (identified → screened → eligible → included) |
| 4.4  | Produce summary statistics (by body site, seq type, year, country) |

**Deliverable:** Validated data + PRISMA flow numbers.

---

## Phase 5: Publication & Dissemination (future)

| Step | Action |
|------|--------|
| 5.1  | Generate PRISMA flow diagram |
| 5.2  | Build static web page for atlas browsing |
| 5.3  | Publish dataset + methodology through conferences / preprint |

---

## Agent Architecture Summary

```
                    ┌─────────────┐
                    │ Orchestrator│
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           v               v               v
   ┌──────────────┐ ┌─────────────┐ ┌────────────┐
   │ Search Agent │ │  Screening  │ │  Metadata  │
   │ (per source) │ │   Agent     │ │   Agent    │
   └──────────────┘ └─────────────┘ └────────────┘
                                           │
                                    ┌──────┴──────┐
                                    │  QC Agent   │
                                    └─────────────┘
```

Each agent has a dedicated prompt in `prompts/` and operates on
shared CSV data files in `data/`.
