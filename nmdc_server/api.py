import csv
import json
import logging
import time
from enum import StrEnum
from importlib import resources
from io import BytesIO, StringIO
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import httpx
import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from linkml_runtime.utils.schemaview import SchemaView
from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from nmdc_server import crud, models, query, schemas, schemas_submission
from nmdc_server.auth import admin_required, get_current_user, login_required_responses
from nmdc_server.bulk_download_schema import BulkDownload, BulkDownloadCreate
from nmdc_server.config import settings
from nmdc_server.crud import (
    ALLOWED_TRANSITIONS,
    DataObjectReportVariant,
    context_edit_roles,
    get_submission_for_user,
    replace_nersc_data_url_prefix,
)
from nmdc_server.data_object_filters import WorkflowActivityTypeEnum
from nmdc_server.database import get_db
from nmdc_server.ingest.envo import nested_envo_trees
from nmdc_server.logger import get_logger
from nmdc_server.metadata import SampleMetadataSuggester
from nmdc_server.models import (
    SubmissionEditorRole,
    SubmissionImagesObject,
    SubmissionMetadata,
    SubmissionRole,
    User,
)
from nmdc_server.pagination import Pagination
from nmdc_server.storage import BucketName, sanitize_filename, storage
from nmdc_server.table import Table

router = APIRouter()

logger = get_logger(__name__)


