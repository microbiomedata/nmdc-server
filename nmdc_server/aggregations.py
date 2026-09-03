from typing import Any, Dict, List, Type, cast

from sqlalchemy import Column, func, or_, select, union_all
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Alias, Selectable

from nmdc_server import models, query, schemas
from nmdc_server.attribute_units import get_attribute_units
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum


def get_annotation_summary(
    db: Session,
    model: Type[models.AnnotatedModel],
) -> Dict[str, schemas.AttributeSummary]:
    attribute = func.jsonb_object_keys(model.annotations)

    # TODO: Figure out the correct type, or remove json aggregations
    q = db.query(
        attribute,
        func.count(),
    ).group_by(attribute)

    attributes: Dict[str, schemas.AttributeSummary] = {}
    for r in q:
        attributes[r[0]] = schemas.AttributeSummary(
            count=r[1],
            type=schemas.AttributeType.string,
        )

    return attributes


def get_column_count(db: Session, column: Column) -> int:
    return db.query(func.count()).filter(column != None).scalar()


def get_table_summary(db: Session, model: models.ModelType) -> schemas.TableSummary:
    count = db.query(model).count()
    attributes: Dict[str, schemas.AttributeSummary] = {}
    if isinstance(model(), models.AnnotatedModel):
        attributes.update(get_annotation_summary(db, cast(Type[models.AnnotatedModel], model)))

    for column in model.__table__.columns:
        if (
            column.name not in ["id", "annotations", "alternate_identifiers"]
            and "_id" not in column.name
        ):
            extra: Dict[str, Any] = {}
            units = schemas.UnitInfo.from_unit(
                get_attribute_units(model.__tablename__, column.name)  # type: ignore
            )
            if units:
                extra["units"] = units
            try:
                type_ = schemas.AttributeType.from_column(column)
            except ValueError:
                continue
            if type_ == schemas.AttributeType.string:
                attributes[column.name] = schemas.AttributeSummary(
                    count=get_column_count(db, column),
                    type=schemas.AttributeType.from_column(column),
                    **extra,
                )
            else:
                count_, min, max = (
                    db.query(func.count(), func.min(column), func.max(column))
                    .filter(column != None)
                    .first()  # type: ignore
                )
                attributes[column.name] = schemas.AttributeSummary(
                    count=count_,
                    min=min,
                    max=max,
                    type=schemas.AttributeType.from_column(column),
                    **extra,
                )

    if model == models.Biosample:
        attributes["env_medium"] = schemas.AttributeSummary(
            count=get_column_count(db, models.Biosample.env_medium_id),
            type=schemas.AttributeType.string,
        )
        attributes["env_local_scale"] = schemas.AttributeSummary(
            count=get_column_count(db, models.Biosample.env_local_scale_id),
            type=schemas.AttributeType.string,
        )
        attributes["env_broad_scale"] = schemas.AttributeSummary(
            count=get_column_count(db, models.Biosample.env_broad_scale_id),
            type=schemas.AttributeType.string,
        )
    if model == models.Study:
        attributes["principal_investigator_name"] = schemas.AttributeSummary(
            count=count,
            type=schemas.AttributeType.string,
        )

    return schemas.TableSummary(total=count, attributes=attributes)


def make_superseded_wfe_outputs_subquery(db: Session) -> Any:
    r"""
    Returns a subquery containing all distinct `DataObject` `id` values that are
    outputs of superseded `WorkflowExecution`s (i.e., those with `superseded_by`
    set to a non-NULL value).
    """
    superseded_queries = []
    for wfe_model in models.workflow_activity_types:
        wfe_superseded_query: Query = (
            db.query(models.DataObject.id)
            .select_from(wfe_model)
            .join(getattr(wfe_model, "outputs"))
            .filter(wfe_model.superseded_by != None)  # noqa: E711
        )
        superseded_queries.append(wfe_superseded_query.statement)
    all_superseded_subquery: Selectable = union_all(*superseded_queries).alias()
    return db.query(all_superseded_subquery).distinct().subquery()


