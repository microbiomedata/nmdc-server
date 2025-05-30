from typing import Any, Dict, List, Type, cast

from sqlalchemy import Column, func, or_, select
from sqlalchemy.orm import Session

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

    for column in model.__table__.columns:  # type: ignore
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
                    "parent_study_id"
                )
            )
            .filter(func.jsonb_typeof(models.Study.part_of) == "array")
            .subquery()
        )

        # Count the number of studies whose `id`s are _not_ in that list of parent study
        # `id`s. The result is the number of studies that are not parent studies.
        num_non_parent_studies = (
            q(models.Study).filter(models.Study.id.notin_(parent_ids_subquery)).count()
        )

        return num_non_parent_studies

    return schemas.AggregationSummary(
        studies=q(models.Study).count(),
        non_parent_studies=count_non_parent_studies(),
        locations=distinct(models.Biosample.annotations["location"]),
        habitats=distinct(models.Biosample.annotations["habitat"]),
        data_size=q(func.sum(func.coalesce(models.DataObject.file_size_bytes, 0))).scalar(),
        metagenomes=omics_category("metagenome"),
        metatranscriptomes=omics_category("metatranscriptome"),
        proteomics=omics_category("proteomics"),
        metabolomics=omics_category("metabolomics"),
        lipodomics=omics_category("lipidomics"),
        organic_matter_characterization=omics_category("organic matter characterization"),
    )


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
) -> schemas.DataObjectAggregation:
    subquery = query.OmicsProcessingQuerySchema(conditions=conditions).query(db).subquery()
    rows = (
        db.query(
            models.DataObject.workflow_type,
            models.DataObject.file_type,
            func.count(models.DataObject.id),
            func.sum(func.coalesce(models.DataObject.file_size_bytes, 0)),
        )
        .filter(
            models.DataObject.workflow_type != None,
            models.DataObject.file_type != None,
            subquery.c.id == models.DataObject.omics_processing_id,
            models.DataObject.url != None,
        )
        .group_by(models.DataObject.workflow_type, models.DataObject.file_type)
    )
    agg: schemas.DataObjectAggregation = {
        workflow.value: schemas.DataObjectAggregationElement()
        for workflow in WorkflowActivityTypeEnum
    }

    # TODO: we could join this into one query with a union, but it might not be worthwhile
    # aggregate workflows
    rows = (
        db.query(
            models.DataObject.workflow_type,
            func.count(models.DataObject.id),
            func.sum(func.coalesce(models.DataObject.file_size_bytes, 0)),
        )
        .filter(
            models.DataObject.workflow_type != None,
            subquery.c.id == models.DataObject.omics_processing_id,
            models.DataObject.url != None,
        )
        .group_by(models.DataObject.workflow_type)
    )
    for row in rows:
        agg[row[0]].count = row[1]
        agg[row[0]].size = row[2]

    # aggregate file_types
    rows = (
        db.query(
            models.DataObject.workflow_type,
            models.DataObject.file_type,
            func.count(models.DataObject.id),
            func.sum(func.coalesce(models.DataObject.file_size_bytes, 0)),
        )
        .filter(
            models.DataObject.workflow_type != None,
            models.DataObject.file_type != None,
            subquery.c.id == models.DataObject.omics_processing_id,
            models.DataObject.url != None,
        )
        .group_by(models.DataObject.workflow_type, models.DataObject.file_type)
    )
    for row in rows:
        agg[row[0]].file_types[row[1]] = schemas.DataObjectAggregationNode(
            count=row[2], size=row[3]
        )
    return agg
