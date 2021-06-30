from typing import Optional

from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.data_object_filters import get_local_data_url
from nmdc_server.ingest.logger import get_logger
from nmdc_server.models import DataObject
from nmdc_server.schemas import DataObjectCreate

file_type_map = {
    "fastq.gz": "Raw output file",
    "filterStats.txt": "Reads QC summary statistics",
    "filtered.fastq.gz": "Reads QC result fastq (clean data)",
    "mapping_stats.txt": "Assembled contigs coverage information",
    "assembly_contigs.fna": "Final assembly contigs fasta",
    "assembly_scaffolds.fna": "Final assembly scaffolds fasta",
    "assembly.agp": "An AGP format file describes the assembly",
    "pairedMapped_sorted.bam": "Sorted bam file of reads mapping back to the final assembly",
    "KO TSV": "Tab delimited file for KO annotation.",
    "EC TSV": "Tab delimited file for EC annotation.",
    "Protein FAA": "FASTA amino acid file for annotated proteins.",
}


def derive_file_type(name: str) -> Optional[str]:
    for pattern in sorted(file_type_map, key=lambda n: len(n), reverse=True):
        if pattern in name:
            return file_type_map[pattern]
    return None


def load(db: Session, cursor: Cursor):
    logger = get_logger(__name__)
    fields = set(DataObjectCreate.__fields__.keys())
    for obj_ in cursor:
        obj = {key: obj_[key] for key in obj_.keys() & fields}

        # TODO: Remove once the source data is fixed.
        url = obj.get("url", "")
        if url and not get_local_data_url(url):
            logger.warning(
                f"Unknown url host '{url}', it need to be added to nginx config for bulk download"
            )
        if url.startswith("https://data.microbiomedata.org") and not url.startswith(
            "https://data.microbiomedata.org/data"
        ):
            obj["url"] = url.replace(
                "https://data.microbiomedata.org", "https://data.microbiomedata.org/data"
            )
        if "file_type" not in obj:
            obj["file_type"] = derive_file_type(obj["name"])

        db.add(DataObject(**obj))
