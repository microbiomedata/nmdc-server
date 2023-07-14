from collections import Counter
from datetime import date
from io import BytesIO
from typing import Any, Dict, List, Optional
from uuid import UUID

import bson.json_util
from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse
import json
from pymongo import MongoClient, DESCENDING
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, StreamingResponse

from nmdc_server import crud, jobs, models, query, schemas, schemas_submission
from nmdc_server.auth import (
    admin_required,
    get_current_user,
    get_current_user_orcid,
    login_required,
    login_required_responses,
)
from nmdc_server.bulk_download_schema import BulkDownload, BulkDownloadCreate
from nmdc_server.config import Settings
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.database import get_db
from nmdc_server.ingest.envo import nested_envo_trees
from nmdc_server.models import IngestLock, SubmissionMetadata, User
from nmdc_server.pagination import Pagination
from nmdc_server.query import Operation

router = APIRouter()


# get application settings
@router.get("/settings", name="Get application settings")
async def get_settings() -> Dict[str, Any]:
    settings = Settings()
    return {"disable_bulk_download": settings.disable_bulk_download.upper() == "YES"}


# get the current user information
@router.get("/me", tags=["user"], name="Return the current user name")
async def me(request: Request, user: str = Depends(get_current_user)) -> Optional[str]:
    return user


@router.get("/me/orcid", tags=["user"], name="Return the ORCID iD of current user")
async def my_orcid(request: Request, orcid: str = Depends(get_current_user_orcid)) -> Optional[str]:
    return orcid


# autocomplete search
@router.get("/search", tags=["aggregation"], response_model=List[query.ConditionResultSchema])
def text_search(terms: str, limit=6, db: Session = Depends(get_db)):
    return crud.text_search(db, terms, limit)


# database summary
@router.get(
    "/summary",
    response_model=schemas.DatabaseSummary,
    tags=["aggregation"],
    response_model_exclude_unset=True,
)
async def get_database_summary(db: Session = Depends(get_db)):
    return crud.get_database_summary(db)


@router.get(
    "/mongo_summary",
    tags=["aggregation"],
)
async def mongo_get_database_summary(db: Session = Depends(get_db)):
    return {
        "biosample": {
            "attributes": {
                "depth.has_numeric_value": {
                    "min": 0,
                    "max": 2000,
                    "type": "float",
                },
                "geo_loc_name.has_raw_value": {
                    "type": "string",
                },
                "gold_classification": {
                    "type": "sankey-tree",
                },
                "env_broad_scale": {
                    "type": "tree",
                },
                "env_local_scale": {
                    "type": "tree",
                },
                "env_medium": {
                    "type": "tree",
                },
                "latitude": {
                    "type": "float",
                },
                "longitude": {
                    "type": "float",
                },
                "collection_date.has_date_value": {
                    "type": "date",
                    "min": "2000-03-15T00:00:00",
                    "max": "2022-08-12T00:00:00",
                },
            },
        },
        "gene_function": {
            "attributes": {
                "id": {
                    "type": "kegg_search",
                },
            },
        },
        "omics_processing": {
            "attributes": {
                "omics_type.has_raw_value": {
                    "type": "string",
                },
                "instrument_name": {
                    "type": "string",
                },
                "processing_institution": {
                    "type": "string",
                },
            },
        },
        "study": {
            "attributes": {
                "principal_investigator.has_raw_value": {
                    "type": "string",
                },
            },
        },
    }


@router.get(
    "/stats",
    response_model=schemas.AggregationSummary,
    tags=["aggregation"],
)
async def get_aggregated_stats(db: Session = Depends(get_db)):
    return crud.get_aggregated_stats(db)


@router.post(
    "/environment/sankey",
    response_model=List[schemas.EnvironmentSankeyAggregation],
    tags=["aggregation"],
)
async def get_environmental_sankey(
    query: query.BiosampleQuerySchema = query.BiosampleQuerySchema(),
    db: Session = Depends(get_db),
):
    return crud.get_environmental_sankey(db, query)


@router.post(
    "/environment/geospatial",
    response_model=List[schemas.EnvironmentGeospatialAggregation],
    tags=["aggregation"],
)
async def get_environmental_geospatial(
    query: query.BiosampleQuerySchema = query.BiosampleQuerySchema(), db: Session = Depends(get_db)
):
    return crud.get_environmental_geospatial(db, query)


