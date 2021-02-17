from logging import getLogger
from typing import Any, Dict

import requests
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server.models import DOIInfo

logger = getLogger(__name__)


def get_doi_info(doi: str) -> Dict[str, Any]:
    url = f"https://doi.org/{doi}"
    headers = {
        "Accept": "application/vnd.citationstyles.csl+json",
    }
    return requests.get(url, headers=headers).json()


def upsert_doi(db: Session, doi: str):
    try:
        info = get_doi_info(doi)
    except Exception:
        logger.exception(f"Failed to fetch {doi}")
        # don't add an entry if it already exists
        if db.query(DOIInfo).get(doi):
            return
        info = {}

    statement = insert(DOIInfo.__table__).values(id=doi, info=info)
    statement = statement.on_conflict_do_update(constraint="pk_doi_info", set_=dict(info=info))
    db.execute(statement)
    db.flush()
