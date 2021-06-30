import json
from pathlib import Path
from typing import Optional

from pydantic import root_validator, validator
from pymongo.cursor import Cursor
import requests
from sqlalchemy.orm import Session

from nmdc_server.crud import create_study
from nmdc_server.ingest.common import extract_extras, extract_value
from nmdc_server.ingest.doi import upsert_doi
from nmdc_server.ingest.logger import get_logger
from nmdc_server.models import PrincipalInvestigator
from nmdc_server.schemas import StudyCreate

HERE = Path(__file__).parent
IMAGES = HERE / "pis"


with (HERE / "study_additional.json").open("r") as f:
    study_additional = {f"gold:{d['id']}": d for d in json.load(f)}


def get_or_create_pi(db: Session, name: str, url: Optional[str]) -> str:
    pi = db.query(PrincipalInvestigator).filter_by(name=name).first()
    if pi:
        return pi.id

    image_data = None
    if url:
        r = requests.get(url)
        if r.ok:
            image_data = r.content

    pi = PrincipalInvestigator(name=name, image=image_data)

    db.add(pi)
    db.flush()
    return pi.id


class Study(StudyCreate):
    _extract_value = validator("*", pre=True, allow_reuse=True)(extract_value)

    @root_validator(pre=True)
    def extract_extras(cls, values):
        return extract_extras(cls, values)


def load(db: Session, cursor: Cursor):
    logger = get_logger(__name__)

    for obj in cursor:
        pi_obj = obj.pop("principal_investigator")
        pi_name = pi_obj["has_raw_value"]
        pi_url = pi_obj.get("profile_image_url")
        obj["principal_investigator_id"] = get_or_create_pi(db, pi_name, pi_url)

        if obj["id"] in study_additional:
            a = study_additional[obj["id"]]
            obj["name"] = a["proposal_title"]
            obj["principal_investigator_websites"] = a["principal_investigator_websites"]
            obj["publication_dois"] = a["publication_dois"]
            obj["scientific_objective"] = a["scientific_objective"]
        else:
            logger.warning(f"additional study data not found for {obj['id']}")

        if "doi" in obj:
            upsert_doi(db, obj["doi"]["has_raw_value"])
        for doi in obj.get("publication_dois", []):
            upsert_doi(db, doi)

        create_study(db, Study(**obj))
