from datetime import datetime
from typing import Dict, Tuple

import pytest
from sqlalchemy.orm.session import Session

from nmdc_server import fakes, models, query

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
    condition["table"] = "biosample"
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
    condition["table"] = "biosample"
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
    condition["table"] = "biosample"
    fakes.BiosampleFactory(id="sample1", annotations={"key1": date1, "key2": date2})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": date1, "key2": date3})
    for _ in range(10):
        fakes.BiosampleFactory()
    db.commit()

    q = query.BiosampleQuerySchema(conditions=[condition])
    assert {s.id for s in q.execute(db)} == expected


@pytest.mark.parametrize(
    "table",
    [
        "study",
        "omics_processing",
        "biosample",
    ],
)
def test_basic_query(db: Session, table):
    tests: Dict[str, Tuple[fakes.AnnotatedFactory, query.BaseQuerySchema]] = {
        "study": (fakes.StudyFactory(), query.StudyQuerySchema()),
        "omics_processing": (fakes.OmicsProcessingFactory(), query.OmicsProcessingQuerySchema()),
        "biosample": (fakes.BiosampleFactory(), query.BiosampleQuerySchema()),
    }
    db.commit()
    q = tests[table][1].execute(db)
    assert tests[table][0].id in {r.id for r in q.all()}


def test_study_search_biosample_conditions(db: Session):
    test_study = fakes.StudyFactory()
    _ = fakes.BiosampleFactory(longitude=10, latitude=0, study=test_study)
    _ = fakes.BiosampleFactory(longitude=0, latitude=50, study=test_study)
    sample_3 = fakes.BiosampleFactory(longitude=10, latitude=50)
    db.commit()

    condition_lat_range = {
        "table": "biosample",
        "field": "latitude",
        "op": "between",
        "value": [49, 51],
    }
    condition_long_range = {
        "table": "biosample",
        "field": "longitude",
        "op": "between",
        "value": [9, 11],
    }
    q = query.StudyQuerySchema(conditions=[condition_lat_range, condition_long_range])
    results = {s.id for s in q.execute(db)}
    assert len(results) == 1
    assert sample_3.study_id in results


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

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "latitude", "op": op, "value": value}]
    )
    assert {r.id for r in q.execute(db)} == expected


def test_grouped_query(db: Session):
    fakes.BiosampleFactory(id="sample1", annotations={"key1": "value1", "key2": "value2"})
    fakes.BiosampleFactory(id="sample2", annotations={"key1": "value1", "key2": "value3"})
    fakes.BiosampleFactory(id="sample3", annotations={"key1": "value4", "key2": "value2"})
    db.commit()

    q = query.BiosampleQuerySchema(
        conditions=[
            {"table": "biosample", "field": "key2", "value": "value2", "op": "=="},
            {"table": "biosample", "field": "key1", "value": "value1", "op": "=="},
            {"table": "biosample", "field": "key2", "value": "value3", "op": "=="},
        ],
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}


def test_indirect_join(db: Session):
    study = fakes.StudyFactory(id="study1")
    biosample = fakes.BiosampleFactory(id="b", study=study)
    # fakes.OmicsProcessingFactory(id="omics_processing1", biosample__study=study)
    fakes.OmicsProcessingFactory(id="omics_processing1", biosample_inputs=[biosample])
    db.commit()

    q = query.StudyQuerySchema(
        conditions=[
            {"table": "omics_processing", "field": "id", "value": "omics_processing1", "op": "=="}
        ]
    )
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

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "id", "op": "==", "value": "sample2"}]
    )
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
        conditions=[{"table": "biosample", "field": "depth", "op": "between", "value": [0.5, 10]}]
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}

    q = query.BiosampleQuerySchema(
        conditions=[
            {"table": "biosample", "field": "add_date", "op": "between", "value": [date0, date2]}
        ]
    )
    assert {s.id for s in q.execute(db)} == {"sample0", "sample1", "sample2"}


