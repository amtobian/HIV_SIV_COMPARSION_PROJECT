from pathlib import Path
import re

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

data_root = Path.home() / "scr10/data_project"
results_dir = Path("results")
results_dir.mkdir(parents=True, exist_ok=True)

genbank_files = list(data_root.rglob("*.gbff"))
if not genbank_files:
    raise SystemExit(f"No .gbff files found under {data_root}")

for gene in ("gag", "pol"):
    sequences = []

    for genbank_file in genbank_files:
        for record in SeqIO.parse(genbank_file, "genbank"):
            for feature_number, feature in enumerate(record.features, start=1):
                if feature.type != "CDS":
                    continue

                annotated_genes = [
                    value.lower()
                    for value in feature.qualifiers.get("gene", [])
                ]
                if gene not in annotated_genes:
                    continue

                source = str(genbank_file.relative_to(data_root))
                identifier = re.sub(
                    r"[^A-Za-z0-9_.-]+", "_",
                    f"{source}_{record.id}_{gene}_{feature_number}",
                )

                sequences.append(
                    SeqRecord(
                        feature.extract(record.seq),
                        id=identifier,
                        description="",
                    )
                )

    if not sequences:
        raise SystemExit(
            f"No CDS features annotated as gene={gene!r} were found. "
            "Check the GenBank feature annotations."
        )

    output_file = results_dir / f"{gene}.fasta"
    SeqIO.write(sequences, output_file, "fasta")
    print(f"Wrote {len(sequences)} {gene} sequences to {output_file}")