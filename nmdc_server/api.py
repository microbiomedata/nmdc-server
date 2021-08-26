from io import BytesIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, StreamingResponse

from nmdc_server import crud, jobs, query, schemas
from nmdc_server.auth import (
    Token,
    admin_required,
    get_current_user,
    login_required,
    login_required_responses,
)
from nmdc_server.bulk_download_schema import BulkDownload, BulkDownloadCreate
from nmdc_server.config import Settings, settings
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.database import create_session
from nmdc_server.ingest.envo import nested_envo_trees
from nmdc_server.models import IngestLock
from nmdc_server.pagination import Pagination

router = APIRouter()


# Dependency
def get_settings():
    yield settings


def get_db(settings: Settings = Depends(get_settings)):
    with create_session() as db:
        yield db


# get the current user information
@router.get("/me", tags=["user"], name="Return the current user name")
async def me(request: Request, user: str = Depends(get_current_user)) -> Optional[str]:
    return user


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
    "/biosample/facet",
    response_model=query.FacetResponse,
    tags=["biosample"],
    name="Get all values of an attribute",
)
async def facet_biosample(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_biosample(db, query.attribute, query.conditions)


@router.post(
    "/biosample/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["biosample"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_biosample(query: query.BinnedFacetQuery, db: Session = Depends(get_db)):
    return crud.binned_facet_biosample(db, **query.dict())


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
    "/study/facet",
    response_model=query.FacetResponse,
    tags=["study"],
    name="Get all values of an attribute",
)
async def facet_study(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_study(db, query.attribute, query.conditions)


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
    token: Token = Depends(login_required),
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
        orcid=token.orcid,
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
async def ping_celery(token: Token = Depends(admin_required)) -> bool:
    try:
        return jobs.ping.delay().wait(timeout=0.5)
    except TimeoutError:
        return False


@router.post(
    "/jobs/ingest",
    tags=["jobs"],
    responses=login_required_responses,
)
async def run_ingest(token: Token = Depends(admin_required), db: Session = Depends(get_db)):
    lock = db.query(IngestLock).first()
    if lock:
        raise HTTPException(
            status_code=409,
            detail=f"An ingest started at {lock.started} is already in progress",
        )
    jobs.ingest.delay()
    return ""


@router.post(
    "/jobs/populate_gene_functions",
    tags=["jobs"],
    responses=login_required_responses,
)
async def repopulate_gene_functions(
    token: Token = Depends(admin_required), db: Session = Depends(get_db)
):
    lock = db.query(IngestLock).first()
    if lock:
        raise HTTPException(
            status_code=409,
            detail=f"An ingest started at {lock.started} is in progress",
        )
    jobs.populate_gene_functions.delay()
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
    token: Token = Depends(login_required),
):
    ip = (x_forwarded_for or "").split(",")[0].strip()
    bulk_download = crud.create_bulk_download(
        db,
        BulkDownloadCreate(
            ip=ip,
            user_agent=user_agent,
            orcid=token.orcid,
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
    token: Token = Depends(login_required),
):
    table = crud.get_zip_download(db, bulk_download_id)
    return Response(
        content=table,
        headers={
            "X-Archive-Files": "zip",
            "Content-Disposition": "attachment; filename=archive.zip",
        },
    )
