import csv
from collections import Counter
from itertools import combinations_with_replacement
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
REGIONS = ("env", "pol", "gag")
BASES = frozenset("ACGT")


def read_fasta(path):
    records = []
    identifier = None
    sequence_parts = []

    def save_record():
        if identifier is None:
            return
        sequence = "".join(sequence_parts).upper().replace("U", "T")
        if not sequence:
            raise ValueError(f"Empty sequence for {identifier!r} in {path}")
        records.append((identifier, sequence))

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
                sequence_parts = []
            elif identifier is None:
                raise ValueError(f"Sequence before FASTA header at {path}:{line_number}")
            else:
                sequence_parts.append(line)
    save_record()
    if not records:
        raise ValueError(f"No FASTA records found in {path}")
    return records


def read_expected_counts(path):
    counts = {}
    with path.open(newline="", encoding="utf-8") as counts_file:
        for row in csv.DictReader(counts_file):
            counts.setdefault(row["region"], {})[row["group"]] = int(
                row["sequence_count"]
            )
    if not counts:
        raise ValueError(f"No dataset counts found in {path}")
    return counts


def summarize_alignment(records, groups):
    seen_identifiers = set()
    sequences_by_group = {group: [] for group in groups}
    for identifier, sequence in records:
        if identifier in seen_identifiers:
            raise ValueError(f"Duplicate aligned FASTA identifier: {identifier}")
        seen_identifiers.add(identifier)
        group, separator, _ = identifier.partition("__")
        if not separator or group not in sequences_by_group:
            raise ValueError(f"Unexpected dataset label in FASTA identifier: {identifier}")
        sequences_by_group[group].append(sequence)

    lengths = {len(sequence) for _, sequence in records}
    if len(lengths) != 1:
        raise ValueError("Aligned sequences do not all have the same length")
    alignment_length = lengths.pop()
    if alignment_length == 0:
        raise ValueError("Alignment contains zero-length sequences")

    rows = []
    for group_a, group_b in combinations_with_replacement(groups, 2):
        sequences_a = sequences_by_group[group_a]
        sequences_b = sequences_by_group[group_b]
        pair_count = (
            len(sequences_a) * (len(sequences_a) - 1) // 2
            if group_a == group_b
            else len(sequences_a) * len(sequences_b)
        )
        callable_sites = 0
        identical_sites = 0

        for column in range(alignment_length):
            counts_a = Counter(
                sequence[column]
                for sequence in sequences_a
                if sequence[column] in BASES
            )
            counts_b = (
                counts_a
                if group_a == group_b
                else Counter(
                    sequence[column]
                    for sequence in sequences_b
                    if sequence[column] in BASES
                )
            )

            if group_a == group_b:
                callable_sites += sum(counts_a.values()) * (
                    sum(counts_a.values()) - 1
                ) // 2
                identical_sites += sum(
                    count * (count - 1) // 2 for count in counts_a.values()
                )
            else:
                callable_sites += sum(counts_a.values()) * sum(counts_b.values())
                identical_sites += sum(
                    count * counts_b[base] for base, count in counts_a.items()
                )

        identity = (
            f"{100 * identical_sites / callable_sites:.6f}"
            if callable_sites
            else ""
        )
        rows.append(
            {
                "group_a": group_a,
                "group_b": group_b,
                "sequences_a": len(sequences_a),
                "sequences_b": len(sequences_b),
                "sequence_pairs": pair_count,
                "alignment_columns": alignment_length,
                "pairwise_callable_sites": callable_sites,
                "identical_sites": identical_sites,
                "pooled_percent_identity": identity,
            }
        )
    return rows, {group: len(items) for group, items in sequences_by_group.items()}


def main():
    counts_by_region = read_expected_counts(
        RESULTS_DIR / "region_sequence_counts.csv"
    )
    groups = list(next(iter(counts_by_region.values())))
    output_path = RESULTS_DIR / "region_pairwise_identity.csv"
    fieldnames = (
        "region",
        "group_a",
        "group_b",
        "sequences_a",
        "sequences_b",
        "sequence_pairs",
        "alignment_columns",
        "pairwise_callable_sites",
        "identical_sites",
        "pooled_percent_identity",
    )

    all_rows = []
    for region in REGIONS:
        if region not in counts_by_region:
            raise ValueError(f"No extracted sequence counts for {region}")
        expected_counts = counts_by_region[region]
        if set(expected_counts) != set(groups):
            raise ValueError(f"Inconsistent dataset groups for {region}")

        alignment = RESULTS_DIR / f"{region}.aln.fasta"
        rows, actual_counts = summarize_alignment(read_fasta(alignment), groups)
        if actual_counts != expected_counts:
            raise ValueError(
                f"Aligned sequence counts do not match extracted counts for "
                f"{region}: expected {expected_counts}, found {actual_counts}"
            )
        all_rows.extend({"region": region, **row} for row in rows)

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote pooled pairwise identity results to {output_path}")


if __name__ == "__main__":
    main()
