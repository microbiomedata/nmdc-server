import csv
from pathlib import Path
from typing import Dict, List, Union

import requests
from sqlalchemy.orm import Session

from nmdc_server.ingest.errors import errors
from nmdc_server.models import (
    CogTermToFunction,
    CogTermToPathway,
    KoTermText,
    KoTermToModule,
    KoTermToPathway,
)

ORTHOLOGY_URL = "https://www.genome.jp/kegg-bin/download_htext?htext=ko00001&format=json"
MODULE_URL = "https://www.genome.jp/kegg-bin/download_htext?htext=ko00002&format=json"

# Expect that this file is mounted from CORI /global/cfs/cdirs/m3408/kegg_pathway.tab.txt
PATHWAY_FILE = "/data/ingest/kegg/kegg_pathway.tab.txt"

# Ingest COG terms, pathways, and functions with these files
COG_FUNCTION_DEFS = "/data/ingest/cog/fun-20.tab"

# Note that we're using the same file for both COG terms and pathways
COG_PATHWAY_DEFS = COG_TERM_DEFS = "/data/ingest/cog/cog-20.def.tab"


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
    file,
    term_key,
    text_key,
    records,
    delimeter="\t",
    fallback_text_key=None,
    fieldnames=None,
):
    """
    Given a delimeted file containing term, pathway, module, etc. itentifiers and
    the corresponding text, append the pairs of identifiers and texts to a dictionary of
    records to be made into database objects for the ko_term_text table.
    """
    try:
        with open(file) as fd:
            for row in csv.DictReader(fd, fieldnames=fieldnames, delimiter=delimeter):
                if not row[term_key]:
                    continue
                if fallback_text_key:
                    records[row[term_key]] = row[text_key] or row[fallback_text_key]
                else:
                    records[row[term_key]] = row[text_key]
    except FileNotFoundError:
        errors["kegg_search"].add(f"Missing {file}")


cog_def_headers = [
    "cog_id",
    "cog_functional_category",
    "cog_name",
    "gene",
    "pathway",
    "pubmed_id",
    "pdb_id",
]

delimeted_files: Dict[str, Dict[str, Union[str, List[str]]]] = {
    PATHWAY_FILE: {
        "term_key": "image_id",
        "text_key": "title",
        "fallback_text_key": "pathway_name",
    },
    COG_FUNCTION_DEFS: {
        "fieldnames": ["function_code", "sequence", "definition"],
        "term_key": "function_code",
        "text_key": "definition",
    },
    COG_PATHWAY_DEFS: {
        "fieldnames": cog_def_headers,
        "term_key": "pathway",
        "text_key": "pathway",
    },
    COG_TERM_DEFS: {
        "fieldnames": cog_def_headers,
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
            fieldnames=keys.get("fieldnames", None),
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

    with open(COG_TERM_DEFS) as fd:
        reader = csv.DictReader(fd, fieldnames=cog_def_headers, delimiter="\t")
        records = []
        for row in reader:
            function_count = len(row.get("cog_functional_category", ""))
            if function_count > 1:
                for char in list(row["cog_functional_category"]):
                    records.append((row["cog_id"], char))
            elif function_count == 1:
                records.append((row["cog_id"], row["cog_functional_category"]))

        db.bulk_save_objects(
            [CogTermToFunction(term=record[0], function=record[1]) for record in records]
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

    with open(COG_TERM_DEFS) as fd:
        reader = csv.DictReader(fd, fieldnames=cog_def_headers, delimiter="\t")
        mappings = set([(row["cog_id"], row["pathway"]) for row in reader])
        db.bulk_save_objects(
            [CogTermToPathway(term=mapping[0], pathway=mapping[1]) for mapping in mappings]
        )
        db.commit()
