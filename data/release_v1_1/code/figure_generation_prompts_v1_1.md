# ASD Microbiome Atlas v1.1: Figure Generation Prompts

These prompts are intended for GPT-assisted creation of reproducible,
publication-quality figures. GPT should generate Python code and vector outputs
from the specified project files rather than inventing values in a raster image.

## Shared Requirements For All Figures

Use English labels. Create publication-quality figures on a white background with
a consistent colorblind-safe palette, preferably Okabe-Ito. Use a clean sans-serif
font, restrained gridlines, no 3D effects, no decorative icons, and no gradients
that encode no information. Export editable SVG and PDF plus a 300-dpi PNG. Keep
all labels readable at final journal size. Display counts as integers and
percentages to one decimal place where applicable. Do not infer or add missing
data. Present the participant sum as an overlap-adjusted atlas contribution, not
as a guaranteed global unique-person count. Add a brief caption and a machine-readable source-data CSV
for every figure.

Primary data files:

- `Frozen_v1.1/datasets_release_v1_1_extended.csv`
- `Manuscript/descriptive_statistics_v1_1.csv`
- `Manuscript/Tables_v1_1/Table_S4_PRISMA_counts_v1_1.md`

## Figure 1. PRISMA-Informed Dataset Identification And Selection

### GPT Prompt

Create a publication-quality PRISMA-informed flow diagram for the ASD Microbiome
Atlas v1.1. Generate the figure reproducibly in Python using matplotlib or
Graphviz. Do not use an image-generation model for text or numbers.

Use the following exact flow:

- Five databases searched.
- Records identified: 340.
- Database contributions: BioProject/SRA 196, GEO 18, ENA 110, MGnify 3, Qiita 13.
- Duplicate or linked-duplicate records removed before screening: 132.
- Records screened: 208.
- Records excluded: 133.
- Exclusion reasons: non-human 65; no control group 27; not ASD 19; not
  microbiome sequencing 17; duplicate dataset 2; insufficient metadata 2;
  other 1.
- Records included after screening: 75.
- Records removed during accession-level curation and final QC: 5.
- Accession-level records included in atlas v1.1: 70.

Show the five database contributions in the identification box, the seven
exclusion reasons in a side box, and final curation as a separate stage after
screening. Add a small note: "PubMed was used for metadata verification only and
was not counted as a retrieval database." Add another note: "Two reviewers
independently screened candidate records; decisions were finalized by consensus."
Use a vertical top-to-bottom flow, aligned boxes, concise labels, and arrows with
consistent weight. Verify that 340 - 132 = 208, 208 - 133 = 75, and 75 - 5 = 70
before exporting.

Suggested caption: "Figure 1. PRISMA-informed identification, screening, and
curation of public human ASD microbiome dataset records included in the ASD
Microbiome Atlas v1.1."

## Figure 2. Landscape Of Included Dataset Records

### GPT Prompt

Create a four-panel publication-quality figure describing the 70 accession-level
records in the ASD Microbiome Atlas v1.1. Read values directly from
`Manuscript/descriptive_statistics_v1_1.csv` and verify them against
`Frozen_v1.1/datasets_release_v1_1_extended.csv`. Use horizontal bar charts with
counts at the bar ends. Percentages must use 70 as the denominator. Do not combine
categories unless explicitly instructed.

Panel A, study country:

- China 34
- United States 8
- Italy 6
- Hong Kong 3
- Uruguay 3
- India 2
- Saudi Arabia 2
- Bosnia and Herzegovina 1
- Colombia 1
- Denmark 1
- Ecuador 1
- Egypt 1
- Israel 1
- Japan 1
- Lebanon 1
- Mexico 1
- Russia 1
- South Korea 1
- Thailand 1

Panel B, normalized body site:

- Stool 62
- Oral 4
- Gut 3
- Gut and oral 1

Panel C, assay classification:

- 16S 53
- Metagenome 12
- Multi-amplicon 2
- Multi-assay 1
- Multi-omic 1
- Shotgun 1

