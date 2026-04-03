#!/usr/bin/env python3
"""Generate PRISMA 2020 flow diagram data from screening_log.csv and search_results."""

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    # Load search results per source
    search_dir = DATA / "search_results"
    source_counts: dict[str, int] = {}
    if search_dir.exists():
        for csv_file in sorted(search_dir.glob("*.csv")):
            rows = load_csv(csv_file)
            source_counts[csv_file.stem] = len(rows)

    total_identified = sum(source_counts.values())

    # Load screening log
    screening = load_csv(DATA / "screening_log.csv")
    decisions = Counter(r.get("decision", "") for r in screening)
    reasons = Counter(
        r.get("exclusion_reason", "")
        for r in screening
        if r.get("decision") == "exclude"
    )

    n_duplicates = reasons.get("duplicate_dataset", 0)
    n_screened = len(screening)
    n_excluded = decisions.get("exclude", 0)
    n_included = decisions.get("include", 0)
    n_maybe = decisions.get("maybe", 0)

    # Load datasets
    datasets = load_csv(DATA / "datasets.csv")

    # Print PRISMA flow
    print("=" * 60)
    print("PRISMA 2020 Flow Diagram — ASD Microbiome Atlas v1.0")
    print("=" * 60)

    print("\n┌─────────────────────────────────────────┐")
    print("│           IDENTIFICATION                 │")
    print("├─────────────────────────────────────────┤")
    for source, count in sorted(source_counts.items()):
        print(f"│  {source:<30} {count:>5}  │")
    print(f"│  {'TOTAL':<30} {total_identified:>5}  │")
    print("└─────────────────────────────────────────┘")
    print("                    │")
    print(f"    Duplicates removed: {n_duplicates}")
    print("                    │")
    print("                    ▼")
    print("┌─────────────────────────────────────────┐")
    print("│             SCREENING                    │")
    print("├─────────────────────────────────────────┤")
    print(f"│  Records screened        {n_screened:>10}     │")
    print(f"│  Records excluded        {n_excluded:>10}     │")
    for reason, count in sorted(reasons.items()):
        if reason:
            print(f"│    - {reason:<26} {count:>5}     │")
    if n_maybe > 0:
        print(f"│  Pending (maybe)         {n_maybe:>10}     │")
    print("└─────────────────────────────────────────┘")
    print("                    │")
    print("                    ▼")
    print("┌─────────────────────────────────────────┐")
    print("│              INCLUDED                    │")
    print("├─────────────────────────────────────────┤")
    print(f"│  Studies in atlas        {n_included:>10}     │")
    print(f"│  Rows in datasets.csv    {len(datasets):>10}     │")
    print("└─────────────────────────────────────────┘")

    # Body site breakdown
    if datasets:
        body_sites = Counter(r.get("body_site", "unknown") for r in datasets)
        seq_types = Counter(r.get("sequencing_type", "unknown") for r in datasets)

        print("\n--- Included Studies Breakdown ---")
        print("\nBy body site:")
        for site, count in body_sites.most_common():
            print(f"  {site:<20} {count:>4}")
        print("\nBy sequencing type:")
        for stype, count in seq_types.most_common():
            print(f"  {stype:<20} {count:>4}")

    print()


if __name__ == "__main__":
    main()
