from io import BytesIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, StreamingResponse

from nmdc_server import crud, query, schemas
from nmdc_server.auth import get_current_user, login_required, login_required_responses, Token
from nmdc_server.config import Settings, settings
from nmdc_server.database import create_session
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
    "/biosample",
    response_model=schemas.Biosample,
    tags=["biosample"],
    responses=login_required_responses,
)
async def create_biosample(
    biosample: schemas.BiosampleCreate,
    db: Session = Depends(get_db),
    token: Token = Depends(login_required),
):
    if crud.get_project(db, biosample.study_id) is None:
        raise HTTPException(status_code=400, detail="Study does not exist")

    return crud.create_biosample(db, biosample)


@router.post(
    "/biosample/search",
    response_model=query.BiosampleSearchResponse,
    tags=["biosample"],
    name="Search for biosamples",
    description="Faceted search of biosample data.",
)
async def search_biosample(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_biosample(db, query.conditions))


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


# @router.delete(
#     "/biosample/{biosample_id}", status_code=204, tags=["biosample"],
# )
# async def delete_biosample(biosample_id: str, db: Session = Depends(get_db)):
#     db_biosample = crud.get_biosample(db, biosample_id)
#     if db_biosample is None:
#         raise HTTPException(status_code=404, detail="Biosample not found")
#     crud.delete_biosample(db, db_biosample)


# study
@router.post(
    "/study",
    response_model=schemas.Study,
    tags=["study"],
    responses=login_required_responses,
)
async def create_study(
    study: schemas.StudyCreate,
    db: Session = Depends(get_db),
    token: Token = Depends(login_required),
):
    return crud.create_study(db, study)


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


# @router.delete(
#     "/study/{study_id}", status_code=204, tags=["study"],
# )
# async def delete_study(study_id: str, db: Session = Depends(get_db)):
#     db_study = crud.get_study(db, study_id)
#     if db_study is None:
#         raise HTTPException(status_code=404, detail="Study not found")
#     crud.delete_study(db, db_study)


# project
@router.post(
    "/project",
    response_model=schemas.Project,
    tags=["project"],
    responses=login_required_responses,
)
async def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    token: Token = Depends(login_required),
):
    return crud.create_project(db, project)


@router.post(
    "/project/search",
    response_model=query.ProjectSearchResponse,
    tags=["project"],
    name="Search for studies",
    description="Faceted search of project data.",
)
async def search_project(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_project(db, query.conditions))


