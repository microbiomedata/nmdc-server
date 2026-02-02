import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from nmdc_server.schemas import AnnotationValue

JsonValueType = Dict[str, str]
EXCLUDED_FIELDS = {
    "_id",
    # Renamed and duplicated to "alternate_identifiers"
    "alternative_identifiers",
    # Unexpected Study fields
    "protocol_link",
    # Unexpected Biosample fields
    "gold_biosample_identifiers",
    "insdc_biosample_identifiers",
    "insdc_secondary_sample_identifiers",
    "gold_sequencing_project_identifiers",
    "emsl_biosample_identifiers",
    "igsn_biosample_identifiers",
    "img_identifiers",
}


class ETLReport:
    """A report about the ETL process."""

    def __init__(self, plural_subject: str = "Things"):
        self.plural_subject: str = plural_subject
        self.num_extracted: int = 0
        self.num_loaded: int = 0

    def __str__(self) -> str:
        """Get a single-line representation of the ETL report."""
        return (
            f"{self.plural_subject}: "
            f"extracted {self.num_extracted}, "
            f"loaded {self.num_loaded}."
        )

    def get_bullets(self) -> List[str]:
        """Get a list of bullet points representing the ETL report."""
        return [
            f"• {self.plural_subject}: extracted `{self.num_extracted}`, loaded `{self.num_loaded}`",
        ]


def coerce_value(value: Union[str, int, float]) -> AnnotationValue:
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()
        except ValueError:
            pass
    return value


def extract_value(value: Any) -> Any:
    # convert {"has_raw_value": <value>} -> <value>
    if isinstance(value, str):
        return value
    elif isinstance(value, dict) and "has_raw_value" in value:
        return coerce_value(value["has_raw_value"])
    return value


def extract_extras(
    cls: BaseModel, values: Dict[str, Any], exclude: Optional[Set[str]] = None
) -> Dict[str, Any]:
    # Move unknown attributes into values['annotations']
    fields = set(cls.model_fields.keys())
    exclude = (exclude or set()).union(EXCLUDED_FIELDS)
    values.setdefault("annotations", {})
    for key, value in values.items():
        if key not in fields and key not in exclude:
            values["annotations"][key] = extract_value(value)
    return values


def merge_download_artifact(ingest_db: Session, query):
    for row in query:
        ingest_db.merge(row)
        ingest_db.commit()


def maybe_merge_download_artifact(ingest_db: Session, query):
    logger = logging.getLogger()
    for row in query:
        try:
            ingest_db.merge(row)
            ingest_db.commit()
        except IntegrityError:
            logger.info("Error: data object with download history was removed.")
            ingest_db.rollback()
