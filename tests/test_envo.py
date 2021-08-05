from pathlib import Path

import pytest
from sqlalchemy.orm.session import Session

from nmdc_server.ingest.envo import build_envo_trees, nested_envo_trees
from nmdc_server.models import EnvoAncestor, EnvoTerm

data_dir = Path(__file__).parent / "data"


@pytest.fixture
def envo_data(db: Session):
    conn = db.bind.raw_connection()
    cursor = conn.cursor()
    sql = f"COPY {EnvoTerm.__tablename__} FROM STDIN WITH (FORMAT CSV, HEADER)"

    with (data_dir / "envo_terms.csv").open() as fd:
        cursor.copy_expert(sql, fd)

    sql = f"COPY {EnvoAncestor.__tablename__} FROM STDIN WITH (FORMAT CSV, HEADER)"

    with (data_dir / "envo_ancestors.csv").open() as fd:
        cursor.copy_expert(sql, fd)

    conn.commit()
    conn.close()


@pytest.mark.expensive
def test_envo_tree(envo_data, db: Session):
    build_envo_trees(db)
    trees = nested_envo_trees()
    assert set(trees.keys()) == {"env_broad_scale_id", "env_local_scale_id", "env_medium_id"}
    assert trees["env_broad_scale_id"].label == "ecosystem"
    assert trees["env_local_scale_id"].label == "astronomical body part"
    assert trees["env_medium_id"].label == "environmental material"
