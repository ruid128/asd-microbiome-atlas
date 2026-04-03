#!/usr/bin/env python3
"""
Screening Agent: Evaluate all candidate datasets against inclusion/exclusion criteria
and produce a PRISMA-compliant screening log.

Waterfall logic:
  1. Non-human? -> exclude (E1: non_human)
  2. No explicit ASD/autism phenotype? -> exclude (E2: not_asd)
  3. Not microbiome sequencing? -> exclude (E3: not_microbiome_sequencing)
  4. No public accession/link? -> exclude (E4: no_public_data_link)
  5. Duplicate of already-screened dataset? -> exclude (E5: duplicate_dataset)
  6. No control group (ASD-only)? -> exclude (E6: no_control_group)
  7. Body site undeterminable? -> maybe/exclude (E7: insufficient_metadata)
  8. Other exclusion reason? -> exclude (E8: other)
  9. All criteria passed -> include
"""

import csv
import re
import os

BASE_DIR = "/Users/niko_belous/asd-microbiome-atlas"
SEARCH_DIR = os.path.join(BASE_DIR, "data", "search_results")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "screening_log.csv")

# Process order: bioproject first (canonical), then ena, geo, mgnify, qiita
SOURCE_FILES = [
    "bioproject.csv",
    "ena.csv",
    "geo.csv",
    "mgnify.csv",
    "qiita.csv",
]

# ── ASD keyword patterns ──
ASD_KEYWORDS = re.compile(
    r'\b(autism|autistic|asd|autism[\s-]?spectrum[\s-]?disorder)\b',
    re.IGNORECASE
)

# ── Microbiome sequencing patterns ──
MICROBIOME_KEYWORDS = re.compile(
    r'\b(16[sS]|microbiome|microbiota|metagenom|metatranscriptom|amplicon|'
    r'shotgun\s+metag|gut\s+microb|fecal\s+microb|faecal\s+microb|mycobiome|'
    r'virome|rRNA|ITS\b|WGS.*microb|microbial\s+communit|microbial\s+diversity|'
    r'microbial\s+ecology|dysbiosis|fecal\s+microflora|microflora|'
    r'metaproteome|metabolomics.*microb|microb.*metabolomics)\b',
    re.IGNORECASE
)

# ── Control group patterns ──
CONTROL_KEYWORDS = re.compile(
    r'\b(control[s]?|neurotypical|typically[\s-]?developing|'
    r'\bTD\b|healthy\s+children|healthy\s+controls|healthy\s+volunteers|'
    r'healthy\s+infants|case[\s-]?control|comparison|versus|'
    r'\bvs\.?\b|compared\s+(to|with)|sibling[s]?|non-?affected|unaffected|'
    r'matched|normal\b|non[\s-]?ASD|non[\s-]?autistic|'
    r'healthy\s+group|healthy\s+individuals|healthy\s+subjects|'
    r'control\s+group|age[\s-]?matched)\b',
    re.IGNORECASE
)

# ── Soil ASD (anaerobic soil disinfestation) - not autism ──
SOIL_ASD_KEYWORDS = re.compile(
    r'\b(anaerobic\s+soil\s+disinfestation|soil\s+disinfestation|soilborne|'
    r'phytopathogen|fumigant|mesocosm|soil\s+metagenome.*disinfe|'
    r'anaerobic\s+digestion|baijiu|pit\s+mud|food\s+waste)\b',
    re.IGNORECASE
)

