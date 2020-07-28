from datetime import datetime
from typing import Any, Dict, Tuple

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

    q = query.BiosampleQuerySchema(conditions=[condition])
    results = {s.id for s in q.execute(db)}
    assert q.count(db) == len(results)
    assert results == expected


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

    q = query.BiosampleQuerySchema(conditions=[condition])
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

    q = query.BiosampleQuerySchema(conditions=[condition])
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

    q: Any
    if table == "project":
        q = query.ProjectQuerySchema
    else:
        q = query.BiosampleQuerySchema

    q = q(conditions=[condition])
    assert {r.id for r in q.execute(db)} == expected


@pytest.mark.parametrize(
    "table",
    [
        "study",
        "project",
        "data_object",
        "biosample",
        "reads_qc",
        "metagenome_assembly",
        "metagenome_annotation",
        "metaproteomic_analysis",
    ],
)
def test_basic_query(db: Session, table):
    tests: Dict[str, Tuple[fakes.AnnotatedFactory, query.BaseQuerySchema]] = {
        "study": (fakes.StudyFactory(), query.StudyQuerySchema()),
        "project": (fakes.ProjectFactory(), query.ProjectQuerySchema()),
        "data_object": (fakes.DataObjectFactory(), query.DataObjectQuerySchema()),
        "biosample": (fakes.BiosampleFactory(), query.BiosampleQuerySchema()),
        "reads_qc": (fakes.ReadsQCFactory(), query.ReadsQCQuerySchema()),
        "metagenome_assembly": (
            fakes.MetagenomeAssemblyFactory(),
            query.MetagenomeAssemblyQuerySchema(),
        ),
        "metagenome_annotation": (
            fakes.MetagenomeAnnotationFactory(),
            query.MetagenomeAnnotationQuerySchema(),
        ),
        "metaproteomic_analysis": (
            fakes.MetaproteomicAnalysisFactory(),
            query.MetaproteomicAnalysisQuerySchema(),
        ),
    }
    db.commit()
    q = tests[table][1].execute(db)
    assert tests[table][0].id in {r.id for r in q.all()}


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

    q = query.BiosampleQuerySchema(conditions=[{"field": "latitude", "op": op, "value": value}])
    assert {r.id for r in q.execute(db)} == expected


def test_grouped_query(db: Session):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    fakes.BiosampleFactory(id="sample3", annotations={"key1": "value4", "key2": "value2"})
    db.commit()

    q = query.BiosampleQuerySchema(
        conditions=[
            {"field": "key2", "value": "value2", "op": "=="},
            {"field": "key1", "value": "value1", "op": "=="},
            {"field": "key2", "value": "value3", "op": "=="},
        ],
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}


def test_indirect_join(db: Session):
    study = fakes.StudyFactory(id="study1")
    fakes.BiosampleFactory(id="sample1", project__study=study)
    db.commit()

    q = query.StudyQuerySchema(conditions=[{"field": "sample_id", "value": "sample1", "op": "=="}])
    assert {s.id for s in q.execute(db)} == {"study1"}


def test_faceted_query(db: Session):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    fakes.BiosampleFactory(id="sample3", annotations={"key1": "value4", "key2": "value2"})
    db.commit()

    q = query.BiosampleQuerySchema(conditions=[])
    assert q.facet(db, "key1") == {"value1": 2, "value4": 1}
    assert q.facet(db, "key2") == {"value2": 2, "value3": 1}


def test_faceted_filtered_query(db: Session):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    fakes.BiosampleFactory(id="sample3", annotations={"key1": "value4", "key2": "value2"})
    db.commit()

    q = query.BiosampleQuerySchema(conditions=[{"field": "id", "op": "==", "value": "sample2"}])
    assert q.facet(db, "key1") == {"value1": 1}
    assert q.facet(db, "key2") == {"value3": 1}


def test_faceted_query_with_no_results(db: Session):
    q = query.BiosampleQuerySchema(conditions=[])
    assert q.facet(db, "key1") == {}


def test_between_query_column(db: Session):
    fakes.BiosampleFactory(id="sample0", depth=0, add_date=date0)
    fakes.BiosampleFactory(id="sample1", depth=1, add_date=date1)
    fakes.BiosampleFactory(id="sample2", depth=10, add_date=date2)
    fakes.BiosampleFactory(id="sample3", depth=100, add_date=date3)
    db.commit()

    q = query.BiosampleQuerySchema(
        conditions=[{"field": "depth", "op": "between", "value": [0.5, 10]}]
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}

    q = query.BiosampleQuerySchema(
        conditions=[{"field": "add_date", "op": "between", "value": [date0, date2]}]
    )
    assert {s.id for s in q.execute(db)} == {"sample0", "sample1", "sample2"}


