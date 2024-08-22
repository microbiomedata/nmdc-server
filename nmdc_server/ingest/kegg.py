import csv
from pathlib import Path
from typing import Dict

import requests
from sqlalchemy.orm import Session

from nmdc_server.ingest.errors import errors
from nmdc_server.models import KoTermText, KoTermToModule, KoTermToPathway

ORTHOLOGY_URL = "https://www.genome.jp/kegg-bin/download_htext?htext=ko00001&format=json"
MODULE_URL = "https://www.genome.jp/kegg-bin/download_htext?htext=ko00002&format=json"

# Expect that this file is mounted from CORI /global/cfs/cdirs/m3408/kegg_pathway.tab.txt
PATHWAY_FILE = "/data/ingest/kegg/kegg_pathway.tab.txt"

# Ingest COG terms, pathways, and functions with these files
COG_PATHWAY_DEFS = "/data/ingest/cog/cog_pathway.txt"
COG_FUNCTION_DEFS = "/data/ingest/cog/cog_function.txt"
COG_TERM_DEFS = "/data/ingest/cog/cog.txt"

COG_FUNCTION_MAPPINGS = "/data/ingest/cog/cog2functions.txt"
COG_PATHWAY_MAPPINGS = "/data/ingest/cog/cog_pathway_cog_members.txt"


def load(db: Session) -> None:
    ingest_ko_search(db)
    ingest_ko_module_map(db)
    ingest_ko_pathway_map(db)


def ingest_ko_search(db: Session) -> None:
    db.execute(f"truncate table {KoTermText.__tablename__}")
    records = get_search_records()
    db.bulk_save_objects([KoTermText(term=term, text=text) for term, text in records.items()])
    db.commit()


def get_search_records_from_delimeted_file(
    file, term_key, text_key, records, delimeter="\t", fallback_text_key=None
):
    """
    Given a delimeted file containing term, pathway, module, etc. itentifiers and
    the corresponding text, append the pairs of identifiers and texts to a dictionary of
    records to be made into database objects for the ko_term_text table.
    """
    try:
        with open(file) as fd:
            for row in csv.DictReader(fd, delimiter=delimeter):
                if fallback_text_key:
                    records[row[term_key]] = row[text_key] or row[fallback_text_key]
                else:
                    records[row[term_key]] = row[text_key]
    except FileNotFoundError:
        errors["kegg_search"].add(f"Missing {file}")


delimeted_files = {
    PATHWAY_FILE: {
        "term_key": "image_id",
        "text_key": "title",
        "fallback_text_key": "pathway_name",
    },
    COG_FUNCTION_DEFS: {
        "term_key": "function_code",
        "text_key": "definition",
    },
    COG_PATHWAY_DEFS: {
        "term_key": "cog_pathway_oid",
        "text_key": "cog_pathway_name",
    },
    COG_TERM_DEFS: {
        "term_key": "cog_id",
        "text_key": "cog_name",
    },
}


def get_search_records():
    records: Dict[str, str] = {}

    def ingest_tree(node: dict) -> None:
        if not node.get("children", False):
            term, *text = node["name"].split("  ", maxsplit=1)
            records[term] = text[0] if text else ""

        for child in node.get("children", ()):
            ingest_tree(child)

    for url in [MODULE_URL, ORTHOLOGY_URL]:
        req = requests.get(url)
        req.raise_for_status()
        ingest_tree(req.json())

    for file, keys in delimeted_files.items():
        get_search_records_from_delimeted_file(
            file,
            keys["term_key"],
            keys["text_key"],
            records,
            fallback_text_key=keys.get("fallback_text_key", None),
        )
    return records


def ingest_ko_module_map(db: Session) -> None:
    """Ingest a mapping of KEGG modules to terms and COG functions to terms."""
    db.execute(f"truncate table {KoTermToModule.__tablename__}")

    datafile = Path(__file__).parent / "data" / "kegg_module_ko_terms.tab.txt"
    with open(datafile) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToModule(term=row["ko_terms"], module=row["module_id"]) for row in reader]
        )
        db.commit()

    with open(COG_FUNCTION_MAPPINGS) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToModule(term=row["cog_id"], module=row["functions"]) for row in reader]
        )
        db.commit()


def ingest_ko_pathway_map(db: Session) -> None:
    """Ingest a mapping of KEGG pathways to terms and COG pathways to COG terms."""
    db.execute(f"truncate table {KoTermToPathway.__tablename__}")

    datafile = Path(__file__).parent / "data" / "ko_term_pathways.tab.txt"
    with open(datafile) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToPathway(term=row["KO_id"], pathway=row["image_id"]) for row in reader]
        )
        db.commit()

    with open(COG_PATHWAY_MAPPINGS) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        mappings = set([(row["cog_members"], row["cog_pathway_oid"]) for row in reader])
        db.bulk_save_objects(
            [KoTermToPathway(term=mapping[0], pathway=mapping[1]) for mapping in mappings]
        )
        db.commit()
