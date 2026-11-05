import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


# ---------------------------------------------------------
# PATHS AND DATASETS
# ---------------------------------------------------------

DATA_ROOT = Path.home() / "scr10/data_project"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
ANNOTATIONS_DIR = RESULTS_DIR / "annotations"

DATASETS = {
    "HIV": DATA_ROOT / "HIV" / "HIV",
    "HIV1": DATA_ROOT / "HIV" / "HIV1",
    "HIV2": DATA_ROOT / "HIV" / "HIV2",
    "Siminian-HIV": DATA_ROOT / "HIV" / "Siminian-HIV",
    "SIV": DATA_ROOT / "SIV" / "SIV",
}

REGIONS = ("env", "pol", "gag")
BATCH_SIZE = 100


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def safe_identifier(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def identify_region(cds_name, gene_name=""):
    """Map an NCBI CDS product name to an HIV/SIV region."""

    cds_name = (cds_name or "").strip().lower()
    gene_name = (gene_name or "").strip().lower()

    if re.search(r"\bgag[\s/-]+pol\b", cds_name):
        return None

    for name in (cds_name, gene_name):
        if re.search(r"\benv\b|envelope|gp160|gp120|gp41", name):
            return "env"

        if re.search(r"\bpol\b|polymerase|reverse transcriptase", name):
            return "pol"

        if re.search(r"\bgag\b|core protein|pr55", name):
            return "gag"

    return None


def read_accessions(report_path):
    """Read original nucleotide accession numbers."""

    accessions = []

    with report_path.open(encoding="utf-8") as report_file:
        for line_number, line in enumerate(report_file, start=1):
            if not line.strip():
                continue

            record = json.loads(line)
            accession = record.get("accession")

            if accession:
                accessions.append(accession)

    if not accessions:
        raise ValueError(f"No accessions found in {report_path}")

    return list(dict.fromkeys(accessions))


def read_local_genomes(fasta_path, accessions):
    """Match existing local genomic FASTA records to accessions."""

    expected = set(accessions)
    genomes = {}

    for record in SeqIO.parse(fasta_path, "fasta"):
        tokens = set(re.split(r"[\s|]+", record.description))

        for accession in tokens.intersection(expected):
            if accession in genomes:
                raise ValueError(
                    f"Duplicate local FASTA record for {accession}"
                )

            genomes[accession] = record

    missing = expected - set(genomes)

    if missing:
        examples = ", ".join(sorted(missing)[:10])
        raise ValueError(
            f"{len(missing)} accession(s) from the data report "
            f"were not found in {fasta_path}. Examples: {examples}"
        )

    return genomes


def parse_annotation_output(output):
    """Parse NCBI JSON Lines output, including wrapped JSON responses."""

    output = output.strip()

    if not output:
        return []

    try:
        parsed = json.loads(output)

        if isinstance(parsed, list):
            return parsed

        if isinstance(parsed, dict) and "reports" in parsed:
            return parsed["reports"]

        if isinstance(parsed, dict):
            return [parsed]

    except json.JSONDecodeError:
        pass

    records = []

    for line_number, line in enumerate(output.splitlines(), start=1):
        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Could not parse NCBI annotation output at "
                f"line {line_number}: {error}"
            ) from error

        if "reports" in record:
            records.extend(record["reports"])
        else:
            records.append(record)

    return records


def fetch_annotations(accessions, group):
    """Retrieve annotations for existing accessions using NCBI Datasets.

    Annotation reports are cached so subsequent runs can reuse them.
    """

    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = ANNOTATIONS_DIR / (
        f"{safe_identifier(group)}_annotation_report.jsonl"
    )

    if cache_file.is_file() and cache_file.stat().st_size > 0:
        print(f"Using cached annotations for {group}: {cache_file}")

        records = []

        with cache_file.open(encoding="utf-8") as annotation_file:
            for line in annotation_file:
                if line.strip():
                    records.append(json.loads(line))

        return records

    datasets_executable = shutil.which("datasets")

    if not datasets_executable:
        raise RuntimeError(
            "The NCBI 'datasets' CLI is unavailable. "
            "Load or activate the environment containing datasets."
        )

    print(
        f"Retrieving NCBI annotations for {group} "
        f"({len(accessions)} accessions)..."
    )

    all_records = []

    with tempfile.TemporaryDirectory() as temporary_directory:
        accession_file = Path(temporary_directory) / "accessions.txt"

        for start in range(0, len(accessions), BATCH_SIZE):
            batch = accessions[start:start + BATCH_SIZE]

            accession_file.write_text(
                "\n".join(batch) + "\n",
                encoding="utf-8",
            )

            command = [
                datasets_executable,
                "summary",
                "virus",
                "genome",
                "accession",
                "--inputfile",
                str(accession_file),
                "--report",
                "annotation",
                "--as-json-lines",
            ]

            api_key = os.environ.get("NCBI_API_KEY")

            if api_key:
                command.extend(["--api-key", api_key])

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"NCBI annotation retrieval failed for {group}.\n"
                    f"STDERR:\n{result.stderr}\n"
                    f"STDOUT:\n{result.stdout[:2000]}"
                )

            batch_records = parse_annotation_output(result.stdout)
            all_records.extend(batch_records)

            print(
                f"Retrieved annotations for batch "
                f"{start // BATCH_SIZE + 1}: "
                f"{len(batch_records)} record(s)"
            )

            time.sleep(0.4)

    if not all_records:
        raise ValueError(
            f"NCBI returned no annotation records for {group}."
        )

    with cache_file.open("w", encoding="utf-8") as output_file:
        for record in all_records:
            output_file.write(json.dumps(record) + "\n")

    print(f"Saved annotation cache to {cache_file}")

    return all_records