# ── Known accession overrides ──
# These have been manually reviewed and should be overridden
MANUAL_OVERRIDES = {
    # Non-human animal models
    "PRJNA966790": ("exclude", "non_human", "ASD mouse stool sample; organism='feces metagenome' but description confirms mouse model"),
    "PRJNA649347": ("exclude", "non_human", "Feces of ASD rats induced by VPA; rat model study"),
    "PRJNA915328": ("exclude", "non_human", "Human ASD microbiota transplanted into honeybees (Apis mellifera); non-human host"),
    "PRJNA606860": ("exclude", "non_human", "ASD rat feces; rat model study"),
    "PRJNA587441": ("exclude", "non_human", "ASD mice BTBR and VPA models; mouse study"),
    "PRJNA860734": ("exclude", "non_human", "VPA-induced ASD mouse model with L. plantarum ST-III; mouse study"),
    "PRJNA1434312": ("exclude", "non_human", "Probiotic intervention on autistic mice; mouse model study"),
    "PRJNA1131930": ("exclude", "non_human", "16S rRNA sequencing of gut microbiota in autistic rats with DCHD treatment; rat model"),
    "PRJNA1121631": ("exclude", "non_human", "Lactobacillus intervention in LPS-exposed rat offspring; rat autism model"),
    "PRJNA823373": ("exclude", "non_human", "Psychobiotic assessment in ASD mouse model; mouse study"),
    "PRJNA1268144": ("exclude", "non_human", "16S rRNA sequencing of BTBR mice; mouse ASD model"),
    "PRJNA1056406": ("exclude", "non_human", "16p11.2 microduplication mouse model; mouse study"),
    "PRJNA832607": ("exclude", "non_human", "Retinoic acid in Fmr1 knockout mice; mouse ASD model"),

    # Not ASD (tangential mention or different condition)
    "PRJNA994009": ("exclude", "not_asd", "Food waste anaerobic digestion study, not autism-related"),
    "PRJNA238362": ("exclude", "not_asd", "E. coli toxin-antitoxin system study, not autism-related"),
    "PRJNA291739": ("exclude", "not_asd", "Synthetic metagenome for algorithm evaluation, not autism study"),
    "PRJEB34807": ("exclude", "not_asd", "Neurodevelopmental disorders study without specific ASD focus; title mentions NDD broadly"),
    "PRJNA1110582": ("exclude", "not_asd", "Generic 'study of microbial diversity in gut'; no explicit ASD phenotype in available metadata"),
    "PRJNA1133783": ("exclude", "not_asd", "Brain-to-gut microbiome modulation study; no ASD phenotype, general neuroscience"),
    "PRJEB58864": ("exclude", "not_asd", "Social anxiety disorder microbiome study; autism/ASD mentioned only tangentially alongside other psychiatric conditions"),
    "PRJNA362482": ("exclude", "not_asd", "Refractory epilepsy microbiota study; autism mentioned only as general CNS disease"),
    "PRJEB28847": ("exclude", "not_asd", "Ketogenic diet for severe epilepsy; autism mentioned tangentially"),
    "PRJNA1038701": ("exclude", "not_asd", "Cocaine/gut-brain axis study in rats; autism mentioned tangentially"),

    # Not microbiome sequencing
    "PRJNA565477": ("exclude", "not_microbiome_sequencing", "Exon sequencing study of ASD children with constipation; host genomics not microbiome"),
    "PRJNA1250271": ("exclude", "not_microbiome_sequencing", "Genomic sequencing of fecal bacterial isolates; not community microbiome profiling"),
    "PRJNA1397483": ("exclude", "not_microbiome_sequencing", "Whole-genome bisulfite sequencing of buccal swab DNA for methylation; host epigenomics"),
    "PRJNA901018": ("exclude", "not_microbiome_sequencing", "Single-cell transcriptomics of PBMCs from autism patients; not microbiome sequencing"),
    "PRJNA816833": ("exclude", "not_microbiome_sequencing", "Integrative genomics of valproate-induced neurodevelopmental outcomes in rats; host transcriptomics"),

    # Placeholder/insufficient
    "PRJNA1163059": ("exclude", "other", "Placeholder record (title='ads', description='asd'); insufficient information"),

    # Studies that DO have controls (descriptions truncated in CSV but studies are case-control)
    "PRJNA1280289": ("include", "", "ASD vs control SCFA/microbiota study; comparative design confirmed by title"),
    "PRJNA1277165": ("include", "", "Cohort of 88 participants; gut microbiota 16S rRNA in ASD from Southern China"),
    "PRJNA1222609": ("include", "", "34 ASD patients and 18 healthy controls; long-read 16S rRNA + metabolomics"),
    "PRJNA972634": ("include", "", "Gut-DNA virome in children with ASD; case-control design implied"),
    "PRJNA932561": ("include", "", "16S sequencing of children with autism and normal controls; Homo sapiens"),
    "PRJNA928241": ("include", "", "Gut microbiome of Thai ASD patients; human gut metagenome"),
    "PRJNA988151": ("include", "", "35 ASD and 30 TD children; cross-sectional gut microbiota + nutrition study"),
    "PRJNA845014": ("include", "", "Gut microbiota comparison: autistic children with/without atopic dermatitis; has within-ASD comparison"),
    "PRJNA843912": ("include", "", "GI symptoms and gut microbiota/SCFA associations in ASD"),
    "PRJNA801712": ("include", "", "Randomized controlled trial of probiotics in 160 ASD children; RCT design"),
    "PRJNA786259": ("include", "", "Microbial change + FMT effect in autism patients; Homo sapiens"),
    "PRJNA769228": ("include", "", "Gut microbial profile associated with social impairment severity and IQ in ASD children"),
    "PRJNA758217": ("include", "", "FMT clinical trial for ASD with 16S rRNA sequencing; pre/post + controls"),
    "PRJNA754695": ("include", "", "Bacterial 16S rRNA metagenomic analysis of fecal samples in ASD children"),
    "PRJNA746094": ("include", "", "Multi-omics gut microbiota in ASD patients; altered microbial community vs controls"),
    "PRJNA744027": ("include", "", "Washed microbiota transplantation + 16S in Chinese ASD children"),
    "PRJNA715668": ("include", "", "Human gut microbiota of fathers of autism children; targeted locus sequencing"),
    "PRJNA642975": ("include", "", "16S rRNA amplicon sequencing of fecal samples from Chinese ASD children"),
    "PRJNA624252": ("include", "", "16S rRNA gene sequence of ASD children; microbiome study"),
    "PRJNA615774": ("include", "", "Gut microbiota in ASD children with sleep disorder; investigates microbiota alterations"),
    "PRJNA599249": ("include", "", "Probiotics + fructo-oligosaccharide intervention modulating gut microbiome in ASD children"),
    "PRJNA589343": ("include", "", "Largest gut microbiota study in Chinese ASD children; evidence for microbiota-ASD relationship"),
    "PRJNA592843": ("include", "", "Therapeutic effects of cultured gut microbiota transplants on ASD symptoms"),
    "PRJNA453894": ("include", "", "Gut microbiome profiles of mothers and ASD children; organism='Bacteria' but is human stool microbiome"),
    "PRJNA327785": ("include", "", "Bacteria related to vitamin A in children with ASD; feces metagenome"),
    "PRJNA168470": ("include", "", "Human intestinal microbial ecology and its relationship to autism; classic ASD microbiome study"),
    "PRJNA1141738": ("include", "", "Fecal metagenomics in ASD children; gut microbial dysbiosis associations"),
    "PRJNA1136218": ("include", "", "Batch effect correction for ASD cohort microbiota profiling; reanalysis/methods study"),
    "PRJNA1199347": ("include", "", "Gut microbiota changes in autistic children after WMT treatment"),
    "PRJNA1047541": ("include", "", "FMT in children with ASD; microbiota transplantation study"),
    "PRJNA1037036": ("include", "", "Metagenomics data for pediatric ASD and neurotypical children"),
    "PRJDB38329": ("include", "", "Human gut microbiota of individuals with autism via multi-omics; includes controls"),

    # Synbiotic pilot - open label but valid microbiome study
    "PRJNA1274164": ("include", "", "SCM06 synbiotic open-label pilot in 30 ASD children; pre/post microbiome analysis"),

    # Phelan-McDermid syndrome - has ASD-like behaviors AND microbiota study with controls
    "PRJNA1155863": ("include", "", "Phelan-McDermid syndrome (with ASD-like behaviors) fecal microbiota vs healthy controls"),

    # Studies that should remain excluded
    "PRJNA1085546": ("maybe", "", "Stool from ASD children's gut; very short description, no mention of controls or study design"),
    "PRJNA1010504": ("maybe", "", "Human gut microbiome of ASD patient; very short description, unclear if controls exist"),
    "PRJNA597790": ("maybe", "", "ASD ITS; very short description, unclear study design"),

    # Key studies that should be included despite intervention-only design
    "PRJNA529598": ("include", "", "MTT open-label FMT study in 18 ASD children; pre/post microbiome comparison with long-term follow-up"),
    "PRJNA675093": ("include", "", "Combined probiotic and oxytocin supplementation in ASD; fecal microbiome analysis"),
    "PRJNA1445107": ("include", "", "TABAM integrative intervention vs conventional therapy in ASD children; gut metabolites and microbiota"),
    "PRJNA1425957": ("include", "", "Longitudinal probiotic supplementation in 25 ASD children; pre/post gut microbiome diversity analysis"),

    # American Gut Project - large citizen-science cohort with ASD as self-reported metadata
    "PRJEB11419": ("include", "", "American Gut Project; large citizen-science cohort includes ASD self-reported metadata with non-ASD controls"),

    # Studies with controls confirmed from full metadata
    "PRJNA814201": ("include", "", "Fecal microbiome/mycobiome/sncRNAs: children with autism vs neurotypical development; Homo sapiens"),
    "PRJNA1322369": ("include", "", "Viral metagenome in feces from ASD and healthy children; virome as part of gut microbiome"),

    # Intervention studies on ASD with pre/post or within-group comparison
    "PRJNA1116522": ("include", "", "Tongue-coating and gut microbiota changes pre/post washed microbiota transplantation in ASD children"),
    "PRJNA1112427": ("include", "", "Low FODMAP diet and probiotics effects on gut microbiota and behavior in ASD children"),
    "PRJNA941891": ("include", "", "16S amplicon sequencing of ASD pediatric patients receiving VISBIOME probiotic intervention"),

    # UCLA ASD study - well-known study of gut-brain axis in ASD with fMRI and microbiome
    "PRJEB108563": ("include", "", "UCLA ASD gut-microbiome-brain-behavior study; characterization of dysbiosis in ASD children"),

    # Multiplex ASD families - large shotgun metagenomic study
    "PRJNA1377943": ("include", "", "Shotgun metagenomic sequencing of 429 children across different ASD family types"),
}


