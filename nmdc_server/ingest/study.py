import re
from typing import Optional

import requests
from pydantic import root_validator, validator
from pymongo.cursor import Cursor
from sqlalchemy.orm import Session

from nmdc_server.crud import create_study, get_doi
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.doi import upsert_doi
from nmdc_server.models import DOIType, PrincipalInvestigator
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
        obj["image"] = get_study_image_data(obj.pop("study_image", []))

        publication_dois = [transform_doi(d) for d in obj.pop("publications", [])] + [
            transform_doi(d) for d in obj.pop("publication_dois", [])
        ]
        award_dois = [transform_doi(doi) for doi in obj.pop("award_dois", [])] + [
            transform_doi(d) for d in obj.pop("emsl_project_dois", [])
        ]
        dataset_dois = [transform_doi(doi) for doi in obj.pop("dataset_dois", [])]

        for doi in publication_dois:
            upsert_doi(db, doi, DOIType.PUBLICATION)

        for doi in award_dois:
            upsert_doi(db, doi, DOIType.AWARD)

        for doi in dataset_dois:
            upsert_doi(db, doi, DOIType.DATASET)

        new_study = create_study(db, Study(**obj))

        for doi_id in publication_dois + award_dois + dataset_dois:
            doi_object = get_doi(db, doi_id)
            if doi_object:
                new_study.dois.append(doi_object)  # type: ignore
