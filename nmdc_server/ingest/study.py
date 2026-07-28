import re
from typing import List, Optional

import requests
from pydantic import model_validator
from pydantic.v1 import validator
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.crud import create_study, get_doi
from nmdc_server.ingest.common import ETLReport, extract_extras, extract_value
from nmdc_server.ingest.doi import upsert_doi
from nmdc_server.logger import get_logger
from nmdc_server.models import PrincipalInvestigator
from nmdc_server.schemas import StudyCreate

logger = get_logger(__name__)

# Define how long we want `requests` to wait (a) to establish a connection to the remote server,
# and (b) for the remote server to send the first (or any subsequent) byte of the response.
# Docs: https://docs.python-requests.org/en/latest/user/advanced/#timeouts
requests_timeout_for_connection = 5  # in seconds
requests_timeout_between_response_bytes = 20  # in seconds
requests_timeout: tuple = (requests_timeout_for_connection, requests_timeout_between_response_bytes)


def get_or_create_pi(db: Session, name: str, url: Optional[str], orcid: Optional[str]) -> str:
    pi = db.query(PrincipalInvestigator).filter_by(name=name).first()
    if pi:
        return pi.id

    image_data = None
    if url:
        try:
            r = requests.get(url, timeout=requests_timeout)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to download image for {name} from {url} : {e}")
        else:
            image_data = r.content

    pi = PrincipalInvestigator(name=name, image=image_data, orcid=orcid)

    db.add(pi)
    db.flush()
    return pi.id


class Study(StudyCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @model_validator(mode="before")
    def extract_extras(cls, values):
        return extract_extras(cls, values)  # type: ignore


def transform_doi(doi: str) -> str:
    matches = re.findall(r"10.\d{4,9}/[-._;()/:a-zA-Z0-9]+$", doi)
    return matches[0]


def get_study_image_data(image_urls: List[dict[str, str]]) -> Optional[bytes]:
    """
    Fetches and returns the data (bytes) from the URL in the "url" field of the first dictionary,
    if any, in the `image_urls` list. If the list is empty or the request fails, returns `None`.

    Note: If the first list item lacks a "url" field, this function raises a `KeyError`. I don't
          know what's special about the first list item—that was the original behavior and I am not
          prepared to modify it.
    """

    if image_urls:
        url = image_urls[0]["url"]
        try:
            response = requests.get(url, timeout=requests_timeout)
            response.raise_for_status()
            return response.content
        # Note: `requests.RequestException` accounts for not only `requests.HTTPError`, but also
        #       `requests.Timeout` (which we've encountered in production) and other exceptions.
        except requests.RequestException as e:
            logger.error(f"Failed to download image from '{url}': {e}")
    return None


def load(db: Session, cursor: Cursor) -> ETLReport:

    # Initialize the report we will return.
    report = ETLReport(plural_subject="Studies")

    for obj in cursor:

        # Update the report to account for this study having been extracted from the Mongo database.
        report.num_extracted += 1

        pi_obj = obj.pop("principal_investigator", None)
        if pi_obj:
            if "name" in pi_obj:
                pi_name = pi_obj["name"]
            else:
                pi_name = pi_obj["has_raw_value"]
            pi_url = pi_obj.get("profile_image_url")
            pi_orcid = pi_obj.get("orcid")
            obj["principal_investigator_id"] = get_or_create_pi(db, pi_name, pi_url, pi_orcid)
            obj["principal_investigator_websites"] = obj.pop("websites", [])
            obj["pricipal_investigator_image_url"] = pi_url
        obj["image"] = get_study_image_data(obj.pop("study_image", []))
        dois = obj.pop("associated_dois", None)
        if dois:
            for doi in dois:
                doi["doi_value"] = transform_doi(doi.pop("doi_value"))

            for doi in dois:
                upsert_doi(
                    db,
                    doi_value=doi["doi_value"],
                    doi_category=doi["doi_category"],
                    doi_provider=doi.get("doi_provider", ""),
                )

        protocol_links = obj.pop("protocol_link", None)
        if protocol_links:
            obj["protocol_link"] = [p["url"] for p in protocol_links if "url" in p]

        new_study = create_study(db, Study(**obj))

        # Update the report to account for this study having been loaded into the ingest database.
        report.num_loaded += 1

        if dois:
            for doi in dois:
                doi_object = get_doi(db, doi["doi_value"])
                if doi_object:
                    new_study.dois.append(doi_object)

    return report
