from sqlalchemy.orm import Session

from nmdc_server import models
from nmdc_server.ingest import study


def test_load_uses_principal_investigators_from_credit_associations(db: Session):
    source = {
        "id": "nmdc:sty-11-test",
        "name": "Study with multiple PIs",
        "description": "",
        "has_credit_associations": [
            {
                "applies_to_agent": {
                    "name": "Roberto Clemente",
                    "orcid": "orcid:0000-0000-0000-0001",
                },
                "applied_roles": ["Principal Investigator", "Project Manager"],
            },
            {
                "applies_to_agent": {"name": "Ichiro Suzuki"},
                "applied_roles": ["Principal Investigator"],
            },
            {
                "applies_to_agent": {"name": "Honus Wagner"},
                "applied_roles": ["Data Manager"],
            },
        ],
    }

    report = study.load(db, [source])  # type: ignore[arg-type]

    loaded = db.get(models.Study, "nmdc:sty-11-test")  # type: ignore[attr-defined]
    assert report.num_loaded == 1
    assert loaded is not None
    assert {pi.name for pi in loaded.principal_investigators} == {
        "Roberto Clemente",
        "Ichiro Suzuki",
    }
    assert loaded.has_credit_associations == source["has_credit_associations"]