def extract_gene_sequence(genome, nucleotide):
    """Extract a gene using its NCBI genomic coordinates."""

    ranges = nucleotide.get("range", [])

    if not ranges:
        return None

    segments = sorted(
        ranges,
        key=lambda item: int(item["begin"]),
    )

    orientations = {
        str(segment.get("orientation", "plus")).lower()
        for segment in segments
    }

    if len(orientations) != 1:
        raise ValueError("Inconsistent gene segment orientations.")

    orientation = orientations.pop()

    if orientation not in ("plus", "minus"):
        raise ValueError(
            f"Unsupported gene orientation: {orientation}"
        )

    sequence_parts = []

    for segment in segments:
        begin = int(segment["begin"])
        end = int(segment["end"])

        if begin < 1 or end < begin or end > len(genome):
            raise ValueError(
                f"Invalid gene coordinates {begin}-{end} "
                f"for genome of length {len(genome)}"
            )

        # NCBI coordinates are 1-based and inclusive.
        sequence_parts.append(genome[begin - 1:end])

    sequence = Seq("").join(sequence_parts)

    if orientation == "minus":
        sequence = sequence.reverse_complement()

    return sequence


# ---------------------------------------------------------
# MAIN EXTRACTION WORKFLOW
# ---------------------------------------------------------

def main():

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    missing_dirs = [
        str(path)
        for path in DATASETS.values()
        if not path.is_dir()
    ]

    if missing_dirs:
        raise SystemExit(
            "Missing dataset directories:\n  "
            + "\n  ".join(missing_dirs)
        )

    sequences_by_region = {
        region: [] for region in REGIONS
    }

    counts = {
        region: {group: 0 for group in DATASETS}
        for region in REGIONS
    }

    for group, dataset_dir in DATASETS.items():

        print(f"\nProcessing dataset: {group}")

        report_path = (
            dataset_dir / "ncbi_dataset" / "data"
            / "data_report.jsonl"
        )

        fasta_path = (
            dataset_dir / "ncbi_dataset" / "data"
            / "genomic.fna"
        )

        if not report_path.is_file():
            raise FileNotFoundError(
                f"Missing data report: {report_path}"
            )

        if not fasta_path.is_file():
            raise FileNotFoundError(
                f"Missing genomic FASTA: {fasta_path}"
            )

        # Read the original accession selection.
        accessions = read_accessions(report_path)

        print(f"Original accessions: {len(accessions)}")

        # Use the genomes already downloaded.
        genomes = read_local_genomes(
            fasta_path,
            accessions,
        )

        # Retrieve or reuse NCBI gene annotations.
        annotation_records = fetch_annotations(
            accessions,
            group,
        )

        genomes_with_annotations = set()

        for annotation in annotation_records:

            accession = annotation.get("accession")

            if accession not in genomes:
                continue

            genomes_with_annotations.add(accession)

            genome = genomes[accession].seq

            for gene_number, gene in enumerate(
                annotation.get("genes", []),
                start=1,
            ):
                cds_features = gene.get("cds", [])
                if not cds_features and gene.get("nucleotide"):
                    cds_features = [gene]

                for cds_number, cds_feature in enumerate(
                    cds_features,
                    start=1,
                ):
                    region = identify_region(
                        cds_feature.get("name", ""),
                        gene.get("name", ""),
                    )

                    if region not in REGIONS:
                        continue

                    nucleotide = cds_feature.get("nucleotide")
                    if not nucleotide:
                        continue

                    sequence = extract_gene_sequence(
                        genome,
                        nucleotide,
                    )

                    if sequence is None or len(sequence) == 0:
                        continue

                    identifier = "__".join(
                        (
                            safe_identifier(group),
                            safe_identifier(accession),
                            f"{region}_{gene_number}_{cds_number}",
                        )
                    )

                    sequences_by_region[region].append(
                        SeqRecord(
                            sequence,
                            id=identifier,
                            description="",
                        )
                    )

                    counts[region][group] += 1

        print(
            f"Annotated genomes returned by NCBI: "
            f"{len(genomes_with_annotations)}"
        )

        for region in REGIONS:
            print(
                f"  {region}: {counts[region][group]} sequences"
            )

    # -----------------------------------------------------
    # WRITE SEQUENCE COUNTS
    # -----------------------------------------------------

    counts_path = RESULTS_DIR / "region_sequence_counts.csv"

    with counts_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as counts_file:

        writer = csv.DictWriter(
            counts_file,
            fieldnames=("region", "group", "sequence_count"),
        )

        writer.writeheader()

        for region in REGIONS:
            for group in DATASETS:

                writer.writerow(
                    {
                        "region": region,
                        "group": group,
                        "sequence_count": counts[region][group],
                    }
                )

    # -----------------------------------------------------
    # WRITE FASTA FILES
    # -----------------------------------------------------

    for region, sequences in sequences_by_region.items():

        if not sequences:
            raise SystemExit(
                f"No {region} CDS sequences were extracted "
                f"from the five datasets."
            )

        output_file = RESULTS_DIR / f"{region}.fasta"

        SeqIO.write(
            sequences,
            output_file,
            "fasta",
        )

        print(
            f"\nWrote {len(sequences)} {region} sequences "
            f"to {output_file}"
        )

        missing_groups = [
            group
            for group, count in counts[region].items()
            if count == 0
        ]

        if missing_groups:
            print(
                f"WARNING: No {region} CDS found for: "
                + ", ".join(missing_groups),
                file=sys.stderr,
            )

    print("\nGene extraction complete.")
    print(f"Results directory: {RESULTS_DIR}")


if __name__ == "__main__":
    main()