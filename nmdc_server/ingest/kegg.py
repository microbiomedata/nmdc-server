import csv
from pathlib import Path
from typing import Dict

import requests
from sqlalchemy.orm import Session

from nmdc_server.models import KoTermText, KoTermToModule, KoTermToPathway

ORTHOLOGY_URL = "https://www.genome.jp/kegg-bin/download_htext?htext=ko00001&format=json"
MODULE_URL = "https://www.genome.jp/kegg-bin/download_htext?htext=ko00002&format=json"


def load(db: Session) -> None:
    ingest_ko_text(db)
    ingest_ko_module_map(db)
    ingest_ko_pathway_map(db)


def ingest_ko_text(db: Session) -> None:
    db.execute(f"truncate table {KoTermText.__tablename__}")

    req = requests.get(
        "https://www.genome.jp/kegg-bin/download_htext?htext=ko00001&format=json&filedir="
    )
    req.raise_for_status()

    records: Dict[str, str] = {}

    def ingest_tree(node: dict) -> None:
        if node["name"].startswith("K"):
            term, *text = node["name"].split("  ", maxsplit=1)
            records[term] = text[0] if text else ""

        for child in node.get("children", ()):
            ingest_tree(child)

    ingest_tree(req.json())

    db.bulk_save_objects([KoTermText(term=term, text=text) for term, text in records.items()])
    db.commit()


def ingest_ko_module_map(db: Session) -> None:
    db.execute(f"truncate table {KoTermToModule.__tablename__}")

    datafile = Path(__file__).parent / "data" / "ko_term_modules.tab.txt"
    with open(datafile) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToModule(term=row["KO_id"], module=row["modules"]) for row in reader]
        )
        db.commit()


def ingest_ko_pathway_map(db: Session) -> None:
    db.execute(f"truncate table {KoTermToPathway.__tablename__}")

    datafile = Path(__file__).parent / "data" / "ko_term_pathways.tab.txt"
    with open(datafile) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToPathway(term=row["KO_id"], pathway=row["image_id"]) for row in reader]
        )
        db.commit()
