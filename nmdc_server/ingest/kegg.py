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


def load(db: Session) -> None:
    ingest_ko_search(db)
    ingest_ko_module_map(db)
    ingest_ko_pathway_map(db)


def ingest_ko_search(db: Session) -> None:
    records = get_search_records()
    db.bulk_save_objects([KoTermText(term=term, text=text) for term, text in records.items()])
    db.flush()


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

    for file in [PATHWAY_FILE]:
        try:
            with open(file) as fd:
                for row in csv.DictReader(fd, delimiter="\t"):
                    records[row["image_id"]] = row["title"] or row["pathway_name"]
        except FileNotFoundError:
            errors["kegg_search"].add(f"Missing {file}")

    return records


def ingest_ko_module_map(db: Session) -> None:
    datafile = Path(__file__).parent / "data" / "ko_term_modules.tab.txt"
    with open(datafile) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToModule(term=row["KO_id"], module=row["modules"]) for row in reader]
        )
        db.flush()


def ingest_ko_pathway_map(db: Session) -> None:
    datafile = Path(__file__).parent / "data" / "ko_term_pathways.tab.txt"
    with open(datafile) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToPathway(term=row["KO_id"], pathway=row["image_id"]) for row in reader]
        )
        db.flush()
