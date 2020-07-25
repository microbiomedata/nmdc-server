from typing import cast, Dict, List, Type

from sqlalchemy import Column, func
from sqlalchemy.orm import Session

from nmdc_server import models, query, schemas
from nmdc_server.query_fields import TableAttribute


def get_column_count(db: Session, column: Column) -> int:
    return db.query(func.count()).filter(column != None).scalar()


def get_table_summary(
    db: Session, model: models.Base, attributes: Type[TableAttribute]
) -> schemas.TableSummary:
    count = db.query(model).count()
    summary: Dict[str, schemas.AttributeSummary] = {}
    for attribute in attributes:
        attribute = cast(TableAttribute, attribute)
        info: schemas.AttributeInfo = attribute.info()
        column = info.column
        kwargs = info.dict(exclude={"column"}, exclude_unset=True)
        count_, min, max = (
            db.query(func.count(), func.min(column), func.max(column))
            .filter(column != None)
            .first()
        )
        kwargs["count"] = count_
        if info.type == schemas.AttributeType.string:
            summary[attribute.value] = schemas.StrAttributeSummary(**kwargs)
        elif info.type == schemas.AttributeType.date:
            summary[attribute.value] = schemas.DateAttributeSummary(
                min=min,
                max=max,
                **kwargs
            )
        elif info.type == schemas.AttributeType.integer:
            summary[attribute.value] = schemas.IntAttributeSummary(
                min=min,
                max=max,
                **kwargs
            )
        elif info.type == schemas.AttributeType.integer:
            summary[attribute.value] = schemas.FloatAttributeSummary(
                min=min,
                max=max,
                **kwargs
            )

    return schemas.TableSummary(total=count, attributes=attributes)


def get_aggregation_summary(db: Session):
    q = db.query

    def distinct(a):
        return q(func.distinct(func.lower(a.astext))).count()

    def omics_category(c):
        return (
            q(models.Project)
            .filter(func.lower(models.Project.annotations["omics_type"].astext) == c)
            .count()
        )

    return schemas.AggregationSummary(
        studies=q(models.Study).count(),
        locations=distinct(models.Biosample.annotations["location"]),
        habitats=distinct(models.Biosample.annotations["habitat"]),
        data_size=q(func.sum(models.DataObject.file_size_bytes)).scalar(),
        metagenomes=omics_category("metagenome"),
        metatranscriptomes=omics_category("metatranscriptome"),
        proteomics=omics_category("proteomics"),
        metabolomics=omics_category("metabolomics"),
        lipodomics=omics_category("lipidomics"),
        organic_matter_characterization=omics_category("organic matter characterization"),
    )


def get_sankey_aggregation(
    db: Session, biosample_query: query.BiosampleQuerySchema,
) -> List[schemas.EnvironmentSankeyAggregation]:
    annotations = models.Biosample.annotations
    columns = [
        annotations[e].astext.label(e)
        for e in [
            "ecosystem",
            "ecosystem_category",
            "ecosystem_type",
            "ecosystem_subtype",
            "ecosystem_subtype",
            "specific_ecosystem",
        ]
    ]
    subquery = biosample_query.query(db).subquery()
    rows = (
        db.query(func.count().label("count"), *columns)
        .join(subquery, models.Biosample.id == subquery.c.id)
        .group_by(*columns)
    )
    return [schemas.EnvironmentSankeyAggregation.from_orm(r) for r in rows]


def get_geospatial_aggregation(
    db: Session, biosample_query: query.BiosampleQuerySchema,
) -> List[schemas.EnvironmentGeospatialAggregation]:
    columns = [
        models.Biosample.latitude,
        models.Biosample.longitude,
        models.Biosample.annotations["ecosystem"].label("ecosystem"),
        models.Biosample.annotations["ecosystem_category"].label("ecosystem_category"),
    ]
    subquery = biosample_query.query(db).subquery()
    rows = (
        db.query(func.count().label("count"), *columns)
        .join(subquery, models.Biosample.id == subquery.c.id)
        .group_by(*columns)
    )
    return [schemas.EnvironmentGeospatialAggregation.from_orm(r) for r in rows]