@router.post(
    "/project/facet",
    response_model=query.FacetResponse,
    tags=["project"],
    name="Get all values of an attribute",
)
async def facet_project(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_project(db, query.attribute, query.conditions)


@router.post(
    "/project/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["project"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_project(query: query.BinnedFacetQuery, db: Session = Depends(get_db)):
    return crud.binned_facet_project(db, **query.dict())


@router.get(
    "/project/{project_id}",
    response_model=schemas.Project,
    tags=["project"],
)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


# @router.delete(
#     "/project/{project_id}", status_code=204, tags=["project"],
# )
# async def delete_project(project_id: str, db: Session = Depends(get_db)):
#     db_project = crud.get_project(db, project_id)
#     if db_project is None:
#         raise HTTPException(status_code=404, detail="Project not found")
#     crud.delete_project(db, db_project)


@router.get(
    "/project/{project_id}/outputs",
    response_model=List[schemas.DataObject],
    tags=["project"],
)
async def list_project_data_objects(project_id: str, db: Session = Depends(get_db)):
    return crud.list_project_data_objects(db, project_id).all()


# data object
@router.post(
    "/data_object",
    response_model=schemas.DataObject,
    tags=["data_object"],
    responses=login_required_responses,
)
async def create_data_object(
    data_object: schemas.DataObjectCreate,
    db: Session = Depends(get_db),
    token: Token = Depends(login_required),
):
    return crud.create_data_object(db, data_object)


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


# @router.delete(
#     "/data_object/{data_object_id}", status_code=204, tags=["data_object"],
# )
# async def delete_data_object(data_object_id: str, db: Session = Depends(get_db)):
#     db_data_object = crud.get_data_object(db, data_object_id)
#     if db_data_object is None:
#         raise HTTPException(status_code=404, detail="DataObject not found")
#     crud.delete_data_object(db, db_data_object)


@router.post(
    "/data_object/search",
    response_model=query.DataObjectSearchResponse,
    tags=["data_object"],
    name="Search for studies",
    description="Faceted search of data_object data.",
)
async def search_data_object(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_data_object(db, query.conditions))


@router.post(
    "/data_object/facet",
    response_model=query.FacetResponse,
    tags=["data_object"],
    name="Get all values of an attribute",
)
async def facet_data_object(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_data_object(db, query.attribute, query.conditions)


@router.post(
    "/data_object/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["data_object"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_data_object(query: query.BinnedFacetQuery, db: Session = Depends(get_db)):
    return crud.binned_facet_data_object(db, **query.dict())


@router.get(
    "/data_object/{data_object_id}/download",
    tags=["data_object"],
    responses=login_required_responses,
)
async def download_data_object(
    data_object_id: str,
    user_agent: Optional[str] = Header(None),
    x_real_ip: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    token: Token = Depends(login_required),
):
    data_object = crud.get_data_object(db, data_object_id)
    if data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    url = data_object.url
    if url is None:
        raise HTTPException(status_code=404, detail="DataObject has no url reference")

    file_download = schemas.FileDownloadCreate(
        ip=x_real_ip,
        user_agent=user_agent,
        orcid=token.orcid,
        data_object_id=data_object_id,
    )
    crud.create_file_download(db, file_download)
    return RedirectResponse(url=url)


# reads_qc
@router.post(
    "/reads_qc/search",
    response_model=query.ReadsQCSearchResponse,
    tags=["reads_qc"],
    name="Search for studies",
    description="Faceted search of reads_qc data.",
)
async def search_reads_qc(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_reads_qc(db, query.conditions))


@router.post(
    "/reads_qc/facet",
    response_model=query.FacetResponse,
    tags=["reads_qc"],
    name="Get all values of an attribute",
)
async def facet_reads_qc(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_reads_qc(db, query.attribute, query.conditions)


@router.post(
    "/reads_qc/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["reads_qc"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_reads_qc(query: query.BinnedFacetQuery, db: Session = Depends(get_db)):
    return crud.binned_facet_reads_qc(db, **query.dict())


@router.get(
    "/reads_qc/{reads_qc_id}",
    response_model=schemas.ReadsQC,
    tags=["reads_qc"],
)
async def get_reads_qc(reads_qc_id: str, db: Session = Depends(get_db)):
    db_reads_qc = crud.get_reads_qc(db, reads_qc_id)
    if db_reads_qc is None:
        raise HTTPException(status_code=404, detail="ReadsQC not found")
    return db_reads_qc


@router.get(
    "/reads_qc/{reads_qc_id}/outputs",
    response_model=List[schemas.DataObject],
    tags=["reads_qc"],
)
async def list_reads_qc_data_objects(reads_qc_id: str, db: Session = Depends(get_db)):
    return crud.list_reads_qc_data_objects(db, reads_qc_id).all()


# metagenome_assembly
@router.post(
    "/metagenome_assembly/search",
    response_model=query.MetagenomeAssemblySearchResponse,
    tags=["metagenome_assembly"],
    name="Search for studies",
    description="Faceted search of metagenome_assembly data.",
)
async def search_metagenome_assembly(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_metagenome_assembly(db, query.conditions))


@router.post(
    "/metagenome_assembly/facet",
    response_model=query.FacetResponse,
    tags=["metagenome_assembly"],
    name="Get all values of an attribute",
)
async def facet_metagenome_assembly(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_metagenome_assembly(db, query.attribute, query.conditions)


@router.post(
    "/metagenome_assembly/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["metagenome_assembly"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_metagenome_assembly(
    query: query.BinnedFacetQuery, db: Session = Depends(get_db)
):
    return crud.binned_facet_metagenome_assembly(db, **query.dict())


@router.get(
    "/metagenome_assembly/{metagenome_assembly_id}",
    response_model=schemas.MetagenomeAssembly,
    tags=["metagenome_assembly"],
)
async def get_metagenome_assembly(metagenome_assembly_id: str, db: Session = Depends(get_db)):
    db_metagenome_assembly = crud.get_metagenome_assembly(db, metagenome_assembly_id)
    if db_metagenome_assembly is None:
        raise HTTPException(status_code=404, detail="MetagenomeAssembly not found")
    return db_metagenome_assembly


@router.get(
    "/metagenome_assembly/{metagenome_assembly_id}/outputs",
    response_model=List[schemas.DataObject],
    tags=["metagenome_assembly"],
)
async def list_metagenome_assembly_data_objects(
    metagenome_assembly_id: str, db: Session = Depends(get_db)
):
    return crud.list_metagenome_assembly_data_objects(db, metagenome_assembly_id).all()


# metagenome_annotation
@router.post(
    "/metagenome_annotation/search",
    response_model=query.MetagenomeAnnotationSearchResponse,
    tags=["metagenome_annotation"],
    name="Search for studies",
    description="Faceted search of metagenome_annotation data.",
)
async def search_metagenome_annotation(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_metagenome_annotation(db, query.conditions))


@router.post(
    "/metagenome_annotation/facet",
    response_model=query.FacetResponse,
    tags=["metagenome_annotation"],
    name="Get all values of an attribute",
)
async def facet_metagenome_annotation(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_metagenome_annotation(db, query.attribute, query.conditions)


@router.post(
    "/metagenome_annotation/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["metagenome_annotation"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_metagenome_annotation(
    query: query.BinnedFacetQuery, db: Session = Depends(get_db)
):
    return crud.binned_facet_metagenome_annotation(db, **query.dict())


@router.get(
    "/metagenome_annotation/{metagenome_annotation_id}",
    response_model=schemas.MetagenomeAnnotation,
    tags=["metagenome_annotation"],
)
async def get_metagenome_annotation(metagenome_annotation_id: str, db: Session = Depends(get_db)):
    db_metagenome_annotation = crud.get_metagenome_annotation(db, metagenome_annotation_id)
    if db_metagenome_annotation is None:
        raise HTTPException(status_code=404, detail="MetagenomeAnnotation not found")
    return db_metagenome_annotation


@router.get(
    "/metagenome_annotation/{metagenome_annotation_id}/outputs",
    response_model=List[schemas.DataObject],
    tags=["metagenome_annotation"],
)
async def list_metagenome_annotation_data_objects(
    metagenome_annotation_id: str, db: Session = Depends(get_db)
):
    return crud.list_metagenome_annotation_data_objects(db, metagenome_annotation_id).all()


# metagenome_annotation
@router.post(
    "/metaproteomic_analysis/search",
    response_model=query.MetaproteomicAnalysisSearchResponse,
    tags=["metaproteomic_analysis"],
    name="Search for studies",
    description="Faceted search of metaproteomic_analysis data.",
)
async def search_metaproteomic_analysis(
    query: query.SearchQuery = query.SearchQuery(),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    return pagination.response(crud.search_metaproteomic_analysis(db, query.conditions))


@router.post(
    "/metaproteomic_analysis/facet",
    response_model=query.FacetResponse,
    tags=["metaproteomic_analysis"],
    name="Get all values of an attribute",
)
async def facet_metaproteomic_analysis(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_metaproteomic_analysis(db, query.attribute, query.conditions)


@router.post(
    "/metaproteomic_analysis/binned_facet",
    response_model=query.BinnedFacetResponse,
    tags=["metaproteomic_analysis"],
    name="Get all values of a non-string attribute with binning",
)
async def binned_facet_metaproteomic_analysis(
    query: query.BinnedFacetQuery, db: Session = Depends(get_db)
):
    return crud.binned_facet_metaproteomic_analysis(db, **query.dict())


@router.get(
    "/metaproteomic_analysis/{metaproteomic_analysis_id}",
    response_model=schemas.MetaproteomicAnalysis,
    tags=["metaproteomic_analysis"],
)
async def get_metaproteomic_analysis(metaproteomic_analysis_id: str, db: Session = Depends(get_db)):
    db_metaproteomic_analysis = crud.get_metaproteomic_analysis(db, metaproteomic_analysis_id)
    if db_metaproteomic_analysis is None:
        raise HTTPException(status_code=404, detail="MetaproteomicAnalysis not found")
    return db_metaproteomic_analysis


@router.get(
    "/metaproteomic_analysis/{metaproteomic_analysis_id}/outputs",
    response_model=List[schemas.DataObject],
    tags=["metaproteomic_analysis"],
)
async def list_metaproteomic_analysis_data_objects(
    metaproteomic_analysis_id: str, db: Session = Depends(get_db)
):
    return crud.list_metaproteomic_analysis_data_objects(db, metaproteomic_analysis_id).all()


@router.get("/principal_investigator/{principal_investigator_id}", tags=["principal_investigator"])
async def get_pi_image(principal_investigator_id: UUID, db: Session = Depends(get_db)):
    image = crud.get_pi_image(db, principal_investigator_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Principal investigator  not found")

    return StreamingResponse(BytesIO(image), media_type="image/jpeg")
