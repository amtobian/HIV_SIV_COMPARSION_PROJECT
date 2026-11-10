import csv
import html
from itertools import combinations_with_replacement
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
REGIONS = ("env", "pol", "gag")
REQUIRED_COLUMNS = {
    "region",
    "group_a",
    "group_b",
    "pooled_percent_identity",
}
LOW_COLOR = (247, 251, 255)
HIGH_COLOR = (8, 81, 156)


def read_identity_summary(path):
    with path.open(newline="", encoding="utf-8") as summary_file:
        reader = csv.DictReader(summary_file)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} must contain columns: "
                + ", ".join(sorted(REQUIRED_COLUMNS))
            )

        groups = []
        identities = {region: {} for region in REGIONS}

        for line_number, row in enumerate(reader, start=2):
            region = row["region"]
            group_a = row["group_a"]
            group_b = row["group_b"]
            if region not in identities:
                raise ValueError(
                    f"Unexpected gene {region!r} in {path}:{line_number}"
                )
            if not group_a or not group_b:
                raise ValueError(
                    f"Missing viral group in {path}:{line_number}"
                )

            for group in (group_a, group_b):
                if group not in groups:
                    groups.append(group)

            identity_text = row["pooled_percent_identity"].strip()
            if identity_text:
                try:
                    identity = float(identity_text)
                except ValueError as error:
                    raise ValueError(
                        f"Invalid identity value in {path}:{line_number}: "
                        f"{identity_text!r}"
                    ) from error
                if not 0 <= identity <= 100:
                    raise ValueError(
                        f"Identity outside 0-100 in {path}:{line_number}: "
                        f"{identity}"
                    )
            else:
                identity = None

            key = frozenset((group_a, group_b))
            if key in identities[region]:
                raise ValueError(
                    f"Duplicate group comparison for {region}: "
                    f"{group_a} / {group_b}"
                )
            identities[region][key] = identity

    if not groups:
        raise ValueError(f"No pairwise identity rows found in {path}")

    expected_pairs = {
        frozenset(pair) for pair in combinations_with_replacement(groups, 2)
    }
    for region in REGIONS:
        missing_pairs = expected_pairs - set(identities[region])
        if missing_pairs:
            missing = sorted(tuple(sorted(pair)) for pair in missing_pairs)
            raise ValueError(
                f"Missing group comparisons for {region} in {path}: {missing}"
            )

    return groups, identities


def identity_color(identity):
    if identity is None:
        return "#e5e7eb"

    fraction = identity / 100
    color = tuple(
        round(start + (end - start) * fraction)
        for start, end in zip(LOW_COLOR, HIGH_COLOR)
    )
    return "#{:02x}{:02x}{:02x}".format(*color)


def render_heatmap(groups, identities):
    cell_size = 48
    grid_top = 112
    first_grid_x = 132
    panel_spacing = 435
    panel_width = len(groups) * cell_size
    width = first_grid_x + (len(REGIONS) - 1) * panel_spacing + panel_width + 150
    height = grid_top + panel_width + 220
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-labelledby="chart-title chart-description">'
        ),
        "<title id=\"chart-title\">Pairwise nucleotide identity by gene and viral group</title>",
        (
            "<desc id=\"chart-description\">Three heatmaps show pooled percent "
            "identity for every within-group and between-group comparison in "
            "env, pol, and gag.</desc>"
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        (
            f'<text x="{width / 2}" y="38" text-anchor="middle" '
            'font-family="sans-serif" font-size="22" font-weight="bold">'
            "Pairwise nucleotide identity by gene and viral group</text>"
        ),
    ]

    for region_index, region in enumerate(REGIONS):
        grid_x = first_grid_x + region_index * panel_spacing
        parts.append(
            f'<text x="{grid_x + panel_width / 2}" y="82" text-anchor="middle" '
            'font-family="sans-serif" font-size="18" font-weight="bold">'
            f"{html.escape(region.upper())}</text>"
        )

        for row_index, group_a in enumerate(groups):
            row_y = grid_top + row_index * cell_size
            parts.append(
                f'<text x="{grid_x - 12}" y="{row_y + cell_size / 2}" '
                'text-anchor="end" dominant-baseline="middle" '
                'font-family="sans-serif" font-size="12">'
                f"{html.escape(group_a)}</text>"
            )

            for column_index, group_b in enumerate(groups):
                column_x = grid_x + column_index * cell_size
                identity = identities[region][frozenset((group_a, group_b))]
                fill = identity_color(identity)
                label = "N/A" if identity is None else f"{identity:.1f}%"
                text_color = (
                    "#ffffff"
                    if identity is not None and identity >= 58
                    else "#111827"
                )
                tooltip = (
                    f"{region.upper()}: {group_a} vs {group_b}: "
                    f"{label} pooled identity"
                )
                parts.extend(
                    [
                        (
                            f'<rect x="{column_x}" y="{row_y}" '
                            f'width="{cell_size}" height="{cell_size}" '
                            f'fill="{fill}" stroke="#ffffff" stroke-width="1">'
                            f"<title>{html.escape(tooltip)}</title></rect>"
                        ),
                        (
                            f'<text x="{column_x + cell_size / 2}" '
                            f'y="{row_y + cell_size / 2}" text-anchor="middle" '
                            'dominant-baseline="middle" font-family="sans-serif" '
                            f'font-size="10" fill="{text_color}">'
                            f"{label}</text>"
                        ),
                    ]
                )

        label_y = grid_top + panel_width + 14
        for column_index, group in enumerate(groups):
            label_x = grid_x + column_index * cell_size + cell_size / 2
            parts.append(
                f'<text x="{label_x}" y="{label_y}" '
                f'transform="rotate(-45 {label_x} {label_y})" '
                'text-anchor="end" font-family="sans-serif" font-size="12">'
                f"{html.escape(group)}</text>"
            )

    legend_y = grid_top + panel_width + 105
    legend_x = first_grid_x + panel_spacing
    legend_width = panel_spacing
    parts.extend(
        [
            (
                f'<defs><linearGradient id="identity-scale" x1="0" x2="1">'
                f'<stop offset="0%" stop-color="{identity_color(0)}"/>'
                f'<stop offset="100%" stop-color="{identity_color(100)}"/>'
                "</linearGradient></defs>"
            ),
            (
                f'<text x="{legend_x + legend_width / 2}" y="{legend_y - 16}" '
                'text-anchor="middle" font-family="sans-serif" font-size="12">'
                "Pooled identity (%)</text>"
            ),
            (
                f'<rect x="{legend_x}" y="{legend_y}" width="{legend_width}" '
                'height="14" fill="url(#identity-scale)"/>'
            ),
        ]
    )
    for value, x in (
        (0, legend_x),
        (50, legend_x + legend_width / 2),
        (100, legend_x + legend_width),
    ):
        parts.append(
            f'<text x="{x}" y="{legend_y + 31}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="11">{value}%</text>'
        )

    note_y = legend_y + 62
    parts.append(
        f'<text x="{width / 2}" y="{note_y}" text-anchor="middle" '
        'font-family="sans-serif" font-size="12" fill="#374151">'
        "Identity is pooled across sequence pairs; gaps and ambiguous bases "
        "are excluded.</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    input_path = RESULTS_DIR / "region_pairwise_identity.csv"
    output_path = RESULTS_DIR / "region_pairwise_identity_heatmap.svg"
    groups, identities = read_identity_summary(input_path)
    output_path.write_text(
        render_heatmap(groups, identities),
        encoding="utf-8",
    )
    print(f"Wrote pairwise identity heatmap to {output_path}")


if __name__ == "__main__":
    main()