Panel D, study design:

- Case-control 58
- Intervention 8
- Cross-sectional 4

Order bars from highest to lowest within each panel. Use one consistent color for
ordinary categories and a distinct but non-alarm color for combined or multi-
component categories. Label panels A-D. Do not use pie or donut charts. Add
"Accession-level records, N=70" below the main title. Keep Hong Kong as the
curated country label used in the atlas; do not silently merge it with China.

Suggested caption: "Figure 2. Geographic, anatomical, methodological, and study-
design characteristics of the 70 accession-level dataset records included in the
ASD Microbiome Atlas v1.1."

## Figure 3. Cross-Repository Mapping And Cohort-Overlap Adjudication

### GPT Prompt

Create a two-panel publication-quality schematic explaining deduplication and
participant-overlap adjudication in the ASD Microbiome Atlas v1.1. Read mapping
fields from `Frozen_v1.1/datasets_release_v1_1_extended.csv`. Use Python with
matplotlib, Graphviz, or Plotly and export vector files.

Panel A, accession-to-canonical mapping:

- Start with 70 accession-level records.
- End with 64 provisional canonical dataset entities.
- Six accession records map to another canonical record.
- Among these six mapped records: four are repository mirrors, one is an
  alternate release, and one is a linked public subset.

Show this as a compact flow or alluvial diagram. Clearly label the unit as
"accession records" on the left and "canonical entities" on the right.

Panel B, accession-level contribution adjudication:

- Full contribution: 55 records.
- Partial contribution: 5 records.
- Zero additional contribution: 10 records.
- Unresolved: 0 records.

Show Panel B as a stacked horizontal bar or four aligned blocks summing to 70.
Use neutral blue for full contribution, amber for partial, and gray for zero
additional contribution. Do not include an unresolved segment. Add a callout:
"Overlap-adjusted atlas contribution: 2,770 ASD + 2,187 controls = 4,957; not a
guaranteed global unique-person count because anonymized overlap may be undetectable."

Do not draw Panel B as downstream from the 64 canonical entities: its categories
are accession-level adjudication flags and sum to 70. Do not imply that 64, 54,
5, 10, and 1 are the same counting unit. Detailed row-level decisions are in
Supplementary Table S2.

Suggested caption: "Figure 3. Cross-repository accession mapping and adjudication
of participant overlap. Accession-level discovery records were mapped to
canonical dataset entities, while participant contributions were evaluated
separately to limit double counting."

## Figure 4. Atlas Website And Dataset-Reuse Workflow

### GPT Prompt

Create a publication-quality workflow figure showing how a researcher uses the
ASD Microbiome Atlas web service. Use a real screenshot of the final deployed
website if one is provided. Do not invent interface elements or claim features
that are not implemented. If no verified screenshot is available, use a clearly
labeled neutral wireframe rather than a realistic fabricated interface.

Show the following left-to-right workflow:

1. Open the ASD Microbiome Atlas.
2. Search and filter dataset records.
3. Review harmonized metadata and curation status.
4. Distinguish accession-level records from canonical dataset entities.
5. Follow the verified repository link.
6. Download public data and metadata from the source repository.
7. Use the selected dataset for reproducible downstream research.

Show representative filters only if they exist in the deployed website:
country, body site/specimen, assay, sequencing platform, study design, public raw
data, downloadable ASD/control pair, and canonical/record status. Include the
release label `v1.1` and a small note that repository files remain hosted by the
original public data providers. Do not imply that the atlas hosts private data,
performs clinical diagnosis, validates biomarkers, or guarantees dataset fitness
for a specific analysis.

Use a clean vector schematic with a restrained browser-frame mockup in the center
and simple labeled steps around it. Avoid stock medical imagery, puzzle-piece
symbols, brain icons, and decorative DNA graphics.

Suggested caption: "Figure 4. Research workflow supported by the ASD Microbiome
Atlas web service, from dataset discovery and metadata review to verified source-
repository access and downstream reuse."