def test_between_query_annotations(db: Session):
    fakes.BiosampleFactory(id="sample0", annotations={"number": 0, "string": "a"})
    fakes.BiosampleFactory(id="sample1", annotations={"number": 1, "string": "c"})
    fakes.BiosampleFactory(id="sample2", annotations={"number": 10, "string": "e"})
    fakes.BiosampleFactory(id="sample3", annotations={"number": 100, "string": "t"})
    db.commit()

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "number", "op": "between", "value": [0.5, 10]}]
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "string", "op": "between", "value": ["b", "e"]}]
    )
    assert {s.id for s in q.execute(db)} == {"sample1", "sample2"}


def test_distinct_results(db: Session):
    study = fakes.StudyFactory(id="study1")
    fakes.BiosampleFactory(id="sample1", study=study)
    fakes.BiosampleFactory(id="sample2", study=study)
    fakes.BiosampleFactory(id="sample3", study=study)
    fakes.BiosampleFactory(id="sample4", study=study)
    db.commit()

    q = query.StudyQuerySchema(conditions=[])
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
    condition["table"] = "biosample"
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

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "env_local_scale", "value": "local1"}]
    )
    assert {s.id for s in q.execute(db)} == {"sample1"}

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "env_local_scale", "value": "local2"}]
    )
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

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "env_local_scale", "value": "local1"}]
    )
    assert q.facet(db, "env_local_scale") == {
        "local1": 1,
        "local2": 1,
    }

    q = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "env_local_scale", "value": "local2"}]
    )
    assert q.facet(db, "env_local_scale") == {
        "local1": 1,
        "local2": 3,
    }