# Get system health.
@router.get("/health", name="Get system health", response_model=schemas.HealthResponse)
def get_health(
    response: Response,
    db: Session = Depends(get_db),
) -> schemas.HealthResponse:
    r"""Get system health information."""

    # Declare that our web server is healthy.
    is_web_server_healthy = True

    # Check whether our database connection is healthy.
    is_database_healthy = False
    try:
        db.execute(text("SELECT 1"))
        is_database_healthy = True
    except Exception as e:
        logger.exception(e)

    # Set the HTTP response code accordingly.
    response.status_code = (
        status.HTTP_200_OK
        if all([is_database_healthy, is_web_server_healthy])
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    # Return a health response.
    return schemas.HealthResponse(
        web_server=is_web_server_healthy,
        database=is_database_healthy,
    )


# get application settings
@router.get("/settings", name="Get application settings")
async def get_settings() -> Dict[str, Any]:
    return {
        "disable_bulk_download": settings.disable_bulk_download.upper() == "YES",
        "portal_banner_message": settings.portal_banner_message,
        "portal_banner_title": settings.portal_banner_title,
    }


# get application version number
@router.get("/version", name="Get application and schema version identifiers")
async def get_version() -> schemas.VersionInfo:
    return schemas.VersionInfo()


# get the current user information
@router.get("/me", tags=["user"], name="Return the current user name")
async def me(user: User = Depends(get_current_user)):
    return user


# autocomplete search
@router.get(
    "/search",
    tags=["aggregation"],
    response_model=List[query.ConditionResultSchema],
)
def text_search(terms: str, limit=6, db: Session = Depends(get_db)):
    # Add 'ilike' filters for study and biosample columns users may want to search by
    study_name_filter = {
        "table": "study",
        "value": terms.lower(),
        "field": "name",
        "op": "like",
    }
    study_id_filter = {
        "table": "study",
        "value": terms.lower(),
        "field": "id",
        "op": "like",
    }
    study_description_filter = {
        "table": "study",
        "value": terms.lower(),
        "field": "description",
        "op": "like",
    }
    study_title_filter = {
        "table": "study",
        "value": terms.lower(),
        "field": "title",
        "op": "like",
    }
    biosample_name_filter = {
        "table": "biosample",
        "value": terms.lower(),
        "field": "name",
        "op": "like",
    }
    biosample_description_filter = {
        "table": "biosample",
        "value": terms.lower(),
        "field": "description",
        "op": "like",
    }
    biosample_title_filter = {
        "table": "biosample",
        "value": terms.lower(),
        "field": "title",
        "op": "like",
    }
    biosample_id_filter = {
        "table": "biosample",
        "value": terms.lower(),
        "field": "id",
        "op": "like",
    }
    # These two lists are of objects of separate types
    filters = crud.text_search(db, terms, limit)
    plaintext_filters = [
        query.SimpleConditionSchema(**study_name_filter),
        query.SimpleConditionSchema(**study_id_filter),
        query.SimpleConditionSchema(**study_description_filter),
        query.SimpleConditionSchema(**study_title_filter),
        query.SimpleConditionSchema(**biosample_name_filter),
        query.SimpleConditionSchema(**biosample_description_filter),
        query.SimpleConditionSchema(**biosample_title_filter),
        query.SimpleConditionSchema(**biosample_id_filter),
    ]
    return [*filters, *plaintext_filters]


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


@router.get(
    "/admin/stats",
    response_model=schemas.AdminStats,
    tags=["administration"],
)
async def get_admin_stats(
    db: Session = Depends(get_db),
    user: models.User = Depends(admin_required),
):
    r"""
    Get statistics designed to be consumed by Data Portal/Submission Portal administrators.
    """

    return crud.get_admin_stats(db)


@router.get("/admin/data_object_report", name="Get a data object report")
async def get_data_object_report(
    db: Session = Depends(get_db),
    user: models.User = Depends(admin_required),
    variant: DataObjectReportVariant = Query(
        DataObjectReportVariant.normal,
        description="Whether you want the report to include only URLs.",
    ),
):
    r"""
    Returns a TSV-formatted report about all `DataObject`s that are the output
    of any `WorkflowExecution`.
    """

    header_row, data_rows = crud.get_data_object_report(db, variant=variant)

    # Build the report as an in-memory TSV "file" (buffer).
    # Reference: https://docs.python.org/3/library/csv.html#csv.writer
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    writer.writerow(header_row)
    writer.writerows(data_rows)

    # Reset the buffer's internal file pointer to the beginning of the buffer, so that,
    # when we stream the buffer's contents later, all of its contents are included.
    buffer.seek(0)

    # Stream the buffer's contents to the HTTP client as a downloadable TSV file.
    filename = "data-object-report.tsv"
    response = StreamingResponse(
        buffer,
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    return response


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


def inject_download_counts(db: Session, results, data_object_ids: set[str]):
    """
    Hydrate paginated biosample results with data object download counts.

    This consolidates counting downloads into a single database query, rather than
    two queries for each data object included in the results (one for file_downloads, and
    another for bulk_downloads).
    """
    counts = crud.get_data_object_counts(db, list(data_object_ids))
    for b in results["results"]:
        for op in b.omics_processing:
            for da in op.outputs:
                da._download_count = counts[da.id]
            for od in op.omics_data:
                for da in od.outputs:
                    da._download_count = counts[da.id]
    return results


# biosample
@router.post(
    "/biosample/search",
    response_model=query.Paginated[schemas.Biosample],
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

    data_object_ids = set()

    # Inject file object selection information before serialization.
    # This could potentially be more efficient to do in the database query,
    # but the code to generate the query would be much more complicated.
    # As a side effect, track all relevant data object IDs for this query.
    # They will be used to get download counts for all data objects in one
    # query.
    def insert_selected(biosample: schemas.Biosample) -> schemas.Biosample:
        for op in biosample.omics_processing:
            for da in op.outputs:
                data_object_ids.add(da.id)
                da.selected = schemas.DataObject.is_selected(
                    WorkflowActivityTypeEnum.raw_data, da, data_object_filter
                )
            for od in op.omics_data:
                workflow = WorkflowActivityTypeEnum(od.type)
                for da in od.outputs:
                    da.selected = schemas.DataObject.is_selected(workflow, da, data_object_filter)
                    data_object_ids.add(da.id)
        return biosample

    results = pagination.response(
        crud.search_biosample(
            db, query.conditions, data_object_filter, prefetch_omics_processing_data=True
        ),
        insert_selected,
    )
    # Filter out irrelevant workflow types based on the initial search conditions.
    # This might be possible with SQLAlchemy options, but we need to figure out how
    # to apply filters to the select related options.
    filter_data_object_tables = [
        Table.omics_processing,
        Table.gene_function,
        Table.metaproteomic_analysis,
    ]
    if any([condition.table in filter_data_object_tables for condition in query.conditions]):
        biosample_ids = [b.id for b in results["results"]]  # type: ignore
        omics_results = crud.search_omics_processing_for_biosamples(
            db, query.conditions, biosample_ids
        )
        omics_ids = set([str(o.id) for o in omics_results.all()])
        for biosample in results["results"]:
            biosample.omics_processing = [  # type: ignore
                op for op in biosample.omics_processing if op.id in omics_ids  # type: ignore
            ]
    return inject_download_counts(db, results, data_object_ids)


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


@router.get(
    "/cog/term/search",
    response_model=schemas.KeggTermTextListResponse,
    tags=["gene_function"],
)
async def cog_text_search(query: str, limit=20, db: Session = Depends(get_db)):
    terms = crud.cog_text_search(db, query, limit)
    return schemas.KeggTermTextListResponse(terms=terms)


@router.get(
    "/pfam/term/search",
    response_model=schemas.KeggTermTextListResponse,
    tags=["gene_function"],
)
async def pfam_text_search(query: str, limit=20, db: Session = Depends(get_db)):
    terms = crud.pfam_text_search(db, query, limit)
    return schemas.KeggTermTextListResponse(terms=terms)


@router.get(
    "/go/term/search",
    response_model=schemas.KeggTermTextListResponse,
    tags=["gene_function"],
)
async def go_text_search(query: str, limit=20, db: Session = Depends(get_db)):
    terms = crud.go_text_search(db, query, limit)
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
    q: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    top_level_condition: List[query.ConditionSchema] = [
        query.SimpleConditionSchema(
            **{
                "field": "part_of",
                "op": "==",
                "value": "null",
                "table": "study",
            }
        )
    ]
    children_condition: List[query.ConditionSchema] = [
        query.SimpleConditionSchema(
            **{
                "field": "part_of",
                "op": "!=",
                "value": "null",
                "table": "study",
            }
        )
    ]

    top_level_condition.extend(q.conditions)
    children_condition.extend(q.conditions)

    children_studies = crud.search_study(db, children_condition).all()
    top_level_studies = crud.search_study(db, top_level_condition).all()

    for parent in top_level_studies:
        parent.children = []
        for child in children_studies:
            if child.part_of is not None and parent.id in child.part_of:
                parent.children.append(child)

    # If there are children studies that match the query, but their top level studies do not,
    # and they are not already listed as children of another top level study,
    # add the child to the top level studies
    for child in children_studies:
        for parent_id in child.part_of:
            if (
                parent_id not in [parent.id for parent in top_level_studies]
                and child.id not in [parent.id for parent in top_level_studies]
                and child.id
                not in [child.id for parent in top_level_studies for child in parent.children]
            ):
                top_level_studies.append(child)

    count = len(top_level_studies)

    total = crud.search_study(db, q.conditions).count()

    structured_results: query.StudySearchResponse = query.StudySearchResponse(
        count=count,
        results=top_level_studies[pagination.offset : pagination.limit + pagination.offset],
        total=total,
    )
    return structured_results


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

    children_condition: List[query.ConditionSchema] = [
        query.SimpleConditionSchema(
            **{"field": "part_of", "op": "!=", "value": "null", "table": "study"}
        )
    ]

    children_studies = crud.search_study(db, children_condition).all()
    if db_study:
        db_study.children = []
        for child in children_studies:
            if child.part_of is not None and db_study.id in child.part_of:
                db_study.children.append(child)

    if db_study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return db_study


@router.get("/study/{study_id}/image", tags=["study"])
async def get_study_image(study_id: str, db: Session = Depends(get_db)):
    image = crud.get_study_image(db, study_id)
    if image is None:
        raise HTTPException(status_code=404, detail="No image exists for this study")
    return StreamingResponse(BytesIO(image), media_type="image/jpeg")


# data_generation
# Note the intermingling of the terms "data generation" and "omics processing."
# The Berkeley schema (NMDC schema v11) did away with the phrase "omics processing."
# As a result, public-facing uses of "omics processing" should be replaced with
# "data generation."
# Future work should go in to a more thorough conversion of omics process to data generation.
@router.post(
    "/data_generation/search",
    response_model=query.Paginated[schemas.OmicsProcessing],
    tags=["data_generation"],
    name="Search for data generations",
    description="Faceted search of data_generation data.",
)
async def search_omics_processing(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_omics_processing(db, query.conditions))


@router.post(
    "/data_generation/facet",
    response_model=query.FacetResponse,
    tags=["data_generation"],
    name="Get all values of an attribute",
)
async def facet_omics_processing(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_omics_processing(db, query.attribute, query.conditions)


@router.post(
    "/data_generation/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["data_generation"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_omics_processing(
    query: query.BinnedFacetQuery, db: Session = Depends(get_db)
):
    return crud.binned_facet_omics_processing(db, **query.dict())


@router.get(
    "/data_generation/{data_generation_id}",
    response_model=schemas.OmicsProcessing,
    tags=["data_generation"],
)
async def get_omics_processing(data_generation_id: str, db: Session = Depends(get_db)):
    db_omics_processing = crud.get_omics_processing(db, data_generation_id)
    if db_omics_processing is None:
        raise HTTPException(status_code=404, detail="OmicsProcessing not found")
    return db_omics_processing


@router.get(
    "/data_generation/{data_generation_id}/outputs",
    response_model=List[schemas.DataObject],
    tags=["data_generation"],
)
async def list_omics_processing_data_objects(
    data_generation_id: str, db: Session = Depends(get_db)
):
    return crud.list_omics_processing_data_objects(db, data_generation_id).all()


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
    user: models.User = Depends(get_current_user),
):
    ip = (x_forwarded_for or "").split(",")[0].strip()
    data_object = crud.get_data_object(db, data_object_id)
    if data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    url = data_object.url
    if url is None:
        raise HTTPException(status_code=404, detail="DataObject has no url reference")

    # Overwrite the prefix of the URL if it refers to a data file hosted at NERSC.
    url = replace_nersc_data_url_prefix(
        url=url, replacement_url_prefix=settings.nersc_data_url_external_replacement_prefix
    )

    file_download = schemas.FileDownloadCreate(
        ip=ip,
        user_agent=user_agent,
        orcid=user.orcid,
        data_object_id=data_object_id,
    )
    crud.create_file_download(db, file_download)
    return {
        "url": url,
    }


@router.get("/data_object/{data_object_id}/get_html_content_url")
async def get_data_object_html_content(data_object_id: str, db: Session = Depends(get_db)):
    data_object = crud.get_data_object(db, data_object_id)
    if data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    url = data_object.url
    if url is None:
        raise HTTPException(status_code=404, detail="DataObject has no url reference")

    # Overwrite the prefix of the URL if it refers to a data file hosted at NERSC.
    url = replace_nersc_data_url_prefix(
        url=url, replacement_url_prefix=settings.nersc_data_url_external_replacement_prefix
    )

    if data_object.file_type in [
        "Kraken2 Krona Plot",
        "GOTTCHA2 Krona Plot",
        "Centrifuge Krona Plot",
        "SingleM Krona Plot",
    ]:
        return {
            "url": url,
        }
    raise HTTPException(status_code=400, detail="DataObject has no relevant HTML content")


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
    user: models.User = Depends(get_current_user),
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


async def stream_zip_archive(zip_file_descriptor: Dict[str, Any]):
    r"""
    Sends the specified `zip_file_descriptor` to ZipStreamer and receives
    a ZIP archive in response, which this function yields in chunks.
    """
    last_chunk_time = time.time()

    # TODO: Consider lowering the "severity" of these `logger.warning` statements to `logger.debug`.
    # Note: We added these statements to help with debugging when this functionality was new.
    logger.warning(f"Processing ZIP file descriptor: {zip_file_descriptor=}")
    logger.warning("Using ZipStreamer service to stream ZIP archive...")
    async with (
        httpx.AsyncClient(timeout=None) as client,
        client.stream("POST", settings.zip_streamer_url, json=zip_file_descriptor) as response,
    ):
        async for chunk in response.aiter_bytes(chunk_size=settings.zip_streamer_chunk_size_bytes):
            this_chunk_time = time.time()
            time_elapsed = this_chunk_time - last_chunk_time
            # TODO: either clean up this logging depending on how useful it is, or make the
            # hardcoded value a setting to be read from the environment.
            # The number 5 was chosen because it is the default timeout length for HTTPX.
            if time_elapsed > 5:
                message = f"This chunk took a while to arrive. It arrived in {int(time_elapsed)}s"
                logger.warning(message)
            last_chunk_time = this_chunk_time
            yield chunk


@router.get(
    "/bulk_download/{bulk_download_id}",
    tags=["download"],
)
async def download_zip_file(
    bulk_download_id: UUID,
    db: Session = Depends(get_db),
):
    zip_file_descriptor = crud.get_zip_download(db, bulk_download_id)
    if not zip_file_descriptor:
        return

    return StreamingResponse(
        stream_zip_archive(zip_file_descriptor),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_file_descriptor['suggestedFilename']}"  # noqa: E501
        },
    )


@router.get(
    "/metadata_submission/mixs_report",
    tags=["metadata_submission"],
)
async def get_metadata_submissions_mixs(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    r"""
    Generate a TSV-formatted report of biosamples belonging to submissions
    that have a status of "Submitted - Pending Review".

    The report indicates which environmental package/extension, broad scale,
    local scale, and medium are specified for each biosample. The report is
    designed to facilitate the review of submissions by NMDC team members.
    """
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Your account has insufficient privileges.")

    # Get the submissions from the database.
    q = crud.get_query_for_submitted_pending_review_submissions(db)
    submissions = q.all()

    # Iterate through the submissions, building the data rows for the report.
    header_row = [
        "Submission ID",
        "Status",
        "Sample Name",
        "Environmental Package/Extension",
        "Environmental Broad Scale",
        "Environmental Local Scale",
        "Environmental Medium",
        "Package T/F",
        "Broad Scale T/F",
        "Local Scale T/F",
        "Medium T/F",
    ]

    # Get submission schema view for enum validation
    schema = fetch_nmdc_submission_schema()

    data_rows = []
    for s in submissions:

        metadata = s.metadata_submission  # creates a concise alias
        sample_data = metadata["sampleData"] if "sampleData" in metadata else {}
        env_pkg = metadata.get("packageName", "")

        # Get sample names from each sample type
        for sample_type in sample_data:
            samples = sample_data[sample_type] if sample_type in sample_data else []
            # Iterate through each sample and extract the name
            for x in samples:
                # Get the sample name
                sample_name = x["samp_name"] if "samp_name" in x else ""
                sample_name = str(sample_name)
                sample_name = sample_name.replace("\t", "")
                sample_name = sample_name.replace("\r", "")
                sample_name = sample_name.replace("\n", "").lstrip("_")

                # Get the env broad scale
                env_broad_scale = x["env_broad_scale"] if "env_broad_scale" in x else ""
                env_broad_scale = str(env_broad_scale)
                env_broad_scale = env_broad_scale.replace("\t", "")
                env_broad_scale = env_broad_scale.replace("\r", "")
                env_broad_scale = env_broad_scale.replace("\n", "").lstrip("_")

                # Get the env local scale
                env_local_scale = x["env_local_scale"] if "env_local_scale" in x else ""
                env_local_scale = str(env_local_scale)
                env_local_scale = env_local_scale.replace("\t", "")
                env_local_scale = env_local_scale.replace("\r", "")
                env_local_scale = env_local_scale.replace("\n", "").lstrip("_")

                # Get the env medium
                env_medium = x["env_medium"] if "env_medium" in x else ""
                env_medium = str(env_medium)
                env_medium = env_medium.replace("\t", "")
                env_medium = env_medium.replace("\r", "")
                env_medium = env_medium.replace("\n", "").lstrip("_")

                # Check against permissible values
                env_pkg_enum, env_broad_enum, env_local_enum, env_med_enum = check_permissible_val(
                    schema, env_pkg, env_broad_scale, env_local_scale, env_medium
                )

                # Append each sample as new row (with env data)
                data_row = [
                    s.id,
                    s.status,
                    sample_name,
                    env_pkg,
                    env_broad_scale,
                    env_local_scale,
                    env_medium,
                    env_pkg_enum,
                    env_broad_enum,
                    env_local_enum,
                    env_med_enum,
                ]
                data_rows.append(data_row)

    # Build the report as an in-memory TSV "file" (buffer).
    # Reference: https://docs.python.org/3/library/csv.html#csv.writer
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    writer.writerow(header_row)
    writer.writerows(data_rows)

    # Reset the buffer's internal file pointer to the beginning of the buffer, so that,
    # when we stream the buffer's contents later, all of its contents are included.
    buffer.seek(0)

    # Stream the buffer's contents to the HTTP client as a downloadable TSV file.
    # Reference: https://fastapi.tiangolo.com/advanced/custom-response
    # Reference: https://mimetype.io/text/tab-separated-values
    filename = "mixs-report.tsv"
    response = StreamingResponse(
        buffer,
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    return response


def fetch_nmdc_submission_schema():
    r"""
    Helper function to get a copy of the current NMDC
    Submission Schema.

    This function specifically returns the enums from
    the NMDC Submission Schema.
    """

    submission_schema_files = resources.files("nmdc_submission_schema")

    # Load each class in the submission schema, ensure that each slot of the class
    # is fully materialized into attributes, and then drop the slot usage definitions
    # to save some bytes.
    schema_path = submission_schema_files / "schema/nmdc_submission_schema.yaml"
    sv = SchemaView(str(schema_path))
    enum_view = sv.all_enums()

    # Get only the enums to have a smaller schema to pass and compare against
    isolated_enums = {
        enum_name: {
            # Also only grab the relevant pieces - name and perm. values
            "name": enum_data["name"],
            "permissible_values": list(enum_data["permissible_values"].keys()),
        }
        for enum_name, enum_data in enum_view.items()
        # Only grab the enums that are relevant to the MIxS data check
        if ("EnvPackage" in enum_name)
        or ("EnvMedium" in enum_name)
        or ("EnvBroadScale" in enum_name)
        or ("EnvLocalScale" in enum_name)
    }

    return isolated_enums


def check_permissible_val(
    schema: dict, env_pkg: str, env_broad_scale: str, env_local_scale: str, env_medium: str
):
    r"""
    Helper function to check the value passed in against the
    permissible values provided for pertaining enums in the
    NMDC Submission Schema copy (returned from fetch_nmdc_submission_schema).
    """

    # Perform enum checks
    env_pkg_enum = "False"
    env_broad_scale_enum = "False"
    env_local_scale_enum = "False"
    env_medium_enum = "False"

    if env_pkg in schema["EnvPackageEnum"]["permissible_values"]:
        env_pkg_enum = "True"

    # Enums exist currently for water, soil, sediment, and plant-associated
    # confirmed_enums will need to be updated as more enum types are added
    confirmed_enums = ["water", "soil", "sediment", "plant-associated"]

    if env_pkg in confirmed_enums:

        # Transform env_package to use it to find enums without updating to include each biome type
        # Replace dashes with spaces, capitalize each word, then remove the space
        temp_env_pkg = env_pkg
        temp_env_pkg = temp_env_pkg.replace("-", " ")
        temp_env_pkg = temp_env_pkg.title()
        temp_env_pkg = temp_env_pkg.replace(" ", "")

        # Validate the rest of the enums
        if env_broad_scale in schema[f"EnvBroadScale{temp_env_pkg}Enum"]["permissible_values"]:
            env_broad_scale_enum = "True"
        if env_local_scale in schema[f"EnvLocalScale{temp_env_pkg}Enum"]["permissible_values"]:
            env_local_scale_enum = "True"
        if env_medium in schema[f"EnvMedium{temp_env_pkg}Enum"]["permissible_values"]:
            env_medium_enum = "True"

    return env_pkg_enum, env_broad_scale_enum, env_local_scale_enum, env_medium_enum


@router.get(
    "/metadata_submission/report",
    tags=["metadata_submission"],
)
async def get_metadata_submissions_report(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    r"""
    Download a TSV file containing a high-level report of Submission Portal submissions,
    including their ID, author info, study info, and PI info.
    """
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Your account has insufficient privileges.")

    # Get the submissions from the database.
    q = crud.get_query_for_all_submissions(db)
    submissions = q.all()

    # Iterate through the submissions, building the data rows for the report.
    header_row = [
        "Submission ID",
        "Author ORCID",
        "Author Name",
        "Study Name",
        "PI Name",
        "PI Email",
        "Source Client",
        "Status",
        "Is Test Submission",
        "Date Last Modified",
        "Date Created",
        "Number of Samples",
    ]
    data_rows = []
    for s in submissions:
        sample_count = 0
        metadata = s.metadata_submission  # creates a concise alias
        # find the number of samples in the submission
        # Note: `metadata["sampleData"]` is a dictionary where keys are sample types
        #       and values are lists of samples of that type.
        # Reference: https://microbiomedata.github.io/submission-schema/SampleData/
        sample_data = metadata["sampleData"]
        for sample_type in sample_data:
            sample_count += len(sample_data[sample_type])

        author_user = s.author  # note: `s.author` is a `models.User` instance
        study_form = metadata["studyForm"] if "studyForm" in metadata else {}
        study_name = study_form["studyName"] if "studyName" in study_form else ""
        pi_name = study_form["piName"] if "piName" in study_form else ""
        pi_email = study_form["piEmail"] if "piEmail" in study_form else ""
        data_row = [
            s.id,
            s.author_orcid,
            author_user.name,
            study_name,
            pi_name,
            pi_email,
            s.source_client,
            s.status,
            s.is_test_submission,
            s.date_last_modified,
            s.created,
            sample_count,
        ]
        data_rows.append(data_row)

    # Build the report as an in-memory TSV "file" (buffer).
    # Reference: https://docs.python.org/3/library/csv.html#csv.writer
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    writer.writerow(header_row)
    writer.writerows(data_rows)

    # Reset the buffer's internal file pointer to the beginning of the buffer, so that,
    # when we stream the buffer's contents later, all of its contents are included.
    buffer.seek(0)

    # Stream the buffer's contents to the HTTP client as a downloadable TSV file.
    # Reference: https://fastapi.tiangolo.com/advanced/custom-response
    # Reference: https://mimetype.io/text/tab-separated-values
    filename = "submissions-report.tsv"
    response = StreamingResponse(
        buffer,
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    return response


async def get_paginated_submission_list(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    pagination: Pagination = Depends(),
    column_sort: str = "created",
    sort_order: str = "desc",
    is_test_submission_filter: Optional[bool] = None,
):
    """
    Dependency function for getting a list of submissions with pagination, sorting, and filtering
    applied.
    """
    query = crud.get_submissions_for_user(
        db, user, column_sort, sort_order, is_test_submission_filter
    )
    return pagination.response(query)


# The following two endpoints perform the same underlying query, but only differ in the
# response model they return.
@router.get(
    "/metadata_submission",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=query.Paginated[schemas_submission.SubmissionMetadataSchema],
)
async def list_submissions(submissions=Depends(get_paginated_submission_list)):
    """Return a paginated list of submissions in full detail."""
    return submissions


@router.get(
    "/metadata_submission/slim",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=query.Paginated[schemas_submission.SubmissionMetadataSchemaSlim],
)
async def list_submissions_slim(submissions=Depends(get_paginated_submission_list)):
    """Return a paginated list of submissions in slim format."""
    return submissions


@router.get(
    "/metadata_submission/{id}",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def get_submission(
    id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    submission: Optional[models.SubmissionMetadata] = db.get(SubmissionMetadata, id)  # type: ignore
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    if user.is_admin or crud.can_read_submission(db, id, user.orcid):
        permission_level = None
        if user.is_admin or user.orcid in submission.owners:
            permission_level = models.SubmissionEditorRole.owner.value
        elif user.orcid in submission.editors:
            permission_level = models.SubmissionEditorRole.editor.value
        elif user.orcid in submission.metadata_contributors:
            permission_level = models.SubmissionEditorRole.metadata_contributor.value
        elif user.orcid in submission.viewers:
            permission_level = models.SubmissionEditorRole.viewer.value
        elif user.orcid in submission.reviewers:
            permission_level = models.SubmissionEditorRole.reviewer.value
        submission_metadata_schema = schemas_submission.SubmissionMetadataSchema.model_validate(
            submission
        )
        submission_metadata_schema.permission_level = permission_level

        return submission_metadata_schema

    raise HTTPException(status_code=403, detail="Must have access.")


def can_save_submission(role: models.SubmissionRole, data: dict, status: str):
    """Compare a patch payload with what the user can actually save."""
    metadata_contributor_fields = set(["sampleData", "metadata_submission"])
    editor_fields = set(
        [
            "packageName",
            "contextForm",
            "addressForm",
            "templates",
            "studyForm",
            "multiOmicsForm",
            "sampleData",
            "metadata_submission",
        ]
    )
    attempted_patch_fields = set(
        [key for key in data] + [key for key in data.get("metadata_submission", {})]
    )
    fields_for_permission = {
        models.SubmissionEditorRole.editor: editor_fields,
        models.SubmissionEditorRole.metadata_contributor: metadata_contributor_fields,
    }
    permission_level = models.SubmissionEditorRole(role.role)
    if status in [SubmissionStatusEnum.InProgress.text, SubmissionStatusEnum.UpdatesRequired.text]:
        if permission_level == models.SubmissionEditorRole.owner:
            return True
        elif (
            permission_level == models.SubmissionEditorRole.viewer
            or permission_level == models.SubmissionEditorRole.reviewer
        ):
            return False
        else:
            allowed_fields = fields_for_permission[permission_level]
            return all([field in allowed_fields for field in attempted_patch_fields])
    else:
        return False


@router.patch(
    "/metadata_submission/{id}",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def update_submission(
    id: str,
    body: schemas_submission.SubmissionMetadataSchemaPatch,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    submission = db.get(SubmissionMetadata, id)  # type: ignore
    body_dict = body.dict(exclude_unset=True)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    current_user_role = crud.get_submission_role(db, id, user.orcid)
    if not (
        user.is_admin
        or (
            current_user_role
            and can_save_submission(current_user_role, body_dict, submission.status)
        )
    ):
        raise HTTPException(403, detail="Must have access.")

    has_lock = crud.try_get_submission_lock(db, submission.id, user.id)
    if not has_lock:
        raise HTTPException(
            status_code=400,
            detail="This submission is currently being edited by a different user.",
        )

    # If the status is "Updates Required", automatically change it to "In Progress" upon edit
    if submission.status == SubmissionStatusEnum.UpdatesRequired.text:
        submission.status = SubmissionStatusEnum.InProgress.text

    if body.field_notes_metadata is not None:
        submission.field_notes_metadata = body.field_notes_metadata

    # Merge the submission metadata dicts
    submission.metadata_submission = (
        submission.metadata_submission | body_dict["metadata_submission"]
    )
    # TODO: remove the child properties "studyName" and "templates" in favor of the top-
    # level property. Requires some coordination between this API and its clients.
    if "studyForm" in body_dict["metadata_submission"]:
        submission.study_name = body_dict["metadata_submission"]["studyForm"]["studyName"]
    if "templates" in body_dict["metadata_submission"]:
        submission.templates = body_dict["metadata_submission"]["templates"]

    # Update permissions if the user is an "owner" or "admin"
    # TODO: consider whether this can be refactored into a separate endpoint
    new_permissions = body_dict.get("permissions", None)
    can_update_permissions = user.is_admin or (
        current_user_role and current_user_role.role == models.SubmissionEditorRole.owner
    )
    if new_permissions is not None and can_update_permissions:
        crud.update_submission_contributor_roles(db, submission, new_permissions)

    crud.update_submission_lock(db, submission.id)

    return submission


@router.get("/status_transitions", name="Get the `Status` transitions allowed by user role")
async def get_transitions():
    return ALLOWED_TRANSITIONS


@router.patch(
    "/metadata_submission/{id}/status",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def update_submission_status(
    id: str,
    body: schemas_submission.SubmissionMetadataStatusPatch,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.SubmissionMetadata:
    """Update submission status and create/update GitHub issue as needed."""
    submission = get_submission_for_user(
        db, id, user, allowed_roles=[SubmissionEditorRole.owner, SubmissionEditorRole.reviewer]
    )
    current_status = submission.status

    # Admins can change to any status
    if user.is_admin:
        submission.status = body.status

    # Non-admin users need to follow allowed transitions based on role
    else:

        # Owner transitions
        if user.orcid in submission.owners:
            transitions = ALLOWED_TRANSITIONS[SubmissionEditorRole.owner]

        # Reviewer transitions
        elif user.orcid in submission.reviewers:
            transitions = ALLOWED_TRANSITIONS[SubmissionEditorRole.reviewer]

        # Apply restricted transitions
        if (
            transitions
            and current_status in transitions
            and body.status in transitions[current_status]
        ):
            submission.status = body.status

        # Any other transitions not allowed
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid status transition.",
            )
    db.commit()

    # If the new status is "Submitted - Pending Review", create or update the GitHub issue
    if (
        body.status == SubmissionStatusEnum.SubmittedPendingReview.text
        and submission.is_test_submission is False
    ):
        if submission.submission_issue is None:
            try:
                submission.submission_issue = create_github_issue(submission, user)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create GitHub issue: {str(e)}",
                )
            db.commit()
        else:
            try:
                update_github_issue_for_resubmission(submission.submission_issue, user)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update GitHub issue: {str(e)}",
                )


@router.post(
    "/metadata_submission/{id}/role",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def add_submission_role(
    id: str,
    body: schemas_submission.SubmissionMetadataRoleAdd,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.SubmissionMetadata:
    """Grant a role to a user on a submission

    This is intended as a simpler alternative to passing a permissions object in the full
    submission PATCH endpoint, which will add, remove, or change roles as needed to match the
    provided permissions object. This endpoint only adds a single role for a single user.
    """
    submission = get_submission_for_user(db, id, user, allowed_roles=[SubmissionEditorRole.owner])
    existing_role = crud.get_submission_role(db, id, body.orcid)
    if existing_role is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a role on this submission.",
        )

    crud.add_submission_role(db, submission, body.orcid, body.role)

    return submission


@router.delete(
    "/metadata_submission/{id}/role/{orcid}",
    tags=["metadata_submission"],
    responses=login_required_responses,
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def remove_submission_role(
    id: str,
    orcid: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.SubmissionMetadata:
    """Remove a role from a submission

    This is intended as a simpler alternative to passing a permissions object in the full
    submission PATCH endpoint, which will add, remove, or change roles as needed to match the
    provided permissions object. This endpoint only removes a single user.
    """
    submission = get_submission_for_user(db, id, user, allowed_roles=[SubmissionEditorRole.owner])

    crud.remove_submission_role(db, submission, orcid)

    return submission


def create_github_issue(submission_model: SubmissionMetadata, user):
    """
    Create a Github issue for the submission.
    Return the issue number.
    """
    submission = schemas_submission.SubmissionMetadataSchema.model_validate(submission_model)
    gh_url = str(settings.github_issue_url)
    token = settings.github_authentication_token
    assignee = settings.github_issue_assignee

    # If the settings for issue creation weren't supplied return, no need to do anything further
    if gh_url is None or token is None:
        return None

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "text/plain; charset=utf-8"}

    # Gathering the fields we want to display in the issue
    study_form = submission.metadata_submission.studyForm
    multiomics_form = submission.metadata_submission.multiOmicsForm
    pi_name = study_form.piName
    pi_orcid = study_form.piOrcid
    data_generated = "Yes" if multiomics_form.dataGenerated else "No"
    omics_processing_types = ", ".join(multiomics_form.omicsProcessingTypes)
    sample_types = ", ".join(submission.metadata_submission.templates)
    num_samples = submission.sample_count

    # some variable data to supply depending on if data has been generated or not
    id_dict = {
        "NCBI ID: ": study_form.NCBIBioProjectId,
        "GOLD ID: ": study_form.GOLDStudyId,
        "JGI ID: ": multiomics_form.JGIStudyId,
        "EMSL ID: ": multiomics_form.studyNumber,
        "Alternative IDs: ": ", ".join(study_form.alternativeNames),
    }
    valid_ids = []
    for key, value in id_dict.items():
        if str(value) != "":
            valid_ids.append(key + value)

    # assemble the body of the API request
    body_lis = [
        f"Issue created from host: {settings.host}",
        f"Submitter: {user.name}, {user.orcid}",
        f"Submission ID: {submission.id}",
        f"Has data been generated: {data_generated}",
        f"PI name: {pi_name}",
        f"PI orcid: {pi_orcid}",
        f"Status: {SubmissionStatusEnum.SubmittedPendingReview.text}",
        f"Data types: {omics_processing_types}",
        f"Sample type: {sample_types}",
        f"Number of samples: {num_samples}",
    ] + valid_ids
    body_string = " \n ".join(body_lis)
    payload_dict = {
        "title": f"NMDC Submission: {submission.id}",
        "body": body_string,
        "assignees": [assignee],
    }

    payload = json.dumps(payload_dict)

    res = requests.post(url=gh_url, data=payload, headers=headers)
    if res.status_code != 201:
        raise HTTPException(
            status_code=res.status_code,
            detail=f"Github issue creation failed: {res.reason}",
        )

    return res.json()['number']


def update_github_issue_for_resubmission(existing_issue, user):
    """
    Update an existing GitHub issue to note that the submission was resubmitted.
    Adds a comment and reopens the issue if it was closed.
    Return nothing.
    """

    # Create a comment noting the resubmission
    from datetime import datetime

    gh_url = str(settings.github_issue_url)
    issue_url = f"{gh_url}/{existing_issue}"
    token = settings.github_authentication_token

    # If the settings for issue creation weren't supplied return, no need to do anything further
    if gh_url is None or token is None:
        return None
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "text/plain; charset=utf-8"}

    # Make comment
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    comment_body = f"""
## 🔄 Submission Resubmitted

**Resubmitted by:** {user.name} ({user.orcid})
**Timestamp:** {timestamp}
**Status:** {SubmissionStatusEnum.SubmittedPendingReview.text}

The submission has been updated and resubmitted for review.
    """.strip()

    # Add comment to the issue
    comment_url = f"{issue_url}/comments"
    comment_payload = {"body": comment_body}
    comment_response = requests.post(comment_url, headers=headers, data=json.dumps(comment_payload))
    if comment_response.status_code != 201:
        raise HTTPException(
            status_code=comment_response.status_code,
            detail=f"Failed to add comment to GitHub issue: {comment_response.reason}",
        )
    
    # If the issue is closed, reopen it
    res = requests.get(url=issue_url, headers=headers)
    if res.status_code != 200:
        raise HTTPException(
            status_code=res.status_code,
            detail=f"Failed to fetch GitHub issue: {res.reason}",
        )
    existing_issue = res.json()
    if existing_issue.get("state") == "closed":
        reopen_payload = {"state": "open", "state_reason": "reopened"}
        reopen_response = requests.patch(
            issue_url, headers=headers, data=json.dumps(reopen_payload)
        )
        if reopen_response.status_code != 200:
            raise HTTPException(
                status_code=reopen_response.status_code,
                detail=f"Failed to reopen GitHub issue: {reopen_response.reason}",
            )


@router.delete(
    "/metadata_submission/{id}",
    tags=["metadata_submission"],
    responses=login_required_responses,
)
async def delete_submission(
    id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    submission = db.get(SubmissionMetadata, id)  # type: ignore
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    if not (user.is_admin or user.orcid in submission.owners):
        raise HTTPException(403, detail="Must have access.")

    has_lock = crud.try_get_submission_lock(db, submission.id, user.id)
    if not has_lock:
        raise HTTPException(
            status_code=400,
            detail="This submission is currently being edited by a different user.",
        )

    for role in submission.roles:
        db.delete(role)
    db.delete(submission)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/metadata_submission/{id}/lock")
async def lock_submission(
    response: Response,
    id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> schemas.LockOperationResult:
    submission: Optional[SubmissionMetadata] = db.get(SubmissionMetadata, id)  # type: ignore
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Attempt to acquire the lock
    lock_acquired = crud.try_get_submission_lock(db, submission.id, user.id)
    if lock_acquired:
        return schemas.LockOperationResult(
            success=True,
            message=f"Lock successfully acquired for submission with ID {id}.",
            locked_by=submission.locked_by,
            lock_updated=submission.lock_updated,
        )
    else:
        response.status_code = status.HTTP_409_CONFLICT
        return schemas.LockOperationResult(
            success=False,
            message="This submission is currently locked by a different user.",
            locked_by=submission.locked_by,
            lock_updated=submission.lock_updated,
        )


@router.put("/metadata_submission/{id}/unlock")
async def unlock_submission(
    response: Response,
    id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> schemas.LockOperationResult:
    submission = db.get(SubmissionMetadata, id)  # type: ignore
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Then verify session user has the lock
    has_lock = crud.try_get_submission_lock(db, submission.id, user.id)
    if not has_lock:
        response.status_code = status.HTTP_409_CONFLICT
        return schemas.LockOperationResult(
            success=False,
            message="This submission is currently locked by a different user.",
            locked_by=submission.locked_by,
            lock_updated=submission.lock_updated,
        )
    else:
        crud.release_submission_lock(db, submission.id)
        return schemas.LockOperationResult(
            success=True,
            message=f"Submission lock released successfully for submission with ID {id}",
        )


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
    user: models.User = Depends(get_current_user),
):
    # Old versions of the Field Notes app will continue to use the pre-v1.6.0 submission format
    # (before certain fields were moved from the multi-omics form to the study form) until its
    # next release. This is a temporary shim layer that can be removed later.
    multi_omics_form_extras = body.metadata_submission.multiOmicsForm.__pydantic_extra__ or {}
    if body.metadata_submission.studyForm.GOLDStudyId is None:
        body.metadata_submission.studyForm.GOLDStudyId = multi_omics_form_extras.get(
            "GOLDStudyId", ""
        )
    if body.metadata_submission.studyForm.NCBIBioProjectId is None:
        body.metadata_submission.studyForm.NCBIBioProjectId = multi_omics_form_extras.get(
            "NCBIBioProjectId", ""
        )
    if body.metadata_submission.studyForm.alternativeNames is None:
        body.metadata_submission.studyForm.alternativeNames = multi_omics_form_extras.get(
            "alternativeNames", []
        )
    if body.metadata_submission.multiOmicsForm.facilities is None:
        body.metadata_submission.multiOmicsForm.facilities = []

    submission = SubmissionMetadata(
        **body.dict(),
        author_orcid=user.orcid,
    )
    submission.author_id = user.id
    submission.study_name = body.metadata_submission.studyForm.studyName
    submission.templates = body.metadata_submission.templates

    db.add(submission)
    db.commit()
    owner_role = SubmissionRole(
        **{
            "submission_id": submission.id,
            "user_orcid": user.orcid,
            "role": SubmissionEditorRole.owner,
        }
    )
    db.add(owner_role)
    db.commit()
    crud.try_get_submission_lock(db, submission.id, user.id)
    return submission


@router.post(
    "/metadata_submission/suggest",
    tags=["metadata_submission"],
    responses=login_required_responses,
)
async def suggest_metadata(
    body: List[schemas_submission.MetadataSuggestionRequest],
    suggester: SampleMetadataSuggester = Depends(SampleMetadataSuggester),
    types: Union[List[schemas_submission.MetadataSuggestionType], None] = Query(None),
    user: models.User = Depends(get_current_user),
) -> List[schemas_submission.MetadataSuggestion]:
    response: List[schemas_submission.MetadataSuggestion] = []
    for item in body:
        suggestions = suggester.get_suggestions(item.data, types=types)
        for slot, value in suggestions.items():
            response.append(
                schemas_submission.MetadataSuggestion(
                    type=(
                        schemas_submission.MetadataSuggestionType.REPLACE
                        if slot in item.data
                        else schemas_submission.MetadataSuggestionType.ADD
                    ),
                    row=item.row,
                    slot=slot,
                    value=value,
                    current_value=item.data.get(slot, None),
                )
            )
    return response


@router.post("/metadata_submission/{id}/image/signed_upload_url", response_model=schemas.SignedUrl)
async def generate_signed_upload_url(
    id: str,
    body: schemas.SignedUploadUrlRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Don't accept files larger than the configured limit (default is 25 MB)
    if body.file_size > settings.max_submission_image_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File size exceeds limit"
        )

    # Ensure the requested submission exists and the user has permission to edit it
    submission = get_submission_for_user(db, id, user, allowed_roles=context_edit_roles)

    # Ensure that the incoming image will not push the submission over its quota
    potential_max_size = submission.study_images_total_size + body.file_size
    if potential_max_size > settings.max_submission_image_total_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Submission quota exceeded",
        )

    sanitized_filename = sanitize_filename(body.file_name)
    return storage.get_signed_upload_url(
        BucketName.SUBMISSION_IMAGES,
        f"{settings.gcs_object_name_prefix}/{id}/{uuid4().hex}-{sanitized_filename}",
        content_type=body.content_type,
    )


@router.post(
    "/metadata_submission/{id}/image/make_public",
    response_model=schemas.SubmissionImagesMakePublicResponse,
)
async def make_submission_images_public(
    id: str,
    body: schemas.SubmissionImagesMakePublicRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SubmissionImagesMakePublicResponse:
    """Copy the submission's images into the public images bucket and return their public URLs.

    This operation is only allowed for admin users. It is intended to be called as part of the
    process of translating submission data into nmdc-schema compatible data. We make a public copy
    instead of changing the permissions of the original image because the submission images
    bucket uses uniform bucket-level access, which means we can't change the permissions of
    individual objects.
    """
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Your account has insufficient privileges.")

    submission = get_submission_for_user(db, id, user)

    def make_public(image: Optional[SubmissionImagesObject]) -> Optional[str]:
        """Make a copy of the given image in the public images bucket and return its public URL."""
        if image is None:
            return None
        public_object = storage.copy_object(
            image.name,
            from_bucket=BucketName.SUBMISSION_IMAGES,
            to_bucket=BucketName.PUBLIC_IMAGES,
            new_name=image.name.replace(id, body.study_id),
        )
        return public_object.public_url

    public_pi_image = make_public(submission.pi_image)
    public_primary_study_image = make_public(submission.primary_study_image)
    public_study_image_urls = [make_public(img) for img in submission.study_images]

    return schemas.SubmissionImagesMakePublicResponse(
        pi_image_url=public_pi_image,
        primary_study_image_url=public_primary_study_image,
        study_image_urls=public_study_image_urls,
    )


class ImageType(StrEnum):
    PI_IMAGE = "pi_image"
    PRIMARY_STUDY_IMAGE = "primary_study_image"
    STUDY_IMAGES = "study_images"


@router.post(
    "/metadata_submission/{id}/image/{image_type}",
    response_model=schemas_submission.SubmissionMetadataSchema,
)
async def set_submission_image(
    id: str,
    image_type: ImageType,
    body: schemas.UploadCompleteRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.SubmissionMetadata:
    submission = get_submission_for_user(db, id, user, allowed_roles=context_edit_roles)

    # Create a new SubmissionImagesObject
    new_image = SubmissionImagesObject(
        name=body.object_name,
        size=body.file_size,
        content_type=body.content_type,
    )

    if image_type == ImageType.STUDY_IMAGES:
        # For study_images, add to the collection
        submission.study_images.append(new_image)
    else:
        # For single image fields (pi_image, primary_study_image), replace existing
        current_image = getattr(submission, image_type)
        if current_image:
            # If the submission already has this type of image, delete it from the storage bucket
            storage.delete_object(BucketName.SUBMISSION_IMAGES, current_image.name)

        # Set the image attribute
        setattr(submission, image_type, new_image)

    db.commit()
    return submission


@router.delete(
    "/metadata_submission/{id}/image/{image_type}",
)
async def delete_submission_image(
    id: str,
    image_type: ImageType,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    image_name: Optional[str] = Query(
        None, description="Image name for study_images, not needed for single image fields"
    ),
):
    submission = get_submission_for_user(db, id, user, allowed_roles=context_edit_roles)

    if image_type == ImageType.STUDY_IMAGES:
        if image_name is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_name query parameter is required when deleting from study_images",
            )

        # Find the specific image in the study_images collection
        image_to_delete = next(
            (image for image in submission.study_images if image.name == image_name),
            None,
        )

        if image_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Image not found in study_images"
            )

        # Delete the image from the storage bucket
        storage.delete_object(BucketName.SUBMISSION_IMAGES, image_to_delete.name)
        # Remove the image from the collection
        submission.study_images.remove(image_to_delete)
        db.delete(image_to_delete)
    else:
        # For single image fields (pi_image, primary_study_image)
        current_image = getattr(submission, image_type)
        if current_image:
            # Delete the image from the storage bucket
            storage.delete_object(BucketName.SUBMISSION_IMAGES, current_image.name)
            # Remove the image from the submission
            setattr(submission, image_type, None)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/users",
    responses=login_required_responses,
    response_model=query.Paginated[schemas.User],
    tags=["user"],
)
async def get_users(
    db: Session = Depends(get_db),
    user: models.User = Depends(admin_required),
    pagination: Pagination = Depends(),
    search_filter: Optional[str] = None,
):
    users = db.query(User).order_by(models.User.name)
    if search_filter:
        users = users.filter(
            (
                models.User.name.ilike(f"%{search_filter}%")
                | models.User.orcid.ilike(f"%{search_filter}%")
            )
        )

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
