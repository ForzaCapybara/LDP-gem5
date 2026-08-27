#!/usr/bin/env python3
"""Render the loop-decoupling mechanism summary as a portable SVG."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPLICATIONS = [
    ("database_hj_m", "HJ-P"),
    ("database_gb_m", "GB"),
    ("graph_bfs_queue", "BFS"),
    ("graph_sssp_queue", "SSSP"),
    ("graph_mst_queue", "MST"),
]
PANELS = [
    ("coverage", "Coverage", 1.0),
    ("timeliness", "Timeliness", 1.0),
    ("speedup_over_nopf", "Speedup", None),
]


def load(path: Path) -> dict[tuple[str, str], float]:
    values: dict[tuple[str, str], float] = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["application"] == "overall":
                continue
            for metric, _, _ in PANELS:
                values[(row["application"], row["variant"], metric)] = float(
                    row[metric]
                )
    return values


def text(x: float, y: float, value: str, **attrs: object) -> str:
    attributes = " ".join(
        f'{name.replace("_", "-")}="{setting}"'
        for name, setting in attrs.items()
    )
    return f'<text x="{x:.1f}" y="{y:.1f}" {attributes}>{value}</text>'


def render(values: dict[tuple[str, str], float]) -> str:
    width, height = 960, 330
    margin_left, margin_top, panel_width, plot_height = 48, 48, 292, 220
    plot_width = 250
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        "<style>"
        "text{font-family:Arial,sans-serif;fill:#111}"
        ".axis{stroke:#111;stroke-width:1.5}"
        ".grid{stroke:#bbb;stroke-width:.7;stroke-dasharray:3 3}"
        ".no-loop{fill:#c8d0d6;stroke:#263238;stroke-width:1}"
        ".full{fill:#17232b}"
        "</style>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<rect x="300" y="14" width="14" height="14" class="no-loop"/>',
        text(320, 26, "No loop decoupling", font_size=14),
        '<rect x="500" y="14" width="14" height="14" class="full"/>',
        text(520, 26, "Loop decoupling", font_size=14),
    ]
    for panel_index, (metric, title, fixed_max) in enumerate(PANELS):
        x0 = margin_left + panel_index * panel_width
        y0 = margin_top + plot_height
        panel_values = [
            values.get((application, variant, metric), 0.0)
            for application, _ in APPLICATIONS
            for variant in ("no_loop", "full")
        ]
        y_max = fixed_max or max(3.0, math.ceil(max(panel_values) * 2) / 2)
        ticks = [0.0, y_max / 2, y_max]
        for tick in ticks:
            y = y0 - tick / y_max * plot_height
            parts.append(
                f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + plot_width}" '
                f'y2="{y:.1f}" class="grid"/>'
            )
            label = f"{tick * 100:.0f}%" if fixed_max else f"{tick:g}"
            parts.append(
                text(
                    x0 - 7,
                    y + 4,
                    label,
                    font_size=12,
                    text_anchor="end",
                )
            )
        parts.extend(
            [
                f'<line x1="{x0}" y1="{margin_top}" x2="{x0}" '
                f'y2="{y0}" class="axis"/>',
                f'<line x1="{x0}" y1="{y0}" x2="{x0 + plot_width}" '
                f'y2="{y0}" class="axis"/>',
                text(
                    x0 + plot_width / 2,
                    height - 14,
                    f"({chr(ord('a') + panel_index)}) {title}",
                    font_size=14,
                    text_anchor="middle",
                ),
            ]
        )
        group_width = plot_width / len(APPLICATIONS)
        bar_width = 15
        for app_index, (application, label) in enumerate(APPLICATIONS):
            center = x0 + group_width * (app_index + 0.5)
            for variant_index, variant in enumerate(("no_loop", "full")):
                value = values.get((application, variant, metric), 0.0)
                bar_height = max(0.0, value / y_max * plot_height)
                x = center + (variant_index - 1) * bar_width
                y = y0 - bar_height
                css_class = "no-loop" if variant == "no_loop" else "full"
                parts.append(
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" '
                    f'height="{bar_height:.1f}" class="{css_class}"/>'
                )
            parts.append(
                text(
                    center + 2,
                    y0 + 18,
                    label,
                    font_size=12,
                    text_anchor="end",
                    transform=f"rotate(-90 {center + 2:.1f} {y0 + 18:.1f})",
                )
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "m5out" / "analysis" / "mechanism_summary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "m5out" / "analysis" / "mechanism.svg",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(load(args.input)), encoding="utf-8")
    print(f"mechanism figure: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