@pytest.mark.parametrize(
    "table", ["reads_qc", "assembly", "annotation", "analysis", "mags", "reads", "nom", "metab"]
)
def test_pipeline_query(db: Session, table):
    omics_processing1 = fakes.OmicsProcessingFactory(name="omics_processing1")
    omics_processing2 = fakes.OmicsProcessingFactory(name="omics_processing2")

    fakes.ReadsQCFactory(was_informed_by=[omics_processing1], name="reads_qc1")
    fakes.ReadsQCFactory(was_informed_by=[omics_processing1], name="reads_qc2")
    fakes.ReadsQCFactory(was_informed_by=[omics_processing2], name="reads_qc3")

    fakes.MetagenomeAssemblyFactory(was_informed_by=[omics_processing1], name="assembly1")
    fakes.MetagenomeAssemblyFactory(was_informed_by=[omics_processing1], name="assembly2")
    fakes.MetagenomeAssemblyFactory(was_informed_by=[omics_processing2], name="assembly3")

    fakes.MetagenomeAnnotationFactory(was_informed_by=[omics_processing1], name="annotation1")
    fakes.MetagenomeAnnotationFactory(was_informed_by=[omics_processing1], name="annotation2")
    fakes.MetagenomeAnnotationFactory(was_informed_by=[omics_processing2], name="annotation3")

    fakes.MetaproteomicAnalysisFactory(was_informed_by=[omics_processing1], name="analysis1")
    fakes.MetaproteomicAnalysisFactory(was_informed_by=[omics_processing1], name="analysis2")
    fakes.MetaproteomicAnalysisFactory(was_informed_by=[omics_processing2], name="analysis3")

    fakes.MAGsAnalysisFactory(was_informed_by=[omics_processing1], name="mags1")
    fakes.MAGsAnalysisFactory(was_informed_by=[omics_processing1], name="mags2")
    fakes.MAGsAnalysisFactory(was_informed_by=[omics_processing2], name="mags3")

    fakes.ReadBasedAnalysisFactory(was_informed_by=[omics_processing1], name="reads1")
    fakes.ReadBasedAnalysisFactory(was_informed_by=[omics_processing1], name="reads2")
    fakes.ReadBasedAnalysisFactory(was_informed_by=[omics_processing2], name="reads3")

    fakes.NOMAnalysisFactory(was_informed_by=[omics_processing1], name="nom1")
    fakes.NOMAnalysisFactory(was_informed_by=[omics_processing1], name="nom2")
    fakes.NOMAnalysisFactory(was_informed_by=[omics_processing2], name="nom3")

    fakes.MetabolomicsAnalysisFactory(was_informed_by=[omics_processing1], name="metab1")
    fakes.MetabolomicsAnalysisFactory(was_informed_by=[omics_processing1], name="metab2")
    fakes.MetabolomicsAnalysisFactory(was_informed_by=[omics_processing2], name="metab3")
    db.commit()

    # test omics_processing not associated with biosamples
    omics_processing1.biosample_id = None
    db.add(omics_processing1)

    # test omics_processing not associated with studies
    omics_processing2.study_id = None
    db.add(omics_processing2)
    db.commit()

    query_schema = {
        "reads_qc": query.ReadsQCQuerySchema,
        "assembly": query.MetagenomeAssemblyQuerySchema,
        "annotation": query.MetagenomeAnnotationQuerySchema,
        "analysis": query.MetaproteomicAnalysisQuerySchema,
        "mags": query.MAGsAnalysisQuerySchema,
        "reads": query.ReadBasedAnalysisQuerySchema,
        "nom": query.NOMAnalysisQuerySchema,
        "metab": query.MetabolomicsAnalysisQuerySchema,
    }[table]

    q = query_schema()
    assert {f"{table}{i}" for i in [1, 2, 3]} == {r.name for r in q.execute(db).all()}

    q = query_schema(
        conditions=[
            {
                "table": "omics_processing",
                "field": "name",
                "value": "omics_processing1",
            }
        ]
    )
    assert {f"{table}{i}" for i in [1, 2]} == {r.name for r in q.execute(db).all()}

    q = query.OmicsProcessingQuerySchema(
        conditions=[{"table": q.table.value, "field": "name", "value": f"{table}1"}]
    )
    assert ["omics_processing1"] == [r.name for r in q.execute(db).all()]


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
    fakes.BiosampleFactory(id="sample1", study=study1)
    fakes.BiosampleFactory(id="sample2", study=study2)
    db.commit()

    q = query.StudyQuerySchema()
    assert q.facet(db, "principal_investigator_name") == {
        "John Doe": 1,
        "Jane Doe": 1,
    }

    q = query.StudyQuerySchema(
        conditions=[
            {
                "table": "study",
                "field": "principal_investigator_name",
                "value": "John Doe",
            }
        ]
    )
    assert ["study1"] == [r.id for r in q.execute(db)]

    qp = query.BiosampleQuerySchema(
        conditions=[
            {
                "table": "study",
                "field": "principal_investigator_name",
                "value": "John Doe",
            }
        ]
    )
    assert ["sample1"] == [r.id for r in qp.execute(db)]


@pytest.mark.parametrize(
    "value,result",
    [
        (0, True),
        (query.MultiomicsValue.mb.value, True),
        (query.MultiomicsValue.mg.value, False),
        (query.MultiomicsValue.mp.value, False),
        (query.MultiomicsValue.mt.value, True),
        (query.MultiomicsValue.om.value, False),
        (query.MultiomicsValue.mb.value | query.MultiomicsValue.mt.value, True),
        (query.MultiomicsValue.mb.value | query.MultiomicsValue.mg.value, False),
        (
            query.MultiomicsValue.mb.value
            | query.MultiomicsValue.mt.value
            | query.MultiomicsValue.mg.value,
            False,
        ),
    ],
)
def test_query_multiomics(db: Session, value: int, result: bool):
    biosample = fakes.BiosampleFactory()
    fakes.OmicsProcessingFactory(
        annotations={"omics_type": "Metabolomics"}, biosample_inputs=[biosample]
    )
    fakes.OmicsProcessingFactory(
        annotations={"omics_type": "Metatranscriptome"}, biosample_inputs=[biosample]
    )
    db.commit()

    models.Biosample.populate_multiomics(db)
    db.commit()

    qs = query.BiosampleQuerySchema(
        conditions=[{"table": "biosample", "field": "multiomics", "op": "has", "value": value}]
    )
    assert bool(list(qs.execute(db))) is result
