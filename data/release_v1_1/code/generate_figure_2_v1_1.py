from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Frozen_v1.1" / "datasets_release_v1_1_extended.csv"
OUTPUT_DIR = ROOT / "Manuscript" / "Fig"
OUTPUT_STEM = OUTPUT_DIR / "Landscape Of Included Dataset Records"
SOURCE_DATA = OUTPUT_DIR / "Figure_2_source_data_v1_1.csv"

EXPECTED_N = 70

PANEL_CONFIG = [
    (
        "A",
        "Study country",
        "country",
        {},
    ),
    (
        "B",
        "Normalized body site",
        "body_site",
        {
            "stool": "Stool",
            "oral": "Oral",
            "gut": "Gut",
            "gut;oral": "Gut and oral",
        },
    ),
    (
        "C",
        "Assay classification",
        "assay_type",
        {
            "16S": "16S",
            "metagenome": "Metagenome",
            "multi_amplicon": "Multi-amplicon",
            "multi_assay": "Multi-assay",
            "multi_omic": "Multi-omic",
            "shotgun": "Shotgun",
        },
    ),
    (
        "D",
        "Study design",
        "study_design",
        {
            "case_control": "Case-control",
            "intervention": "Intervention",
            "cross_sectional": "Cross-sectional",
        },
    ),
]


def load_rows() -> list[dict[str, str]]:
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_N:
        raise ValueError(f"Expected {EXPECTED_N} records, found {len(rows)}")
    return rows


def panel_counts(
    rows: list[dict[str, str]], field: str, labels: dict[str, str]
) -> list[tuple[str, int, str]]:
    counts = Counter(row[field].strip() for row in rows)
    if "" in counts:
        raise ValueError(f"Blank value found in required Figure 2 field: {field}")
    unknown = set(counts) - set(labels) if labels else set()
    if unknown:
        raise ValueError(f"Unexpected {field} categories: {sorted(unknown)}")

    items = []
    for raw_value, count in counts.items():
        display = labels.get(raw_value, raw_value)
        items.append((display, count, raw_value))
    return sorted(items, key=lambda item: (-item[1], item[0]))


def style_axis(ax: plt.Axes) -> None:
    ax.set_xlim(0, EXPECTED_N)
    ax.set_xlabel("Count (percentage of 70)", fontsize=10)
    ax.tick_params(axis="both", labelsize=9)
    ax.xaxis.grid(True, linestyle=(0, (4, 4)), color="#D7DCE2", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#202020")
        spine.set_linewidth(0.8)


def draw_panel(
    ax: plt.Axes,
    panel_letter: str,
    title: str,
    data: list[tuple[str, int, str]],
) -> None:
    labels = [item[0] for item in data]
    counts = [item[1] for item in data]
    raw_values = [item[2] for item in data]
    colors = [
        "#009E73" if (";" in raw or raw.startswith("multi_")) else "#3C78B5"
        for raw in raw_values
    ]

    bars = ax.barh(labels, counts, color=colors, edgecolor="none", height=0.62)
    ax.invert_yaxis()
    style_axis(ax)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.text(
        -0.055,
        1.04,
        panel_letter,
        transform=ax.transAxes,
        fontsize=19,
        fontweight="bold",
        va="bottom",
        ha="right",
    )

    for bar, count in zip(bars, counts):
        percent = count / EXPECTED_N * 100
        ax.text(
            count + 0.55,
            bar.get_y() + bar.get_height() / 2,
            f"{count} ({percent:.1f}%)",
            va="center",
            ha="left",
            fontsize=9,
            color="#111111",
        )


def write_source_data(
    panels: list[tuple[str, str, list[tuple[str, int, str]]]]
) -> None:
    with SOURCE_DATA.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["panel", "characteristic", "category", "count", "percent", "denominator"],
        )
        writer.writeheader()
        for panel_letter, title, data in panels:
            for display, count, _ in data:
                writer.writerow(
                    {
                        "panel": panel_letter,
                        "characteristic": title,
                        "category": display,
                        "count": count,
                        "percent": f"{count / EXPECTED_N * 100:.1f}",
                        "denominator": EXPECTED_N,
                    }
                )


def main() -> None:
    rows = load_rows()
    panels = [
        (letter, title, panel_counts(rows, field, labels))
        for letter, title, field, labels in PANEL_CONFIG
    ]

    study_design = {name: count for name, count, _ in panels[3][2]}
    expected_design = {"Case-control": 58, "Intervention": 8, "Cross-sectional": 4}
    if study_design != expected_design:
        raise ValueError(f"Unexpected study-design counts: {study_design}")

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    fig = plt.figure(figsize=(15, 10.2))
    grid = fig.add_gridspec(
        2,
        6,
        height_ratios=[1.35, 1.0],
        left=0.13,
        right=0.985,
        top=0.86,
        bottom=0.12,
        hspace=0.34,
        wspace=0.34,
    )
    axes = [
        fig.add_subplot(grid[0, :]),
        fig.add_subplot(grid[1, 0:2]),
        fig.add_subplot(grid[1, 2:4]),
        fig.add_subplot(grid[1, 4:6]),
    ]

    for ax, (letter, title, data) in zip(axes, panels):
        draw_panel(ax, letter, title, data)

    fig.suptitle(
        "Figure 2. Landscape of Included Dataset Records",
        fontsize=21,
        fontweight="bold",
        y=0.965,
    )
    fig.text(
        0.5,
        0.91,
        "Accession-level records, N=70",
        ha="center",
        va="center",
        fontsize=13,
    )
    fig.text(
        0.07,
        0.055,
        "Figure 2. ",
        ha="left",
        va="center",
        fontsize=10.5,
        fontweight="bold",
    )
    fig.text(
        0.122,
        0.055,
        "Geographic, anatomical, methodological, and study-design characteristics of the 70 accession-level "
        "dataset records included in the ASD Microbiome Atlas v1.1.",
        ha="left",
        va="center",
        fontsize=10.5,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_source_data(panels)
    fig.savefig(OUTPUT_STEM.with_suffix(".png"), dpi=300)
    fig.savefig(OUTPUT_STEM.with_suffix(".pdf"))
    fig.savefig(OUTPUT_STEM.with_suffix(".svg"))
    plt.close(fig)

    print(f"Wrote {OUTPUT_STEM.with_suffix('.png').relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_STEM.with_suffix('.pdf').relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_STEM.with_suffix('.svg').relative_to(ROOT)}")
    print(f"Wrote {SOURCE_DATA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
