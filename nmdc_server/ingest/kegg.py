import csv
from pathlib import Path

from sqlalchemy.orm import Session

from nmdc_server.models import KoTermToModule


def load(db: Session) -> None:
    ingest_ko_module_map(db)


def ingest_ko_module_map(db: Session) -> None:
    db.execute(f"truncate table {KoTermToModule.__tablename__}")

    datafile = Path(__file__).parent / "data" / "ko_term_modules.tab.txt"
    with open(datafile) as fd:
        reader = csv.DictReader(fd, delimiter="\t")
        db.bulk_save_objects(
            [KoTermToModule(term=row["KO_id"], module=row["modules"]) for row in reader]
        )
        db.commit()
