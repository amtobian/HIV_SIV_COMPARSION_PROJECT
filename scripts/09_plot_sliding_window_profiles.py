import csv
import html
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
REGIONS = ("env", "pol", "gag")
GROUP_COLORS = (
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#17becf",
    "#e377c2",
    "#7f7f7f",
)
REQUIRED_COLUMNS = {
    "region",
    "group",
    "window_start",
    "window_end",
    "alignment_length",
    "pi_per_site",
    "mean_conservation_pct",
}


def read_profiles(path):
    with path.open(newline="", encoding="utf-8") as profile_file:
        reader = csv.DictReader(profile_file)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} must contain columns: " + ", ".join(sorted(REQUIRED_COLUMNS))
            )

        profiles = {
            region: {"pi_per_site": {}, "mean_conservation_pct": {}}
            for region in REGIONS
        }
        for line_number, row in enumerate(reader, start=2):
            region = row["region"]
            group = row["group"]
            if region not in profiles or not group:
                raise ValueError(f"Unexpected region or empty group in {path}:{line_number}")
            try:
                start = int(row["window_start"])
                end = int(row["window_end"])
                alignment_length = int(row["alignment_length"])
            except ValueError as error:
                raise ValueError(f"Invalid window coordinates in {path}:{line_number}") from error
            if start < 1 or end < start or end > alignment_length:
                raise ValueError(f"Window outside alignment in {path}:{line_number}")

            key = (group, start, end)
            for metric in ("pi_per_site", "mean_conservation_pct"):
                value_text = row[metric].strip()
                value = None
                if value_text:
                    try:
                        value = float(value_text)
                    except ValueError as error:
                        raise ValueError(
                            f"Invalid {metric} in {path}:{line_number}: {value_text!r}"
                        ) from error
                if key in profiles[region][metric]:
                    raise ValueError(f"Duplicate profile row in {path}:{line_number}")
                profiles[region][metric][key] = value

    if not any(profiles[region][metric] for region in REGIONS for metric in profiles[region]):
        raise ValueError(f"No sliding-window profile rows found in {path}")
    return profiles


def render_plot(region, metric, values):
    series = {}
    alignment_length = 0
    for (group, start, end), value in values.items():
        alignment_length = max(alignment_length, end)
        if value is not None:
            series.setdefault(group, []).append(((start + end) / 2, value))
    if not series:
        raise ValueError(f"No defined {metric} values for {region}")

    groups = sorted(series)
    for group in groups:
        series[group].sort()

    is_conservation = metric == "mean_conservation_pct"
    title = (
        f"{region.upper()} sliding-window conservation"
        if is_conservation
        else f"{region.upper()} sliding-window nucleotide diversity"
    )
    y_label = "Mean conservation (%)" if is_conservation else "Nucleotide diversity (π/site)"
    y_max = 100.0 if is_conservation else min(
        1.0, max(value for points in series.values() for _, value in points) * 1.1
    )
    y_max = max(y_max, 1.0 if is_conservation else 0.000001)

    width = 900
    left = 82
    right = 28
    top = 52
    bottom = 350
    plot_width = width - left - right
    plot_height = bottom - top
    x_max = max(alignment_length, 1)

    def x_position(position):
        return left + (position - 1) / max(x_max - 1, 1) * plot_width

    def y_position(value):
        return bottom - value / y_max * plot_height

    legend_columns = 2
    legend_row_height = 22
    legend_start_y = bottom + 76
    height = legend_start_y + (
        (len(groups) + legend_columns - 1) // legend_columns
    ) * legend_row_height + 20

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" role="img">'
        ),
        f"<title>{html.escape(title)}</title>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        (
            f'<text x="{width / 2}" y="30" text-anchor="middle" '
            'font-family="sans-serif" font-size="20" font-weight="bold">'
            f"{html.escape(title)}</text>"
        ),
    ]

    for tick in range(5):
        value = y_max * tick / 4
        y = y_position(value)
        label = f"{value:.0f}" if is_conservation else f"{value:.4f}"
        parts.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" '
                f'y2="{y:.2f}" stroke="#e5e7eb"/>',
                (
                    f'<text x="{left - 10}" y="{y:.2f}" text-anchor="end" '
                    'dominant-baseline="middle" font-family="sans-serif" '
                    f'font-size="11">{label}</text>'
                ),
            ]
        )

    parts.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#374151"/>',
            (
                f'<line x1="{left}" y1="{bottom}" x2="{width - right}" '
                f'y2="{bottom}" stroke="#374151"/>'
            ),
            (
                f'<text x="{left + plot_width / 2}" y="{bottom + 38}" '
                'text-anchor="middle" font-family="sans-serif" font-size="13">'
                "Alignment position (columns)</text>"
            ),
            (
                f'<text x="20" y="{top + plot_height / 2}" '
                f'transform="rotate(-90 20 {top + plot_height / 2})" '
                'text-anchor="middle" font-family="sans-serif" font-size="13">'
                f"{html.escape(y_label)}</text>"
            ),
        ]
    )

    for group_index, group in enumerate(groups):
        points = series[group]
        color = GROUP_COLORS[group_index % len(GROUP_COLORS)]
        point_text = " ".join(
            f"{x_position(position):.2f},{y_position(value):.2f}"
            for position, value in points
        )
        parts.append(
            f'<polyline points="{point_text}" fill="none" stroke="{color}" '
            'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        )

    legend_column_width = (width - left - right) / legend_columns
    for group_index, group in enumerate(groups):
        column = group_index % legend_columns
        row = group_index // legend_columns
        x = left + column * legend_column_width
        y = legend_start_y + row * legend_row_height
        color = GROUP_COLORS[group_index % len(GROUP_COLORS)]
        parts.extend(
            [
                f'<line x1="{x:.2f}" y1="{y}" x2="{x + 24:.2f}" y2="{y}" '
                f'stroke="{color}" stroke-width="3"/>',
                (
                    f'<text x="{x + 31:.2f}" y="{y}" '
                    'dominant-baseline="middle" font-family="sans-serif" '
                    f'font-size="12">{html.escape(group)}</text>'
                ),
            ]
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    input_path = RESULTS_DIR / "sliding_window_profiles.csv"
    profiles = read_profiles(input_path)
    for region in REGIONS:
        for metric, suffix in (
            ("pi_per_site", "nucleotide_diversity"),
            ("mean_conservation_pct", "conservation"),
        ):
            output_path = RESULTS_DIR / f"{region}_sliding_window_{suffix}.svg"
            output_path.write_text(
                render_plot(region, metric, profiles[region][metric]),
                encoding="utf-8",
            )
            print(f"Wrote sliding-window plot to {output_path}")


if __name__ == "__main__":
    main()