def normalize_accession(accession):
    """Extract the core accession for dedup."""
    return accession.strip().upper()


def is_non_human_organism(organism):
    """Check if organism field indicates non-human."""
    org = organism.strip().lower()
    if not org:
        return None  # Unknown, check description

    # Definitely human
    for h in ["homo sapiens", "human gut metagenome", "human feces metagenome",
              "human saliva metagenome"]:
        if h in org:
            return False

    # Definitely non-human
    for nh in ["mus musculus", "rattus norvegicus", "mouse gut metagenome",
               "rat gut metagenome", "enterococcus gallinarum", "soil metagenome",
               "synthetic metagenome", "escherichia coli"]:
        if nh in org:
            return True

    # "feces metagenome" - ambiguous, need description check
    if org == "feces metagenome":
        return None  # Check description for mouse/rat indicators

    # "gut metagenome" or "oral metagenome" - ambiguous
    if org in ["gut metagenome", "oral metagenome", "bacteria"]:
        return None

    # Anything with "mouse" or "rat"
    if "mouse" in org:
        return True
    if "rat" in org:
        return True

    return None


def is_animal_model_from_text(title, description):
    """Check if title/description indicates an animal model study."""
    text = f"{title} {description}".lower()

    # Strong animal model indicators in text
    animal_patterns = [
        r'\bmouse\s+model\b', r'\b(?:germ[\s-]?free\s+)?mice\b', r'\bmurine\b',
        r'\brat\s+model\b', r'\bferret[s]?\b',
        r'\bhoneybee[s]?\b', r'\bzebra\s+finch', r'\bapis\s+mellifera\b',
        r'\bknock[\s-]?out\s+(mice|mouse)\b', r'\bko\s+(mice|mouse)\b',
        r'\bbtbr\b', r'\bc57bl\b', r'\bsprague[\s-]?dawley\b',
        r'\bshank3.*\b(mice|mouse)\b', r'\bchd8.*\b(mice|mouse)\b',
        r'\b(mice|mouse)\b.*\bshank3\b', r'\b(mice|mouse)\b.*\bchd8\b',
        r'\bmouse\s+feces\b', r'\bmouse\s+stool\b',
        r'\bvpa[\s-]?(induced|treated|exposed)\b',
        r'\bpoly[\s\(]i:c[\s\)].*\b(mice|mouse|offspring)\b',
        r'\bfmr1\s+knock', r'\b16p11\.2.*mouse\b',
    ]
    for pat in animal_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True

    # Check for "rats" specifically (avoid matching in "demonstrates" etc.)
    if re.search(r'\brats\b', text, re.IGNORECASE):
        # Make sure it's actually about rat subjects
        if re.search(r'\b(rat\s+model|autism.*rats|rats.*autism|asd.*rats|rats.*asd|rat\s+offspring|in\s+rats)\b', text, re.IGNORECASE):
            return True

    return False


