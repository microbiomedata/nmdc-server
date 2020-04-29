from datetime import datetime

import pytest
from sqlalchemy.orm.session import Session

from nmdc_server import fakes, query

date0 = datetime(1990, 1, 1)
date1 = datetime(2000, 1, 1)
date2 = datetime(2000, 1, 2)
date3 = datetime(2000, 1, 3)


@pytest.mark.parametrize(
    "condition,expected",
    [
        ({"field": "key1", "value": "value1", "op": "=="}, {"sample1", "sample2"}),
        ({"field": "key2", "value": "value2", "op": "=="}, {"sample1"}),
        ({"field": "key2", "value": "value", "op": ">"}, {"sample1", "sample2"}),
        ({"field": "key2", "value": "value", "op": "<"}, set()),
        ({"field": "key2", "value": "value2", "op": "!="}, {"sample2"}),
    ],
)
def test_string_query(db: Session, condition, expected):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    q = query.QuerySchema(table="sample", conditions=[condition])
    assert {s.id for s in q.execute(db)} == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        ({"field": "key1", "value": 1, "op": "=="}, {"sample1", "sample2"}),
        ({"field": "key2", "value": 2, "op": "=="}, {"sample1"}),
        ({"field": "key2", "value": 0, "op": ">"}, {"sample1", "sample2"}),
        ({"field": "key2", "value": 0, "op": "<"}, set()),
        ({"field": "key2", "value": 2, "op": "!="}, {"sample2"}),
    ],
)
def test_numeric_query(db: Session, condition, expected):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": 1, "key2": 2})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": 1, "key2": 3})
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    q = query.QuerySchema(table="sample", conditions=[condition])
    assert {s.id for s in q.execute(db)} == expected


@pytest.mark.parametrize(
    "condition,expected",
    [
        ({"field": "key1", "value": date1, "op": "=="}, {"sample1", "sample2"}),
        ({"field": "key2", "value": date2, "op": "=="}, {"sample1"}),
        ({"field": "key2", "value": date0, "op": ">"}, {"sample1", "sample2"}),
        ({"field": "key2", "value": date0, "op": "<"}, set()),
        ({"field": "key2", "value": date2, "op": "!="}, {"sample2"}),
    ],
)
def test_date_query(db: Session, condition, expected):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": date1, "key2": date2})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": date1, "key2": date3})
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    q = query.QuerySchema(table="sample", conditions=[condition])
    assert {s.id for s in q.execute(db)} == expected


@pytest.mark.parametrize(
    "table,condition,expected",
    [
        ("project", {"field": "sample_id", "value": "sample1", "op": "=="}, {"project1"}),
        ("sample", {"field": "project_id", "value": "project1", "op": "=="}, {"sample1"}),
        ("sample", {"field": "study_id", "value": "study1", "op": "=="}, {"sample2"}),
    ],
)
def test_foreign_key_search(db: Session, table, condition, expected):
    fakes.BiosampleFactory(id="sample1", project__id="project1")
    project = fakes.ProjectFactory(id="project2", study__id="study1")
    fakes.BiosampleFactory(id="sample2", project=project)
    db.commit()

    q = query.QuerySchema(table=table, conditions=[condition])
    assert {r.id for r in q.execute(db)} == expected


@pytest.mark.parametrize(
    "op,value,expected",
    [
        ("==", 0, {"sample1"}),
        ("<", 0, {"sample3"}),
        (">=", 0, {"sample1", "sample2"}),
        ("!=", 0, {"sample2", "sample3"}),
    ],
)
def test_latitude_query(db: Session, op, value, expected):
    fakes.BiosampleFactory(id="sample1", latitude=0)
    fakes.BiosampleFactory(id="sample2", latitude=10)
    fakes.BiosampleFactory(id="sample3", latitude=-10)
    db.commit()

    q = query.QuerySchema(
        table="sample", conditions=[{"field": "latitude", "op": op, "value": value}]
    )
    assert {r.id for r in q.execute(db)} == expected


def test_grouped_query(db: Session):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    fakes.BiosampleFactory(id="sample3", annotations={"key1": "value4", "key2": "value2"})
    db.commit()

    q = query.QuerySchema(
        table="sample",
        conditions=[
            {"field": "key2", "value": "value2", "op": "=="},
            {"field": "key1", "value": "value1", "op": "=="},
            {"field": "key2", "value": "value3", "op": "=="},
        ],
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}


def test_faceted_query(db: Session):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    fakes.BiosampleFactory(id="sample3", annotations={"key1": "value4", "key2": "value2"})
    db.commit()

    q = query.QuerySchema(table="sample", conditions=[])
    assert q.facet(db, "key1") == {"value1": 2, "value4": 1}
    assert q.facet(db, "key2") == {"value2": 2, "value3": 1}


def test_faceted_query_with_no_results(db: Session):
    q = query.QuerySchema(table="sample", conditions=[])
    assert q.facet(db, "key1") == {}