def make_all_wfe_outputs_subquery(db: Session) -> Alias:
    r"""
    Returns a subquery that gets all of the distinct `DataObject` `id` values
    that are referenced by any `WorkflowExecution` via the latter's `outputs`
    relationship.
    """

    # For each `WorkflowExecution` model, make a query that `SELECT`s all
    # of the `DataObject.id` values that are referenced by that model via
    # its `outputs` relationship. Then, `UNION ALL` those individual queries
    # into a single subquery. Finally, return a subquery that preserves only
    # the `DISTINCT` `DataObject.id` values.
    #
    # Note: All this time, we're still building up a query. SQLAlchemy won't
    #       actually query the database until we call something like `.all()`,
    #       `.first()`, `scalar()`, etc.
    #
    wfe_outputs_queries = []
    for wfe_model in models.workflow_activity_types:
        wfe_outputs_query: Query = (
            db.query(models.DataObject.id)
            .select_from(wfe_model)
            .join(getattr(wfe_model, "outputs"))
        )
        wfe_outputs_queries.append(wfe_outputs_query.statement)
    all_wfe_outputs_subquery: Selectable = union_all(*wfe_outputs_queries).alias()
    return db.query(all_wfe_outputs_subquery).distinct().subquery()


def get_aggregation_summary(db: Session):
    q = db.query

    def distinct(a):
        return q(func.distinct(func.lower(a.astext))).count()

    def omics_category(c):
        return (
            q(models.OmicsProcessing)
            .filter(func.lower(models.OmicsProcessing.annotations["omics_type"].astext) == c)
            .count()
        )

    def count_non_parent_studies() -> int:
        r"""Returns the number of studies that are not parent studies."""

        # Make a subquery that (a) finds all the studies whose `part_of` value is an array,
        # and (b) selects the distinct `id`s that are in any of those arrays. The result is
        # a list of parent study `id`s.
        parent_ids_subquery = (
            q(
                func.distinct(func.jsonb_array_elements_text(models.Study.part_of)).label(
                    "parent_id"
                )
            )
            .filter(func.jsonb_typeof(models.Study.part_of) == "array")
            .subquery()
        )

        # Count the number of studies whose `id`s are _not_ in that list of parent study
        # `id`s. The result is the number of studies that are not parent studies.
        num_non_parent_studies = (
            q(models.Study)
            .filter(models.Study.id.notin_(select(parent_ids_subquery.c.parent_id)))  # type: ignore
            .count()
        )

        return num_non_parent_studies

    wfe_outputs_subquery = make_all_wfe_outputs_subquery(db)
    wfe_outputs_inner_query = select(wfe_outputs_subquery.c.id)  # type: ignore
    return schemas.AggregationSummary(
        studies=q(models.Study).count(),
        non_parent_studies=count_non_parent_studies(),
        locations=distinct(models.Biosample.annotations["location"]),
        habitats=distinct(models.Biosample.annotations["habitat"]),
        data_size=q(func.sum(func.coalesce(models.DataObject.file_size_bytes, 0))).scalar(),
        wfe_output_data_size_bytes=(
            q(func.sum(func.coalesce(models.DataObject.file_size_bytes, 0)))
            .filter(models.DataObject.id.in_(wfe_outputs_inner_query))
            .scalar()
            or 0
        ),
        metagenomes=omics_category("metagenome"),
        metatranscriptomes=omics_category("metatranscriptome"),
        proteomics=omics_category("proteomics"),
        metabolomics=omics_category("metabolomics"),
        lipodomics=omics_category("lipidomics"),
        organic_matter_characterization=omics_category("organic matter characterization"),
    )


def get_wfe_output_data_objects(db: Session) -> List[models.DataObject]:
    r"""
    Returns a list of all `DataObject`s that are the output of any `WorkflowExecution`.
    """

    wfe_outputs_subquery = make_all_wfe_outputs_subquery(db)
    wfe_outputs_inner_query = select(wfe_outputs_subquery.c.id)  # type: ignore
    q = db.query(models.DataObject).filter(models.DataObject.id.in_(wfe_outputs_inner_query))
    return q.all()