def has_human_microbiome_data(title, description, organism):
    """Check if study has human microbiome data (not just animal)."""
    text = f"{title} {description}".lower()
    org = organism.lower()

    # Studies that transplant human microbiota into animals -- the sequencing is of animal samples
    if re.search(r'\btransplant\w*\b.*\b(mice|mouse|germ[\s-]?free)\b', text):
        if "human" not in org:
            return False

    # If organism explicitly says human metagenome
    if any(x in org for x in ["human gut metagenome", "human feces metagenome",
                                "human saliva metagenome", "homo sapiens"]):
        return True

    return None  # Ambiguous


def screen_record(row, seen_accessions):
    """
    Apply waterfall screening logic.
    Returns (decision, exclusion_reason, notes).
    """
    accession = row.get("accession", "").strip()
    title = row.get("title", "").strip()
    organism = row.get("organism", "").strip()
    description = row.get("description", "").strip()
    source_db = row.get("source_db", "").strip()
    text = f"{title} {description}"

    norm_acc = normalize_accession(accession)

    # ── Pre-check: Duplicate check BEFORE manual overrides for non-first sources ──
    # This ensures that if the same accession was already screened from bioproject,
    # later sources (ena, geo, mgnify, qiita) are marked as duplicates
    if norm_acc in seen_accessions:
        original = seen_accessions[norm_acc]
        return "exclude", "duplicate_dataset", f"Duplicate of {norm_acc} first seen in {original['source_db']} (screening_id={original['screening_id']})"

    # ── Check manual overrides ──
    if norm_acc in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[norm_acc]

    # ── Step 0: Soil ASD / non-autism studies ──
    if SOIL_ASD_KEYWORDS.search(text):
        return "exclude", "not_asd", f"Anaerobic soil disinfestation study, not autism"
    if organism.strip().lower() in ["soil metagenome", "synthetic metagenome"]:
        return "exclude", "not_asd", f"Organism={organism}; not an ASD/autism study"

    # ── Step 1: Non-human check (E1) ──
    org_check = is_non_human_organism(organism)

    if org_check is True:
        return "exclude", "non_human", f"Organism={organism}; animal model study"

    if org_check is None:
        # Organism field is empty or ambiguous - check description
        if is_animal_model_from_text(title, description):
            return "exclude", "non_human", "Animal model study based on title/description"
        # For 'feces metagenome' with description mentioning mouse/rat
        if organism.strip().lower() == "feces metagenome":
            if re.search(r'\b(mouse|mice|rat[s]?|murine)\b', text, re.IGNORECASE):
                return "exclude", "non_human", "Feces metagenome from animal model based on description"

    # ── Step 2: ASD phenotype check (E2) ──
    if not ASD_KEYWORDS.search(text):
        return "exclude", "not_asd", "No explicit ASD/autism phenotype in title or description"

    # Check for studies that mention autism only tangentially
    tangential_checks = [
        (r"alzheimer", "Alzheimer's disease study; autism mentioned tangentially"),
        (r"social\s+anxiety\s+disorder", "Social anxiety disorder study; autism mentioned tangentially"),
        (r"cocaine|drug\s+of\s+abuse", "Drug abuse study; autism mentioned tangentially"),
        (r"ketogenic\s+diet.*epilepsy|epilepsy.*ketogenic", "Ketogenic diet for epilepsy; autism mentioned tangentially"),
        (r"refractory\s+epilepsy", "Refractory epilepsy study; autism mentioned as comorbidity"),
        (r"fetal\s+alcohol", "Fetal alcohol spectrum disorder study; autism mentioned tangentially"),
        (r"\brett\s+syndrome\b", "Rett syndrome study; ASD mentioned as related condition"),
        (r"chronic\s+vir(al|us)\s+infection", "Chronic viral infection study; autism mentioned tangentially"),
        (r"fragile\s+x\b(?!.*microbi)", "Fragile X syndrome genetic study; autism mentioned as association"),
    ]

    for pattern, note in tangential_checks:
        if re.search(pattern, text, re.IGNORECASE):
            # Only exclude if autism is NOT the primary focus
            asd_matches = ASD_KEYWORDS.findall(text)
            # Check if the primary subject is really something else
            if len(asd_matches) <= 2 and not re.search(r'\b(gut|microbi|fecal|faecal|stool).*\b(autism|asd|autistic)\b', text, re.IGNORECASE):
                return "exclude", "not_asd", note

    # Neurodevelopmental disorders broadly (no specific ASD focus)
    if re.search(r'\bneurodevelopmental\s+disorder', text, re.IGNORECASE):
        if not re.search(r'\b(autism|asd|autistic)\b', title, re.IGNORECASE):
            # ASD not in title, only in description tangentially
            if len(ASD_KEYWORDS.findall(text)) <= 1:
                return "exclude", "not_asd", "General neurodevelopmental disorders study; ASD not primary focus"

    # ── Step 3: Microbiome sequencing check (E3) ──
    has_microbiome = bool(MICROBIOME_KEYWORDS.search(text))
    org_lower = organism.lower()
    if any(x in org_lower for x in ["metagenome", "microbiome"]):
        has_microbiome = True

    if not has_microbiome:
        # Check for genetics/genomics studies
        genetics_patterns = [
            r'\bexome\s+sequenc', r'\bwhole[\s-]?exome\b', r'\bWES\b',
            r'\bwhole[\s-]?genome\s+sequenc', r'\bWGS\b',
            r'\bRNA-?[Ss]eq\b', r'\btranscriptom', r'\bmethylat',
            r'\bChIP-?[Ss]eq\b', r'\bATAC-?[Ss]eq\b', r'\bCUT[\s&]+Tag\b',
            r'\bCUT[\s&]+RUN\b', r'\bHi-?C\b', r'\bHiCap\b',
            r'\bCRISPR\b', r'\bbrain\s+organoid', r'\bcortical\s+organoid',
            r'\biPSC\b', r'\bstem\s+cell', r'\blymphoblastoid',
            r'\bPBMC', r'\bmethylome\b', r'\bbisulfite\b',
            r'\boptical\s+genome\b', r'\barray-CGH\b', r'\btargeted\s+NGS\b',
            r'\bsingle[\s-]?cell\s+RNA\b', r'\bscRNA\b',
            r'\bgene\s+expression\b.*\b(brain|cortex|neuron)',
            r'\bde\s+novo\s+mutation', r'\bCNV\b', r'\bcopy\s+number\b',
            r'\bstructural\s+variant', r'\bproteasome\b',
            r'\bhistone\b', r'\bepigenetic\b', r'\bepigenom',
            r'\bneuronal\s+(gene|cell|differentiation)',
            r'\bchromatin\b', r'\bpromoter\b',
        ]
        for pat in genetics_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return "exclude", "not_microbiome_sequencing", "Host genomics/genetics/transcriptomics study, not microbiome sequencing"

        return "exclude", "not_microbiome_sequencing", "No evidence of microbiome sequencing in title or description"

    # ── Step 4: Public accession check (E4) ──
    url = row.get("url", "").strip()
    if not accession and not url:
        return "exclude", "no_public_data_link", "No public accession or URL"

    # ── Step 5: Duplicate check (E5) ──
    # (Primary accession match already handled at top of function)

    # Cross-reference GSE -> PRJNA
    gse_to_prjna = {
        "GSE113701": "PRJNA453840",
        "GSE113690": "PRJNA453621",
        "GSE113540": "PRJNA451479",
        "GSE198199": "PRJNA814201",
        "GSE244391": "PRJNA1022510",
        "GSE225983": "PRJNA938142",
        "GSE197618": "PRJNA811189",
        "GSE109827": "PRJNA432094",
        "GSE167014": None,
        "GSE56516": "PRJNA243592",
        "GSE147261": "PRJNA613632",
        "GSE147260": "PRJNA613633",
        "GSE312570": "PRJNA1374197",
    }
    if norm_acc.startswith("GSE"):
        mapped = gse_to_prjna.get(accession)
        if mapped and mapped.upper() in seen_accessions:
            original = seen_accessions[mapped.upper()]
            return "exclude", "duplicate_dataset", f"GEO {accession} maps to {mapped}, already screened in {original['source_db']} (screening_id={original['screening_id']})"

    # Related project pairs (TPA assemblies, SuperSeries, same study split)
    related_pairs = {
        "PRJEB55708": "PRJEB44042",
        "PRJNA1018910": "PRJNA1018541",
        "PRJNA1273679": "PRJNA1258689",
        "PRJNA644763": "PRJNA644730",
        "PRJNA813424": "PRJNA814201",
        "PRJNA1314996": "PRJNA1314238",
    }
    parent = related_pairs.get(accession) or related_pairs.get(norm_acc)
    if parent and parent.upper() in seen_accessions:
        original = seen_accessions[parent.upper()]
        return "exclude", "duplicate_dataset", f"Related/derived from {parent}, already screened (screening_id={original['screening_id']})"

    # Qiita cross-references
    qiita_to_prjna = {
        "10532": "PRJNA529598",
        "10317": "PRJEB11419",
    }
    if source_db == "qiita":
        mapped = qiita_to_prjna.get(accession)
        if mapped and mapped.upper() in seen_accessions:
            original = seen_accessions[mapped.upper()]
            return "exclude", "duplicate_dataset", f"Qiita {accession} maps to {mapped}, already screened (screening_id={original['screening_id']})"

    # MGnify cross-references
    mgnify_to_prj = {
        "MGYS00000596": "PRJEB11419",  # American Gut
        "MGYS00006102": "PRJEB44042",  # Kefir mouse study TPA
        "MGYS00002238": "PRJNA362687", # Oral microbial changes ASD
    }
    if source_db == "mgnify":
        mapped = mgnify_to_prj.get(accession)
        if mapped and mapped.upper() in seen_accessions:
            original = seen_accessions[mapped.upper()]
            return "exclude", "duplicate_dataset", f"MGnify {accession} maps to {mapped}, already screened (screening_id={original['screening_id']})"

    # ── Step 6: Control group check (E6) ──
    has_controls = bool(CONTROL_KEYWORDS.search(text))

    # Special: American Gut Project has non-ASD participants as controls
    if "american gut" in text.lower():
        has_controls = True

    # RCTs inherently have control arm
    is_rct = bool(re.search(r'\b(randomized|placebo[\s-]?controlled|double[\s-]?blind)\b', text, re.IGNORECASE))
    if is_rct:
        has_controls = True

    # "ASD and" or "ASD vs" implies comparison
    if re.search(r'\bASD\s+(and|vs|versus)\b', text, re.IGNORECASE):
        has_controls = True

    # Check for patterns like "X children with ASD and Y healthy/controls"
    if re.search(r'\d+\s+(ASD|autis\w+)\b.*\d+\s+(healthy|control|TD|neurotyp)', text, re.IGNORECASE):
        has_controls = True
    if re.search(r'\d+\s+(healthy|control|TD|neurotyp)\w*', text, re.IGNORECASE):
        has_controls = True

    if not has_controls:
        # Short description - mark as maybe, give benefit of doubt
        if len(description) < 80:
            return "maybe", "", "Short description; unclear if controls exist. Needs manual verification."

        # Intervention-only without controls
        is_intervention = bool(re.search(
            r'\b(FMT|fecal\s+microbiota\s+transplant|probiotic|supplementation|'
            r'washed\s+microbiota|open[\s-]?label|pilot)\b',
            text, re.IGNORECASE
        ))
        if is_intervention:
            return "exclude", "no_control_group", "Intervention study on ASD subjects without mention of control/comparison group"

        return "exclude", "no_control_group", "No mention of control/comparison group in description"

    # ── Step 7: Body site check (E7) ──
    body_site_re = re.compile(
        r'\b(gut|stool|fecal|faecal|feces|faeces|intestin|colon|rectal|'
        r'oral|saliva|tongue|buccal|mouth|skin|nasal|oropharyn)\b',
        re.IGNORECASE
    )
    has_body_site = bool(body_site_re.search(text))
    if any(x in org_lower for x in ["gut metagenome", "feces metagenome", "saliva metagenome"]):
        has_body_site = True

    if not has_body_site:
        if re.search(r'\b(microbiome|microbiota|16[sS]|metagenom)\b', text, re.IGNORECASE):
            # Most ASD microbiome studies are gut - give benefit of doubt
            return "maybe", "", "Body site not explicitly mentioned; likely gut but needs confirmation"
        return "maybe", "", "Body site cannot be determined from available metadata"

    # ── Step 8: Other exclusions ──
    # Genomic sequencing of isolates (not community)
    if re.search(r'\bgenomic\s+sequencing\s+of\s+(fecal\s+)?isolat', text, re.IGNORECASE):
        return "exclude", "not_microbiome_sequencing", "Genomic sequencing of bacterial isolates, not community microbiome profiling"
    if re.search(r'\bbacterial\s+strain\s+isolation\b', text, re.IGNORECASE):
        return "exclude", "not_microbiome_sequencing", "Bacterial strain isolation and genomics, not community microbiome profiling"

    # ── Step 9: All criteria passed → include ──
    return "include", "", ""


