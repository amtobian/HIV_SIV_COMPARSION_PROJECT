import argparse
import csv
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
REGIONS = ("env", "pol", "gag")
BASES = frozenset("ACGT")
ALL_GROUPS_LABEL = "ALL"
FIELDNAMES = (
    "region",
    "group",
    "window_start",
    "window_end",
    "n_sequences",
    "alignment_length",
    "callable_columns",
    "diversity_callable_columns",
    "pi_per_site",
    "mean_conservation_pct",
    "invariant_site_pct",
)


def read_alignment(path):
    sequences_by_group = {}
    seen_identifiers = set()
    identifier = None
    sequence_parts = []

    def save_record():
        if identifier is None:
            return
        sequence = "".join(sequence_parts).upper().replace("U", "T")
        if not sequence:
            raise ValueError(f"Empty sequence for {identifier!r} in {path}")
        group, separator, _ = identifier.partition("__")
        if not separator or not group:
            raise ValueError(
                f"Expected a group-prefixed FASTA identifier in {path}: "
                f"{identifier!r}"
            )
        if group == ALL_GROUPS_LABEL:
            raise ValueError(
                f"{ALL_GROUPS_LABEL!r} is reserved for the pooled group profile"
            )
        sequences_by_group.setdefault(group, []).append(sequence)

    with path.open(encoding="utf-8") as fasta_file:
        for line_number, line in enumerate(fasta_file, start=1):
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                save_record()
                identifier = line[1:].split(None, 1)[0]
                if not identifier:
                    raise ValueError(f"Empty FASTA identifier at {path}:{line_number}")
                if identifier in seen_identifiers:
                    raise ValueError(f"Duplicate FASTA identifier in {path}: {identifier}")
                seen_identifiers.add(identifier)
                sequence_parts = []
            elif identifier is None:
                raise ValueError(f"Sequence before FASTA header at {path}:{line_number}")
            else:
                sequence_parts.append(line)
    save_record()

    if not sequences_by_group:
        raise ValueError(f"No FASTA records found in {path}")

    lengths = {
        len(sequence)
        for sequences in sequences_by_group.values()
        for sequence in sequences
    }
    if len(lengths) != 1:
        raise ValueError(f"Aligned sequences do not all have the same length in {path}")
    alignment_length = lengths.pop()
    if alignment_length == 0:
        raise ValueError(f"Alignment contains zero-length sequences in {path}")

    return sequences_by_group, alignment_length


def window_ranges(alignment_length, window_size, step_size):
    if alignment_length <= window_size:
        return [(0, alignment_length)]

    windows = [
        (start, start + window_size)
        for start in range(0, alignment_length - window_size + 1, step_size)
    ]
    if windows[-1][1] < alignment_length:
        windows.append((alignment_length - window_size, alignment_length))
    return windows


def column_profiles(sequences):
    pi_by_column = []
    conservation_by_column = []
    invariant_by_column = []

    for column in zip(*sequences):
        counts = Counter(base for base in column if base in BASES)
        callable_count = sum(counts.values())
        if callable_count == 0:
            pi_by_column.append(None)
            conservation_by_column.append(None)
            invariant_by_column.append(None)
            continue

        largest_count = max(counts.values())
        conservation_by_column.append(largest_count / callable_count)
        invariant_by_column.append(
            float(largest_count == callable_count) if callable_count >= 2 else None
        )

        pair_count = callable_count * (callable_count - 1) // 2
        if pair_count:
            identical_pairs = sum(
                count * (count - 1) // 2 for count in counts.values()
            )
            pi_by_column.append((pair_count - identical_pairs) / pair_count)
        else:
            pi_by_column.append(None)

    return pi_by_column, conservation_by_column, invariant_by_column


def mean_defined(values):
    defined_values = [value for value in values if value is not None]
    return (
        sum(defined_values) / len(defined_values) if defined_values else None,
        len(defined_values),
    )


def format_value(value, multiplier=1):
    return "" if value is None else f"{value * multiplier:.6f}"


def summarize_region(region, sequences_by_group, alignment_length, window_size, step_size):
    group_sequences = dict(sequences_by_group)
    group_sequences[ALL_GROUPS_LABEL] = [
        sequence
        for sequences in sequences_by_group.values()
        for sequence in sequences
    ]
    windows = window_ranges(alignment_length, window_size, step_size)
    rows = []

    for group, sequences in group_sequences.items():
        pi_values, conservation_values, invariant_values = column_profiles(sequences)
        for start, end in windows:
            pi, diversity_callable_columns = mean_defined(pi_values[start:end])
            conservation, callable_columns = mean_defined(
                conservation_values[start:end]
            )
            invariant, _ = mean_defined(invariant_values[start:end])
            rows.append(
                {
                    "region": region,
                    "group": group,
                    "window_start": start + 1,
                    "window_end": end,
                    "n_sequences": len(sequences),
                    "alignment_length": alignment_length,
                    "callable_columns": callable_columns,
                    "diversity_callable_columns": diversity_callable_columns,
                    "pi_per_site": format_value(pi),
                    "mean_conservation_pct": format_value(conservation, 100),
                    "invariant_site_pct": format_value(invariant, 100),
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Calculate sliding-window diversity and conservation profiles."
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=100,
        help="Window width in alignment columns (default: 100).",
    )
    parser.add_argument(
        "--step-size",
        type=int,
        default=10,
        help="Distance between window starts in alignment columns (default: 10).",
    )
    args = parser.parse_args()
    if args.window_size < 1 or args.step_size < 1:
        parser.error("--window-size and --step-size must both be positive")

    all_rows = []
    for region in REGIONS:
        alignment_path = RESULTS_DIR / f"{region}.aln.fasta"
        if not alignment_path.is_file():
            raise FileNotFoundError(f"Required alignment not found: {alignment_path}")
        sequences_by_group, alignment_length = read_alignment(alignment_path)
        all_rows.extend(
            summarize_region(
                region,
                sequences_by_group,
                alignment_length,
                args.window_size,
                args.step_size,
            )
        )

    output_path = RESULTS_DIR / "sliding_window_profiles.csv"
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Wrote sliding-window profiles to {output_path}")


if __name__ == "__main__":
    main()