def conditions_to_mongo_filter(conditions):
    mongo_filter = dict()
    for condition in conditions:
        if condition.table.name == "biosample":
            field_name = condition.field
        else:
            field_name = f"{condition.table.name}.{condition.field}"

        if condition.op == Operation.equal:
            if not mongo_filter.get(field_name):
                mongo_filter[field_name] = {"$in": []}
            mongo_filter[field_name]["$in"].append(condition.value)
        elif condition.op == Operation.less:
            mongo_filter[field_name] = { "$lt": condition.value }
        elif condition.op == Operation.less_equal:
            mongo_filter[field_name] = { "$lte": condition.value }
        elif condition.op == Operation.greater:
            mongo_filter[field_name] = { "$gt": condition.value }
        elif condition.op == Operation.greater_equal:
            mongo_filter[field_name] = { "$gte": condition.value }
        elif condition.op == "between":
            mongo_filter[field_name] = { "$gte": condition.value[0], "$lte": condition.value[1] }

    return mongo_filter


# biosample
@router.post(
    "/biosample/search",
    response_model=query.BiosampleSearchResponse,
    tags=["biosample"],
    name="Search for biosamples",
    description="Faceted search of biosample data.",
)
async def search_biosample(
    query: query.BiosampleSearchQuery = query.BiosampleSearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    data_object_filter = query.data_object_filter

    # Inject file object selection information before serialization.
    # This could potentially be more efficient to do in the database query,
    # but the code to generate the query would be much more complicated.
    def insert_selected(biosample: schemas.Biosample) -> schemas.Biosample:
        for op in biosample.omics_processing:
            for da in op.outputs:
                da.selected = schemas.DataObject.is_selected(
                    WorkflowActivityTypeEnum.raw_data, da, data_object_filter
                )
            for od in op.omics_data:
                workflow = WorkflowActivityTypeEnum(od.type)
                for da in od.outputs:
                    da.selected = schemas.DataObject.is_selected(workflow, da, data_object_filter)
        return biosample

    return pagination.response(
        crud.search_biosample(db, query.conditions, data_object_filter), insert_selected
    )


@router.post(
    "/biosample/mongo_search",
    tags=["biosample"],
    name="Search for biosamples",
    description="Faceted search of biosample data.",
)
async def mongo_search_biosample(
    query: query.BiosampleSearchQuery = query.BiosampleSearchQuery(),
    pagination: Pagination = Depends(),
):
    settings = Settings()
    client = MongoClient(
        host=settings.mongo_host,
        username=settings.mongo_user,
        password=settings.mongo_password,
        port=settings.mongo_port,
        directConnection=True,
    )
    mongo_filter = conditions_to_mongo_filter(query.conditions)
    return json.loads(bson.json_util.dumps({
        "count": client.nmdc.denormalized.count_documents(filter=mongo_filter),
        "results": [doc for doc in client.nmdc.denormalized.find(filter=mongo_filter, skip=pagination.offset, limit=pagination.limit, sort=[("omics_processing_count", DESCENDING)])],
    }))


@router.post(
    "/biosample/facet",
    response_model=query.FacetResponse,
    tags=["biosample"],
    name="Get all values of an attribute",
)
async def facet_biosample(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_biosample(db, query.attribute, query.conditions)


@router.post(
    "/biosample/mongo_facet",
    tags=["biosample"],
    name="Get all values of an attribute",
)
async def mongo_facet_biosample(query: query.FacetQuery):
    settings = Settings()
    client = MongoClient(
        host=settings.mongo_host,
        username=settings.mongo_user,
        password=settings.mongo_password,
        port=settings.mongo_port,
        directConnection=True,
    )
    aggregation = [
        {
            "$match": conditions_to_mongo_filter(query.conditions),
        }, {
            "$sortByCount": f"${query.attribute}",
        },
    ]
    return json.loads(bson.json_util.dumps({
        "facets": { facet["_id"]: facet["count"] for facet in client.nmdc.denormalized.aggregate(aggregation) },
    }))


@router.post(
    "/biosample/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["biosample"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_biosample(query: query.BinnedFacetQuery, db: Session = Depends(get_db)):
    return crud.binned_facet_biosample(db, **query.dict())


@router.post(
    "/biosample/mongo_binned_facet",
    tags=["biosample"],
    name="Get all values of an attribute",
)
async def mongo_binned_facet_biosample(query: query.FacetQuery):
    settings = Settings()
    client = MongoClient(
        host=settings.mongo_host,
        username=settings.mongo_user,
        password=settings.mongo_password,
        port=settings.mongo_port,
        directConnection=True,
    )
    aggregation = [
        {
            "$match": conditions_to_mongo_filter(query.conditions),
        }, {
            "$group": {
                "_id": { "year": { "$year": "$collection_date.has_date_value" }, "month": { "$month": "$collection_date.has_date_value" } },
                "count": { "$count": {} }
            },
        },
    ]

    date_string = lambda d: f"{d['_id']['year']}-{str(d['_id']['month']).zfill(2)}-01"
    binned_data = list(client.nmdc.denormalized.aggregate(aggregation))
    binned_data.sort(key=date_string)
    binned_data = [d for d in binned_data if d["_id"]["year"] is not None]

    # Fill in missing months with zero counts
    def next_month(d):
        if d["month"] < 12:
            return {"month": d["month"] + 1, "year": d["year"]}
        return {"month": 1, "year": d["year"] + 1}
    full_binned_data = []
    for d in binned_data:
        if len(full_binned_data) == 0:
            full_binned_data.append(d)
            continue
        while full_binned_data[-1]["_id"]["year"] != d["_id"]["year"] or full_binned_data[-1]["_id"]["month"] != d["_id"]["month"]:
            full_binned_data.append({"_id": next_month(full_binned_data[-1]["_id"]), "count": 0})
        full_binned_data[-1] = d

    return json.loads(bson.json_util.dumps({
        "bins": [date_string(d) for d in full_binned_data],
        "facets": [d["count"] for d in full_binned_data],
    }))


@router.get(
    "/biosample/{biosample_id}",
    response_model=schemas.Biosample,
    tags=["biosample"],
)
async def get_biosample(biosample_id: str, db: Session = Depends(get_db)):
    db_biosample = crud.get_biosample(db, biosample_id)
    if db_biosample is None:
        raise HTTPException(status_code=404, detail="Biosample not found")
    return db_biosample


@router.get(
    "/envo/tree",
    response_model=schemas.EnvoTreeResponse,
    tags=["envo"],
)
async def get_envo_tree():
    return schemas.EnvoTreeResponse(trees=nested_envo_trees())


@router.get(
    "/kegg/module/{module}",
    response_model=schemas.KeggTermListResponse,
    tags=["kegg"],
)
async def get_kegg_terms_for_module(module: str, db: Session = Depends(get_db)):
    terms = crud.list_ko_terms_for_module(db, module)
    return schemas.KeggTermListResponse(terms=terms)


@router.get(
    "/kegg/pathway/{pathway}",
    response_model=schemas.KeggTermListResponse,
    tags=["kegg"],
)
async def get_kegg_terms_for_pathway(pathway: str, db: Session = Depends(get_db)):
    terms = crud.list_ko_terms_for_pathway(db, pathway)
    return schemas.KeggTermListResponse(terms=terms)


@router.get(
    "/kegg/term/search",
    response_model=schemas.KeggTermTextListResponse,
    tags=["kegg"],
)
async def kegg_text_search(query: str, limit=20, db: Session = Depends(get_db)):
    terms = crud.kegg_text_search(db, query, limit)
    return schemas.KeggTermTextListResponse(terms=terms)


# study
@router.post(
    "/study/search",
    response_model=query.StudySearchResponse,
    tags=["study"],
    name="Search for studies",
    description="Faceted search of study data.",
)
async def search_study(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_study(db, query.conditions))


@router.post(
    "/study/mongo_search",
    tags=["study"],
    name="Search for studies",
    description="Faceted search of study data.",
)
async def mongo_search_study(
    query: query.BiosampleSearchQuery = query.BiosampleSearchQuery(),
    pagination: Pagination = Depends(),
):
    settings = Settings()
    client = MongoClient(
        host=settings.mongo_host,
        username=settings.mongo_user,
        password=settings.mongo_password,
        port=settings.mongo_port,
        directConnection=True,
    )

    aggregation = [
        {
            "$match": conditions_to_mongo_filter(query.conditions),
        }, {
            "$unwind": { "path": "$study" },
        }, {
            "$group": {
                "_id": "$study.id",
                "study": { "$first": "$study" },
                "sample_count": { "$count": {} },
                "omics_processing": { "$push": "$omics_processing" },
            },
        }, {
            "$set": {
                "study.sample_count": "$sample_count",
                "study.omics_processing": {
                    "$map": {
                        "input": {
                            # Transform array of arrays of omics_processing into flat array of omics_processing
                            "$reduce": {
                                "input": "$omics_processing",
                                "initialValue": [],
                                "in": { "$concatArrays": ["$$this", "$$value"] },
                            },
                        },
                        # Extract only the omics_type
                        "in": "$$this.omics_type.has_raw_value",
                    },
                },
                # "study.omics_processing_concat": { "$concatArrays": "$omics_processing" },
            },
        }, {
            "$replaceRoot": { "newRoot": "$study" },
        },
    ]

    results = [doc for doc in client.nmdc.denormalized.aggregate([*aggregation, {"$skip": pagination.offset}, {"$limit": pagination.limit}])]

    # Count number of each omics_type
    for result in results:
        omics_processing_counts = Counter(result["omics_processing"])
        count_list = [{"type": key, "count": value} for key, value in omics_processing_counts.items()]
        count_list.sort(key=lambda x: x["type"])
        result["omics_processing_counts"] = count_list if len(count_list) > 0 else None
        del result["omics_processing"]

    return json.loads(bson.json_util.dumps({
        "count": [doc for doc in client.nmdc.denormalized.aggregate([*aggregation, {"$count": "count"}])][0]["count"],
        "results": results,
    }))


@router.post(
    "/study/facet",
    response_model=query.FacetResponse,
    tags=["study"],
    name="Get all values of an attribute",
)
async def facet_study(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_study(db, query.attribute, query.conditions)


@router.post(
    "/study/mongo_facet",
    tags=["study"],
    name="Get all values of an attribute",
)
async def mongo_facet_study(query: query.FacetQuery):
    settings = Settings()
    client = MongoClient(
        host=settings.mongo_host,
        username=settings.mongo_user,
        password=settings.mongo_password,
        port=settings.mongo_port,
        directConnection=True,
    )
    aggregation = [
        {
            "$match": conditions_to_mongo_filter(query.conditions),
        }, {
            "$unwind": { "path": "$study" },
        }, {
            "$group": {
                "_id": "$study.id",
                "study": { "$first": "$study" },
            },
        }, {
            "$replaceRoot": { "newRoot": "$study" },
        }, {
            "$sortByCount": f"${query.attribute}",
        },
    ]

    return json.loads(bson.json_util.dumps({
        "facets": { facet["_id"]: facet["count"] for facet in client.nmdc.denormalized.aggregate(aggregation) },
    }))


@router.post(
    "/study/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["study"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_study(query: query.BinnedFacetQuery, db: Session = Depends(get_db)):
    return crud.binned_facet_study(db, **query.dict())


@router.get(
    "/study/{study_id}",
    response_model=schemas.Study,
    tags=["study"],
)
async def get_study(study_id: str, db: Session = Depends(get_db)):
    db_study = crud.get_study(db, study_id)
    if db_study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return db_study


@router.get("/study/{study_id}/image", tags=["study"])
async def get_study_image(study_id: str, db: Session = Depends(get_db)):
    image = crud.get_study_image(db, study_id)
    if image is None:
        raise HTTPException(status_code=404, detail="No image exists for this study")
    return StreamingResponse(BytesIO(image), media_type="image/jpeg")


# omics_processing
@router.post(
    "/omics_processing/search",
    response_model=query.OmicsProcessingSearchResponse,
    tags=["omics_processing"],
    name="Search for studies",
    description="Faceted search of omics_processing data.",
)
async def search_omics_processing(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_omics_processing(db, query.conditions))


@router.post(
    "/omics_processing/facet",
    response_model=query.FacetResponse,
    tags=["omics_processing"],
    name="Get all values of an attribute",
)
async def facet_omics_processing(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_omics_processing(db, query.attribute, query.conditions)


@router.post(
    "/omics_processing/mongo_facet",
    tags=["omics_processing"],
    name="Get all values of an attribute",
)
async def mongo_facet_omics_processing(query: query.FacetQuery):
    settings = Settings()
    client = MongoClient(
        host=settings.mongo_host,
        username=settings.mongo_user,
        password=settings.mongo_password,
        port=settings.mongo_port,
        directConnection=True,
    )
    aggregation = [
        {
            "$match": conditions_to_mongo_filter(query.conditions),
        }, {
            "$unwind": { "path": "$omics_processing" },
        }, {
            "$group": {
                "_id": "$omics_processing.id",
                "omics_processing": { "$first": "$omics_processing" },
            },
        }, {
            "$replaceRoot": { "newRoot": "$omics_processing" },
        }, {
            "$sortByCount": f"${query.attribute}",
        },
    ]

    return json.loads(bson.json_util.dumps({
        "facets": { facet["_id"]: facet["count"] for facet in client.nmdc.denormalized.aggregate(aggregation) },
    }))


@router.post(
    "/omics_processing/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["omics_processing"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_omics_processing(
    query: query.BinnedFacetQuery, db: Session = Depends(get_db)
):
    return crud.binned_facet_omics_processing(db, **query.dict())


@router.get(
    "/omics_processing/{omics_processing_id}",
    response_model=schemas.OmicsProcessing,
    tags=["omics_processing"],
)
async def get_omics_processing(omics_processing_id: str, db: Session = Depends(get_db)):
    db_omics_processing = crud.get_omics_processing(db, omics_processing_id)
    if db_omics_processing is None:
        raise HTTPException(status_code=404, detail="OmicsProcessing not found")
    return db_omics_processing


@router.get(
    "/omics_processing/{omics_processing_id}/outputs",
    response_model=List[schemas.DataObject],
    tags=["omics_processing"],
)
async def list_omics_processing_data_objects(
    omics_processing_id: str, db: Session = Depends(get_db)
):
    return crud.list_omics_processing_data_objects(db, omics_processing_id).all()


# data object
@router.get(
    "/data_object/{data_object_id}",
    response_model=schemas.DataObject,
    tags=["data_object"],
)
async def get_data_object(data_object_id: str, db: Session = Depends(get_db)):
    db_data_object = crud.get_data_object(db, data_object_id)
    if db_data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    return db_data_object


@router.get(
    "/data_object/{data_object_id}/download",
    tags=["data_object"],
    responses=login_required_responses,
)
async def download_data_object(
    data_object_id: str,
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(login_required),
):
    ip = (x_forwarded_for or "").split(",")[0].strip()
    data_object = crud.get_data_object(db, data_object_id)
    if data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    url = data_object.url
    if url is None:
        raise HTTPException(status_code=404, detail="DataObject has no url reference")

    file_download = schemas.FileDownloadCreate(
        ip=ip,
        user_agent=user_agent,
        orcid=user.orcid,
        data_object_id=data_object_id,
    )
    crud.create_file_download(db, file_download)
    return RedirectResponse(url=url)


@router.post(
    "/data_object/workflow_summary",
    response_model=schemas.DataObjectAggregation,
    tags=["data_object"],
    name="Aggregate data objects by workflow",
)
def data_object_aggregation(
    query: query.DataObjectQuerySchema = query.DataObjectQuerySchema(),
    db: Session = Depends(get_db),
):
    return crud.aggregate_data_object_by_workflow(db, query.conditions)


@router.get("/principal_investigator/{principal_investigator_id}", tags=["principal_investigator"])
async def get_pi_image(principal_investigator_id: UUID, db: Session = Depends(get_db)):
    image = crud.get_pi_image(db, principal_investigator_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Principal investigator  not found")

    return StreamingResponse(BytesIO(image), media_type="image/jpeg")


@router.post(
    "/jobs/ping",
    tags=["jobs"],
    responses=login_required_responses,
)
async def ping_celery(user: models.User = Depends(admin_required)) -> bool:
    try:
        return jobs.ping.delay().wait(timeout=0.5)
    except TimeoutError:
        return False


@router.post(
    "/jobs/ingest",
    tags=["jobs"],
    responses=login_required_responses,
)
async def run_ingest(
    user: models.User = Depends(admin_required),
    params: schemas.IngestArgumentSchema = schemas.IngestArgumentSchema(),
    db: Session = Depends(get_db),
):
    lock = db.query(IngestLock).first()
    if lock:
        raise HTTPException(
            status_code=409,
            detail=f"An ingest started at {lock.started} is already in progress",
        )
    jobs.ingest.delay(function_limit=params.function_limit, skip_annotation=params.skip_annotation)
    return ""


@router.post(
    "/bulk_download",
    tags=["download"],
    response_model=BulkDownload,
    responses=login_required_responses,
    status_code=201,
)
async def create_bulk_download(
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None),
    query: query.BiosampleQuerySchema = query.BiosampleQuerySchema(),
    db: Session = Depends(get_db),
    user: models.User = Depends(login_required),
):
    ip = (x_forwarded_for or "").split(",")[0].strip()
    bulk_download = crud.create_bulk_download(
        db,
        BulkDownloadCreate(
            ip=ip,
            user_agent=user_agent,
            orcid=user.orcid,
            conditions=query.conditions,
            filter=query.data_object_filter,
        ),
    )
    if bulk_download is None:
        return JSONResponse(status_code=400, content={"error": "no files matched the filter"})
    return bulk_download


@router.post(
    "/bulk_download/summary",
    tags=["download"],
    response_model=query.DataObjectAggregation,
)
async def get_data_object_aggregation(
    query: query.DataObjectQuerySchema = query.DataObjectQuerySchema(),
    db: Session = Depends(get_db),
):
    return query.aggregate(db)


@router.get(
    "/bulk_download/{bulk_download_id}",
    tags=["download"],
    responses=login_required_responses,
)
async def download_zip_file(
    bulk_download_id: UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(login_required),
):
    table = crud.get_zip_download(db, bulk_download_id)
    return Response(
        content=table,
        headers={
            "X-Archive-Files": "zip",
            "Content-Disposition": "attachment; filename=archive.zip",
        },
    )


@router.get(
    "/metadata_submission",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=query.MetadataSubmissionResponse,
)
async def list_submissions(
    db: Session = Depends(get_db),
    user: models.User = Depends(login_required),
    pagination: Pagination = Depends(),
):
    query = db.query(SubmissionMetadata)
    try:
        await admin_required(user)
    except HTTPException:
        query = query.join(User).filter(User.orcid == user.orcid)
    return pagination.response(query)


@router.get(
    "/metadata_submission/{id}",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def get_submission(
    id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(login_required),
):
    submission = db.query(SubmissionMetadata).get(id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.author.orcid != user.orcid:
        await admin_required(user)
    return submission


@router.patch(
    "/metadata_submission/{id}",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def update_submission(
    id: str,
    body: schemas_submission.SubmissionMetadataSchemaCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(login_required),
):
    submission = db.query(SubmissionMetadata).get(id)
    body_dict = body.dict()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.author_orcid != user.orcid:
        await admin_required(user)
    submission.metadata_submission = body_dict["metadata_submission"]
    if body_dict["status"]:
        submission.status = body_dict["status"]
    db.commit()
    return submission


@router.post(
    "/metadata_submission",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
    status_code=201,
)
async def submit_metadata(
    body: schemas_submission.SubmissionMetadataSchemaCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(login_required),
):
    submission = SubmissionMetadata(**body.dict(), author_orcid=user.orcid)
    submission.author_id = user.id
    db.add(submission)
    db.commit()
    return submission


@router.get(
    "/users", responses=login_required_responses, response_model=query.UserResponse, tags=["user"]
)
async def get_users(
    db: Session = Depends(get_db),
    user: models.User = Depends(admin_required),
    pagination: Pagination = Depends(),
):
    users = db.query(User)
    return pagination.response(users)


@router.post(
    "/users/{id}", responses=login_required_responses, response_model=schemas.User, tags=["user"]
)
async def update_user(
    id: UUID,
    body: schemas.User,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_required),
):
    if body.id != id:
        raise HTTPException(status_code=400, detail="Invalid id")
    return crud.update_user(db, body)
