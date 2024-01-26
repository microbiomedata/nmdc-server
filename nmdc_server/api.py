from io import BytesIO
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, StreamingResponse

from nmdc_server import __version__, crud, jobs, models, query, schemas, schemas_submission
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
from nmdc_server.models import (
    IngestLock,
    SubmissionEditorRole,
    SubmissionMetadata,
    SubmissionRole,
    User,
)
from nmdc_server.pagination import Pagination

router = APIRouter()


# get application settings
@router.get("/settings", name="Get application settings")
async def get_settings() -> Dict[str, Any]:
    settings = Settings()
    return {"disable_bulk_download": settings.disable_bulk_download.upper() == "YES"}


# get application version number
@router.get("/version", name="Get application version identifier")
async def get_version() -> Dict[str, Any]:
    return {"nmdc-server": __version__}


# get the current user information
@router.get("/me", tags=["user"], name="Return the current user name")
async def me(request: Request, user: str = Depends(get_current_user)) -> Optional[str]:
    return user


@router.get("/me/orcid", tags=["user"], name="Return the ORCID iD of current user")
async def my_orcid(request: Request, orcid: str = Depends(get_current_user_orcid)) -> Optional[str]:
    return orcid


# autocomplete search
@router.get(
    "/search",
    tags=["aggregation"],
    response_model=List[query.ConditionResultSchema],
)
def text_search(terms: str, limit=6, db: Session = Depends(get_db)):
    # Add 'ilike' filters for study columns users may want to search by
    study_name_filter = {
        "table": "study",
        "value": terms.lower(),
        "field": "name",
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
    # These two lists are of objects of separate types
    filters = crud.text_search(db, terms, limit)
    plaintext_filters = [
        query.SimpleConditionSchema(**study_name_filter),
        query.SimpleConditionSchema(**study_description_filter),
        query.SimpleConditionSchema(**study_title_filter),
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
    q: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
    flat: bool = False,
):
    if not flat:
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

        #     """
        #     If there are children studies that match the query, but the top level studies do not,
        #     add the parent to the top level studies
        #     """
        for child in children_studies:
            for parent_id in child.part_of:
                if parent_id not in [
                    parent.id for parent in top_level_studies
                ] and child.id not in [parent.id for parent in top_level_studies]:
                    top_level_studies.append(child)

        for parent in top_level_studies:
            parent.children = []
            for child in children_studies:
                if child.part_of is not None and parent.id in child.part_of:
                    parent.children.append(child)

        count = len(top_level_studies)

        total = crud.search_study(db, q.conditions).count()

        structured_results: query.StudySearchResponse = query.StudySearchResponse(
            count=count,
            results=top_level_studies[pagination.offset : pagination.limit + pagination.offset],
            total=total,
        )
        return structured_results

    return pagination.response(crud.search_study(db, q.conditions))


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


# omics_processing
@router.post(
    "/omics_processing/search",
    response_model=query.OmicsProcessingSearchResponse,
    tags=["omics_processing"],
    name="Search for omics processings",
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
        query = crud.get_submissions_for_user(db, user)
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
    _ = crud.try_get_submission_lock(db, submission.id, user.id)
    if user.is_admin or crud.can_edit_entire_submission(db, id, user.orcid):
        permission_level = None
        if user.is_admin or user.orcid in submission.owners:
            permission_level = models.SubmissionEditorRole.owner.value
        elif user.orcid in submission.editors:
            permission_level = models.SubmissionEditorRole.editor.value
        elif user.orcid in submission.metadata_contributor:
            permission_level = models.SubmissionEditorRole.metadata_contributor.value
        elif user.orcid in submission.viewer:
            permission_level = models.SubmissionEditorRole.viewer.value
        return schemas_submission.SubmissionMetadataSchema(
            **submission.__dict__,
            author=schemas.User(**submission.author.__dict__),
            locked_by=schemas.User(**submission.locked_by.__dict__),
            permission_level=permission_level
        )
    raise HTTPException(status_code=403, detail="Must have access.")


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

    if not (user.is_admin or crud.can_edit_entire_submission(db, id, user.orcid)):
        raise HTTPException(403, detail="Must have access.")

    has_lock = crud.try_get_submission_lock(db, submission.id, user.id)
    if not has_lock:
        raise HTTPException(
            status_code=400,
            detail="This submission is currently being edited by a different user.",
        )

    submission.metadata_submission = body_dict["metadata_submission"]
    pi_orcid = body_dict["metadata_submission"].get("studyForm", {}).get("piOrcid", None)
    if pi_orcid and pi_orcid not in submission.owners:
        # Create an owner role for the PI if it doesn't exist
        pi_owner_role = SubmissionRole(
            submission_id=id, user_orcid=pi_orcid, role=SubmissionEditorRole.owner.value
        )
        db.add(pi_owner_role)

    contributors = body_dict["metadata_submission"].get("studyForm", {}).get("contributors", [])
    contributors = [schemas_submission.Contributor(**c) for c in contributors]
    crud.update_submission_contributor_roles(db, submission, contributors)

    crud.update_submission_lock(db, submission.id)
    if body_dict["status"]:
        submission.status = body_dict["status"]
    db.commit()
    return submission


@router.put("/metadata_submission/{id}/unlock")
async def unlock_submission(
    id: str, db: Session = Depends(get_db), user: models.User = Depends(login_required)
) -> str:
    submission = db.query(SubmissionMetadata).get(id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    # Then verify session user has the lock
    has_lock = crud.try_get_submission_lock(db, submission.id, user.id)
    if not has_lock:
        raise HTTPException(
            status_code=400, detail="This submission is currently being edited by a different user."
        )
    else:
        crud.release_submission_lock(db, submission.id)
        return f"Submission lock released successfully for submission with ID {id}"


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