def main():
    screening_id_counter = 0
    seen_accessions = {}  # norm_acc -> {source_db, screening_id}
    all_rows = []

    for filename in SOURCE_FILES:
        filepath = os.path.join(SEARCH_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, skipping")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                screening_id_counter += 1
                scr_id = f"SCR{screening_id_counter:05d}"

                accession = row.get("accession", "").strip()
                norm_acc = normalize_accession(accession)

                decision, exclusion_reason, notes = screen_record(row, seen_accessions)

                # Register accession for dedup (only non-duplicates)
                if exclusion_reason != "duplicate_dataset":
                    if norm_acc and norm_acc not in seen_accessions:
                        seen_accessions[norm_acc] = {
                            "source_db": row.get("source_db", ""),
                            "screening_id": scr_id,
                        }

                all_rows.append({
                    "screening_id": scr_id,
                    "source_db": row.get("source_db", "").strip(),
                    "query_id": row.get("query_id", "").strip(),
                    "accession": accession,
                    "title": row.get("title", "").strip(),
                    "url": row.get("url", "").strip(),
                    "search_date": row.get("search_date", "").strip(),
                    "decision": decision,
                    "exclusion_reason": exclusion_reason,
                    "notes": notes,
                    "screened_by": "screening_agent",
                    "screening_round": 1,
                })

    # Write output
    fieldnames = [
        "screening_id", "source_db", "query_id", "accession", "title",
        "url", "search_date", "decision", "exclusion_reason", "notes",
        "screened_by", "screening_round"
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_rows)

    # ── Summary ──
    total = len(all_rows)
    includes = sum(1 for r in all_rows if r["decision"] == "include")
    excludes = sum(1 for r in all_rows if r["decision"] == "exclude")
    maybes = sum(1 for r in all_rows if r["decision"] == "maybe")

    print(f"\n{'='*60}")
    print(f"SCREENING SUMMARY")
    print(f"{'='*60}")
    print(f"Total records screened: {total}")
    print(f"  Include:  {includes}")
    print(f"  Exclude:  {excludes}")
    print(f"  Maybe:    {maybes}")
    print()

    reasons = {}
    for r in all_rows:
        if r["decision"] == "exclude" and r["exclusion_reason"]:
            reasons[r["exclusion_reason"]] = reasons.get(r["exclusion_reason"], 0) + 1

    print("Exclusion reasons:")
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    print("\nBy source database:")
    for src in ["bioproject", "ena", "geo", "mgnify", "qiita"]:
        src_rows = [r for r in all_rows if r["source_db"] == src]
        src_inc = sum(1 for r in src_rows if r["decision"] == "include")
        src_exc = sum(1 for r in src_rows if r["decision"] == "exclude")
        src_may = sum(1 for r in src_rows if r["decision"] == "maybe")
        print(f"  {src}: {len(src_rows)} total ({src_inc} include, {src_exc} exclude, {src_may} maybe)")

    # List included accessions
    print(f"\nIncluded studies ({includes}):")
    for r in all_rows:
        if r["decision"] == "include":
            print(f"  {r['screening_id']} | {r['source_db']:10s} | {r['accession']:15s} | {r['title'][:70]}")

    print(f"\nMaybe studies ({maybes}):")
    for r in all_rows:
        if r["decision"] == "maybe":
            print(f"  {r['screening_id']} | {r['source_db']:10s} | {r['accession']:15s} | {r['notes'][:70]}")

    print(f"\nOutput written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