def get_sankey_aggregation(
    db: Session,
    biosample_query: query.BiosampleQuerySchema,
) -> List[schemas.EnvironmentSankeyAggregation]:
    columns = [
        models.Biosample.ecosystem,
        models.Biosample.ecosystem_category,
        models.Biosample.ecosystem_type,
        models.Biosample.ecosystem_subtype,
        models.Biosample.ecosystem_subtype,
        models.Biosample.specific_ecosystem,
    ]
    subquery = biosample_query.query(db).subquery()
    rows = (
        db.query(func.count().label("count"), *columns)
        .filter(or_(*[column.isnot(None) for column in columns]))
        .join(subquery, models.Biosample.id == subquery.c.id)
        .group_by(*columns)
    )
    return [schemas.EnvironmentSankeyAggregation.from_orm(r) for r in rows]


def get_geospatial_aggregation(
    db: Session,
    biosample_query: query.BiosampleQuerySchema,
) -> List[schemas.EnvironmentGeospatialAggregation]:
    columns = [
        models.Biosample.latitude,
        models.Biosample.longitude,
        models.Biosample.ecosystem,
        models.Biosample.ecosystem_category,
    ]
    subquery = biosample_query.query(db).subquery()
    rows = (
        db.query(func.count().label("count"), *columns)
        .join(subquery, models.Biosample.id == subquery.c.id)
        .group_by(*columns)
    )
    return [schemas.EnvironmentGeospatialAggregation.from_orm(r) for r in rows]


def get_data_object_aggregation(
    db: Session,
    conditions: List[query.ConditionSchema],
    include_superseded_workflow_executions: bool = True,
) -> schemas.DataObjectAggregation:
    """
    Aggregate data objects by workflow type and file type,
    optionally excluding outputs of superseded workflow executions.
    """
    subquery = query.OmicsProcessingQuerySchema(conditions=conditions).query(db).subquery()
    if not include_superseded_workflow_executions:
        superseded_subquery = make_superseded_wfe_outputs_subquery(db)
        superseded_dobj_ids_subquery = select(superseded_subquery.c.id)
    agg: schemas.DataObjectAggregation = {
        workflow.value: schemas.DataObjectAggregationElement()
        for workflow in WorkflowActivityTypeEnum
    }

    # A data object can be associated with multiple matching data generations
    # (notably when a workflow is informed by pooled replicates). Deduplicate at
    # the data object level before aggregating so both counts and byte totals are
    # accurate.
    data_objects_query = (
        db.query(
            models.DataObject.id,
            models.DataObject.workflow_type,
            models.DataObject.file_type,
            models.DataObject.file_size_bytes,
        )
        .join(
            models.omics_processing_output_association,
            models.omics_processing_output_association.c.data_object_id == models.DataObject.id,
        )
        .join(
            subquery,
            subquery.c.id == models.omics_processing_output_association.c.omics_processing_id,
        )
        .filter(
            models.DataObject.workflow_type != None,  # noqa: E711
            models.DataObject.url != None,  # noqa: E711
        )
    )
    if not include_superseded_workflow_executions:
        data_objects_query = data_objects_query.filter(
            models.DataObject.id.notin_(superseded_dobj_ids_subquery)
        )
    data_objects = data_objects_query.distinct().subquery()

    # TODO: we could join this into one query with a union, but it might not be worthwhile
    # aggregate workflows
    workflow_rows_query = db.query(
        data_objects.c.workflow_type,
        func.count(data_objects.c.id),
        func.sum(func.coalesce(data_objects.c.file_size_bytes, 0)),
    )
    for row in workflow_rows_query.group_by(data_objects.c.workflow_type):
        agg[row[0]].count = int(row[1] or 0)
        agg[row[0]].size = int(row[2] or 0)

    # aggregate file_types
    file_type_rows_query = db.query(
        data_objects.c.workflow_type,
        data_objects.c.file_type,
        func.count(data_objects.c.id),
        func.sum(func.coalesce(data_objects.c.file_size_bytes, 0)),
    ).filter(
        data_objects.c.file_type != None,  # noqa: E711
    )
    for row in file_type_rows_query.group_by(
        data_objects.c.workflow_type, data_objects.c.file_type
    ):
        agg[row[0]].file_types[row[1]] = schemas.DataObjectAggregationNode(
            count=row[2], size=row[3]
        )
    return agg
