import re
from typing import Optional

import requests
from pydantic import model_validator
from pydantic.v1 import validator
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.crud import create_study, get_doi
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.doi import upsert_doi
from nmdc_server.logger import get_logger
from nmdc_server.models import PrincipalInvestigator
from nmdc_server.schemas import StudyCreate

logger = get_logger(__name__)


def get_or_create_pi(db: Session, name: str, url: Optional[str], orcid: Optional[str]) -> str:
    pi = db.query(PrincipalInvestigator).filter_by(name=name).first()
    if pi:
        return pi.id

    image_data = None
    if url:
        try:
            r = requests.get(url)
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
        return extract_extras(cls, values)


List = list
Study.model_rebuild()


def transform_doi(doi: str) -> str:
    matches = re.findall(r"10.\d{4,9}/[-._;()/:a-zA-Z0-9]+$", doi)
    return matches[0]


def get_study_image_data(image_urls: list[dict[str, str]]) -> Optional[bytes]:
    if image_urls:
        r = requests.get(image_urls[0]["url"])
        if r.ok:
            return r.content
    return None


def load(db: Session, cursor: Cursor):
    for obj in cursor:
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
            obj["relevant_protocols"] = [p["url"] for p in protocol_links if "url" in p]

        study = Study(**obj)
        new_study = create_study(db, Study(**obj))
        if dois:
            for doi in dois:
                doi_object = get_doi(db, doi["doi_value"])
                if doi_object:
                    new_study.dois.append(doi_object)  # type: ignore