def test_between_query_annotations(db: Session):
    fakes.BiosampleFactory(id="sample0", annotations={"number": 0, "string": "a"})
    fakes.BiosampleFactory(id="sample1", annotations={"number": 1, "string": "c"})
    fakes.BiosampleFactory(id="sample2", annotations={"number": 10, "string": "e"})
    fakes.BiosampleFactory(id="sample3", annotations={"number": 100, "string": "t"})
    db.commit()

    q = query.BiosampleQuerySchema(
        conditions=[{"field": "number", "op": "between", "value": [0.5, 10]}]
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}

    q = query.BiosampleQuerySchema(
        conditions=[{"field": "string", "op": "between", "value": ["b", "e"]}]
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}


def test_distinct_results(db: Session):
    project = fakes.ProjectFactory(id="project1")
    fakes.BiosampleFactory(id="sample1", project=project)
    fakes.BiosampleFactory(id="sample2", project=project)
    fakes.BiosampleFactory(id="sample3", project=project)
    fakes.BiosampleFactory(id="sample4", project=project)
    db.commit()

    q = query.ProjectQuerySchema(conditions=[])
    assert len(q.execute(db).all()) == 1


@pytest.mark.parametrize(
    "condition,expected",
    [
        ({"field": "env_broad_scale", "value": "broad1"}, "sample2"),
        ({"field": "env_local_scale", "value": "local1"}, "sample1"),
        ({"field": "env_medium", "value": "medium1"}, "sample3"),
    ],
)
def test_query_envo(db: Session, condition, expected):
    env_local = fakes.EnvoTermFactory(label="local1")
    env_broad = fakes.EnvoTermFactory(label="broad1")
    env_medium = fakes.EnvoTermFactory(label="medium1")
    fakes.BiosampleFactory(id="sample1", env_local_scale=env_local)
    fakes.BiosampleFactory(id="sample2", env_broad_scale=env_broad)
    fakes.BiosampleFactory(id="sample3", env_medium=env_medium)
    db.commit()

    q = query.BiosampleQuerySchema(conditions=[condition])
    assert [s.id for s in q.execute(db).all()] == [expected]


def test_facet_envo(db: Session):
    env_local1 = fakes.EnvoTermFactory(label="local1")
    env_local2 = fakes.EnvoTermFactory(label="local2")
    fakes.BiosampleFactory(id="sample1", env_local_scale=env_local1)
    fakes.BiosampleFactory(id="sample2", env_local_scale=env_local2)
    fakes.BiosampleFactory(id="sample3", env_local_scale=env_local2)
    db.commit()

    q = query.BiosampleQuerySchema(conditions=[])
    assert q.facet(db, "env_local_scale") == {
        "local1": 1,
        "local2": 2,
    }


def test_facet_foreign_table(db: Session):
    env_local1 = fakes.EnvoTermFactory(label="local1")
    env_local2 = fakes.EnvoTermFactory(label="local2")
    fakes.BiosampleFactory(id="sample1", env_local_scale=env_local1)
    fakes.BiosampleFactory(id="sample2", env_local_scale=env_local2)
    fakes.BiosampleFactory(id="sample3", env_local_scale=env_local2)
    db.commit()

    q = query.StudyQuerySchema(conditions=[])
    assert q.facet(db, "env_local_scale") == {}
    assert q.facet(db, "sample_id") == {}


def test_envo_ancestor_query(db: Session):
    env_local1 = fakes.EnvoTermFactory(label="local1")
    env_local2 = fakes.EnvoTermFactory(label="local2")
    fakes.EnvoAncestorFactory(term=env_local1, ancestor=env_local2)
    fakes.BiosampleFactory(id="sample1", env_local_scale=env_local1)
    fakes.BiosampleFactory(id="sample2", env_local_scale=env_local2)
    fakes.BiosampleFactory(id="sample3", env_local_scale=env_local2)
    db.commit()

    q = query.BiosampleQuerySchema(conditions=[{"field": "env_local_scale", "value": "local1"}])
    assert {s.id for s in q.execute(db)} == {"sample1"}

    q = query.BiosampleQuerySchema(conditions=[{"field": "env_local_scale", "value": "local2"}])
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2", "sample3"}


def test_envo_ancestor_facet(db: Session):
    env_local1 = fakes.EnvoTermFactory(label="local1")
    env_local2 = fakes.EnvoTermFactory(label="local2")
    env_local3 = fakes.EnvoTermFactory(label="local3")
    fakes.EnvoAncestorFactory(term=env_local1, ancestor=env_local2)
    fakes.BiosampleFactory(id="sample1", env_local_scale=env_local1)
    fakes.BiosampleFactory(id="sample2", env_local_scale=env_local2)
    fakes.BiosampleFactory(id="sample3", env_local_scale=env_local2)
    fakes.BiosampleFactory(id="sample4", env_local_scale=env_local3)
    db.commit()

    q = query.BiosampleQuerySchema(conditions=[])
    assert q.facet(db, "env_local_scale") == {
        "local1": 1,
        "local2": 3,
        "local3": 1,
    }

    q = query.BiosampleQuerySchema(conditions=[{"field": "env_local_scale", "value": "local1"}])
    assert q.facet(db, "env_local_scale") == {
        "local1": 1,
        "local2": 1,
    }

    q = query.BiosampleQuerySchema(conditions=[{"field": "env_local_scale", "value": "local2"}])
    assert q.facet(db, "env_local_scale") == {
        "local1": 1,
        "local2": 3,
    }


