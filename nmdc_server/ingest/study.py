from typing import Optional

import requests
from pydantic import root_validator, validator
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.crud import create_study
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.doi import upsert_doi
from nmdc_server.models import PrincipalInvestigator
from nmdc_server.schemas import StudyCreate


def get_or_create_pi(db: Session, name: str, url: Optional[str], orcid: Optional[str]) -> str:
    pi = db.query(PrincipalInvestigator).filter_by(name=name).first()
    if pi:
        return pi.id

    image_data = None
    if url:
        r = requests.get(url)
        if r.ok:
            image_data = r.content

    pi = PrincipalInvestigator(name=name, image=image_data, orcid=orcid)

    db.add(pi)
    db.flush()
    return pi.id


class Study(StudyCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @root_validator(pre=True)
    def extract_extras(cls, values):
        return extract_extras(cls, values)


def load(db: Session, cursor: Cursor):
    for obj in cursor:
        pi_obj = obj.pop("principal_investigator")
        pi_name = pi_obj["has_raw_value"]
        pi_url = pi_obj.get("profile_image_url")
        pi_orcid = pi_obj.get("orcid")
        obj["principal_investigator_id"] = get_or_create_pi(db, pi_name, pi_url, pi_orcid)
        obj["principal_investigator_websites"] = obj.pop("websites", [])
        obj["publication_dois"] = [
            d.replace("https://doi.org/", "") for d in obj.pop("publications", [])
        ]

        if "doi" in obj:
            upsert_doi(db, obj["doi"]["has_raw_value"])
        for doi in obj.get("publication_dois", []):
            upsert_doi(db, doi)

        create_study(db, Study(**obj))
