from typing import Optional

from sqlalchemy.orm.session import Session

from nmdc_server import crud, models
from nmdc_server.query import FacetResponse

# (table name, field name) for globally searchable text
search_fields = [
    ("study", "principal_investigator_name"),
    ("biosample", "geo_loc_name"),
    # Envo
    ("biosample", "env_broad_scale"),
    ("biosample", "env_medium"),
    ("biosample", "env_local_scale"),
    # GOLD classification
    ("biosample", "ecosystem"),
    ("biosample", "ecosystem_category"),
    ("biosample", "ecosystem_type"),
    ("biosample", "ecosystem_subtype"),
    ("biosample", "specific_ecosystem"),
    ("omics_processing", "instrument_name"),
    ("omics_processing", "omics_type"),
    ("omics_processing", "processing_institution"),
]


def load(db: Session):
    db.execute(f"TRUNCATE TABLE {models.SearchIndex.__tablename__}")

    for table, field in search_fields:
        values: Optional[FacetResponse] = None

        if table == "study":
            values = crud.facet_study(db, field, [])
        elif table == "biosample":
            values = crud.facet_biosample(db, field, [])
        elif table == "omics_processing":
            values = crud.facet_omics_processing(db, field, [])

        if values is not None:
            for value in values.facets:
                assert type(value) is str, "Search value must be a string"
                db.add(
                    models.SearchIndex(
                        table=table,
                        value=value,
                        field=field,
                    )
                )