@pytest.mark.parametrize("table", ["reads_qc", "assembly", "annotation", "analysis"])
def test_pipeline_query(db: Session, table):
    project1 = fakes.ProjectFactory(name="project1")
    project2 = fakes.ProjectFactory(name="project2")

    fakes.ReadsQCFactory(project=project1, name="reads_qc1")
    fakes.ReadsQCFactory(project=project1, name="reads_qc2")
    fakes.ReadsQCFactory(project=project2, name="reads_qc3")

    fakes.MetagenomeAssemblyFactory(project=project1, name="assembly1")
    fakes.MetagenomeAssemblyFactory(project=project1, name="assembly2")
    fakes.MetagenomeAssemblyFactory(project=project2, name="assembly3")

    fakes.MetagenomeAnnotationFactory(project=project1, name="annotation1")
    fakes.MetagenomeAnnotationFactory(project=project1, name="annotation2")
    fakes.MetagenomeAnnotationFactory(project=project2, name="annotation3")

    fakes.MetaproteomicAnalysisFactory(project=project1, name="analysis1")
    fakes.MetaproteomicAnalysisFactory(project=project1, name="analysis2")
    fakes.MetaproteomicAnalysisFactory(project=project2, name="analysis3")
    db.commit()

    query_schema = {
        "reads_qc": query.ReadsQCQuerySchema,
        "assembly": query.MetagenomeAssemblyQuerySchema,
        "annotation": query.MetagenomeAnnotationQuerySchema,
        "analysis": query.MetaproteomicAnalysisQuerySchema,
    }[table]

    q = query_schema()
    assert {f"{table}{i}" for i in [1, 2, 3]} == {r.name for r in q.execute(db).all()}

    q = query_schema(conditions=[{"table": "project", "field": "name", "value": "project1",}])
    assert {f"{table}{i}" for i in [1, 2]} == {r.name for r in q.execute(db).all()}

    q = query.ProjectQuerySchema(
        conditions=[{"table": q.table.value, "field": "name", "value": f"{table}1"}]
    )
    assert ["project1"] == [r.name for r in q.execute(db).all()]


def test_query_invalid_attribute(db: Session):
    q = query.ReadsQCQuerySchema(
        conditions=[{"table": "reads_qc", "field": "bad value", "value": ""}]
    )
    with pytest.raises(query.InvalidAttributeException):
        q.execute(db)


def test_facet_invalid_attribute(db: Session):
    q = query.ReadsQCQuerySchema()
    with pytest.raises(query.InvalidAttributeException):
        q.facet(db, "bad value")


def test_query_pi(db: Session):
    study1 = fakes.StudyFactory(id="study1", principal_investigator__name="John Doe")
    study2 = fakes.StudyFactory(id="study2", principal_investigator__name="Jane Doe")
    fakes.ProjectFactory(id="project1", study=study1)
    fakes.ProjectFactory(id="project2", study=study2)
    db.commit()

    q = query.StudyQuerySchema()
    assert q.facet(db, "principal_investigator_name") == {
        "John Doe": 1,
        "Jane Doe": 1,
    }

    q = query.StudyQuerySchema(
        conditions=[
            {"table": "study", "field": "principal_investigator_name", "value": "John Doe",}
        ]
    )
    assert ["study1"] == [r.id for r in q.execute(db)]

    qp = query.ProjectQuerySchema(
        conditions=[
            {"table": "study", "field": "principal_investigator_name", "value": "John Doe",}
        ]
    )
    assert ["project1"] == [r.id for r in qp.execute(db)]


def test_query_data_object(db: Session):
    project = fakes.ProjectFactory(id="project")
    fakes.DataObjectFactory(id="file1", project=project, file_size_bytes=16)
    fakes.DataObjectFactory(id="file2", project=project, file_size_bytes=1024)
    fakes.DataObjectFactory(id="file3", file_size_bytes=2048)
    db.commit()

    q = query.DataObjectQuerySchema(
        conditions=[{"table": "project", "field": "id", "value": "project",}]
    )
    assert {"file1", "file2"} == {r.id for r in q.execute(db)}

    q = query.DataObjectQuerySchema(
        conditions=[
            {"table": "project", "field": "id", "value": "project",},
            {"table": "data_object", "field": "file_size_bytes", "op": ">=", "value": 64,},
        ]
    )
    assert {"file2"} == {r.id for r in q.execute(db)}
