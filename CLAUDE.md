# ASD Microbiome Atlas

This project builds a systematized, PRISMA-compliant catalog of public human
ASD (Autism Spectrum Disorder) microbiome sequencing datasets.

## Project Structure

```
config/          — YAML configs: search queries, inclusion/exclusion criteria, vocabularies
data/            — All data artifacts (CSV): search results, screening log, final datasets
prompts/         — Agent prompts for each pipeline stage
schemas/         — JSON Schema definitions for CSV validation
scripts/         — Python utilities (validation, PRISMA reports)
```

## Key Files

- `PLAN.md` — Work plan with phases and deliverables
- `agents.md` — Agent architecture, roles, data flow
- `data/datasets.csv` — The atlas: curated dataset catalog
- `data/screening_log.csv` — PRISMA-compliant screening audit trail

## Conventions

- **Language:** All files, prompts, and documentation in English
- **CSV format:** UTF-8, comma-separated, double-quote escaping
- **Dates:** YYYY-MM-DD
- **Controlled vocabularies:** Defined in `config/controlled_vocab.yaml`
- **Decisions:** `include` / `exclude` / `maybe` — see `config/criteria.yaml`

## Inclusion / Exclusion Criteria (summary)

**Include if ALL of:** Human (I1), ASD phenotype (I2), microbiome sequencing (I3),
body site determinable (I4), public access (I5), ASD vs control comparison (I6).

**Exclude if ANY of:** Non-human (E1), no ASD (E2), not microbiome seq (E3),
no public link (E4), duplicate (E5), no control group (E6), body site
undetermined (E7), other with notes (E8).

## Agent Pipeline

Search → Screening → Metadata Extraction → QC

See `agents.md` for full architecture and `prompts/` for agent instructions.
