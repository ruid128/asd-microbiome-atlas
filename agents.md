# ASD Microbiome Atlas — Agent Architecture

## Overview

The atlas is built by a team of specialized Claude Code agents coordinated by
an orchestrator. Each agent has a single responsibility and communicates
through shared data files (CSV/YAML) in the `data/` directory.

---

## Agents

### 1. Orchestrator

| Property | Value |
|----------|-------|
| Prompt   | `prompts/orchestrator.md` |
| Role     | Workflow coordinator |
| Inputs   | `PLAN.md`, `config/*`, current state of `data/*` |
| Outputs  | Task assignments, progress tracking, final reports |

**Responsibilities:**
- Sequence work phases (search → screening → metadata → QC)
- Launch worker agents with correct parameters
- Monitor progress and resolve blockers
- Aggregate results and generate summary reports

---

### 2. Search Agent

| Property | Value |
|----------|-------|
| Prompt   | `prompts/search_agent.md` |
| Role     | Database searcher |
| Inputs   | `config/search_config.yaml` |
| Outputs  | `data/search_results/<source>.csv` |

**Responsibilities:**
- Execute standardized search queries against each target database
- Handle API pagination and rate limits
- Deduplicate within a single source
- Record all hits with accession, title, organism, description
- Log search metadata (query, date, total results) for PRISMA

**Target databases:**
1. NCBI BioProject / SRA
2. ENA (European Nucleotide Archive)
3. GEO (Gene Expression Omnibus)
4. MGnify
5. Qiita

---

### 3. Screening Agent

| Property | Value |
|----------|-------|
| Prompt   | `prompts/screening_agent.md` |
| Role     | Inclusion / exclusion screener |
| Inputs   | `data/search_results/*.csv`, `config/criteria.yaml` |
| Outputs  | `data/screening_log.csv` |

**Responsibilities:**
- Evaluate each candidate against inclusion criteria (I1–I6)
- Apply exclusion criteria (E1–E8) when inclusion fails
- Set decision: `include`, `exclude`, or `maybe`
- For `maybe`: attempt resolution by checking BioSample / linked paper
- Record standardized `exclusion_reason` for every exclusion
- Flag potential duplicates across sources for dedup check

**Decision logic (waterfall):**
```
IF non-human           → exclude (E1: non_human)
IF no ASD phenotype    → exclude (E2: not_asd)
IF not microbiome seq  → exclude (E3: not_microbiome_sequencing)
IF no public link      → exclude (E4: no_public_data_link)
IF duplicate           → exclude (E5: duplicate_dataset)
IF no control group    → exclude (E6: no_control_group)
IF body site unknown   → maybe → resolve or exclude (E7: insufficient_metadata)
ELSE                   → include
```

---

### 4. Metadata Extraction Agent

| Property | Value |
|----------|-------|
| Prompt   | `prompts/metadata_agent.md` |
| Role     | Metadata extractor and normalizer |
| Inputs   | `data/screening_log.csv` (included entries), `config/controlled_vocab.yaml` |
| Outputs  | `data/datasets.csv` |

**Responsibilities:**
- For each included dataset, fetch detailed metadata from source database
- Normalize fields to controlled vocabularies:
  - `body_site` → stool, gut, oral, oral_saliva, oral_plaque, rectal_swab, nasal, skin, other
  - `sequencing_type` → 16S, shotgun, metagenome, metatranscriptome
  - `age_group` → child, adult, mixed, unknown
- Extract sample counts (n_asd, n_control, n_total)
- Find linked PubMed IDs and DOIs
- Fill all `datasets.csv` columns; use `unknown` for unavailable fields

---

### 5. QC Agent

| Property | Value |
|----------|-------|
| Prompt   | `prompts/qc_agent.md` |
| Role     | Quality control and validation |
| Inputs   | `data/datasets.csv`, `data/screening_log.csv`, `schemas/*` |
| Outputs  | Validation report, PRISMA flow counts |

**Responsibilities:**
- Validate CSV files against JSON schemas
- Check referential integrity (every included screening_log entry has a datasets.csv row)
- Report completeness metrics (% of fields filled vs unknown)
- Detect anomalies (e.g., n_total != n_asd + n_control)
- Generate PRISMA flow diagram counts:
  - Records identified per source
  - Duplicates removed
  - Records screened
  - Records excluded (by reason)
  - Studies included in final atlas

---

## Data Flow

```
[BioProject] [ENA] [GEO] [MGnify] [Qiita]
      │        │     │      │        │
      └────────┴─────┴──────┴────────┘
                     │
              Search Agent
                     │
                     v
        data/search_results/*.csv
                     │
            Screening Agent
                     │
                     v
          data/screening_log.csv
                     │
         Metadata Extraction Agent
                     │
                     v
            data/datasets.csv
                     │
               QC Agent
                     │
                     v
         Validated atlas + PRISMA flow
```

---

## Running the Pipeline

```bash
# The orchestrator coordinates all phases:
# Phase 1: Search
claude --prompt-file prompts/search_agent.md

# Phase 2: Screening
claude --prompt-file prompts/screening_agent.md

# Phase 3: Metadata extraction
claude --prompt-file prompts/metadata_agent.md

# Phase 4: QC
claude --prompt-file prompts/qc_agent.md

# Or run the orchestrator to coordinate all phases:
claude --prompt-file prompts/orchestrator.md
```

## File Conventions

- All CSV files use UTF-8 encoding, comma separator, double-quote escaping
- Date format: `YYYY-MM-DD`
- Empty optional fields: leave blank (not `NA` or `null`)
- All text content in English
