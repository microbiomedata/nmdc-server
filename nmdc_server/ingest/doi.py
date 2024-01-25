import re

import requests
from requests.adapters import HTTPAdapter
from requests.models import Response
from requests.packages.urllib3.util.retry import Retry
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server.logger import get_logger
from nmdc_server.models import DOIInfo, DOIType

retry_strategy = Retry(total=10)
adapter = HTTPAdapter(max_retries=retry_strategy)


def get_doi_info(doi: str) -> Response:
    url = f"https://doi.org/{doi}"
    headers = {
        "Accept": "application/vnd.citationstyles.csl+json",
    }
    http = requests.Session()
    http.mount("https://", adapter)
    return requests.get(url, headers=headers, timeout=60)


def upsert_doi(db: Session, doi_value: str, doi_category: str, doi_provider: str=''):
    logger = get_logger(__name__)
    # Try really hard to get doi data... the doi.org service is very unreliable.
    try:
        # Search the doi string for an actual DOI, because it might be a URL or something else
        matched_doi = re.search(r"10.\d{4,9}/[-._;()/:A-Z0-9]+", doi_value, flags=re.IGNORECASE)
        if matched_doi is not None:
            data = get_doi_info(matched_doi.group(0))
            data.raise_for_status()
            info = data.json()
        else:
            info = {}
    except Exception:
        logger.exception(f"Failed to fetch {doi_value}")
        # don't add an entry if it already exists
        if db.query(DOIInfo).get(doi_value):
            return
        info = {}

    statement = insert(DOIInfo.__table__).values(id=doi_value, info=info, doi_type=DOIType(doi_category), doi_provider=doi_provider)
    statement = statement.on_conflict_do_update(constraint="pk_doi_info", set_=dict(info=info))
    db.execute(statement)
    db.flush()
