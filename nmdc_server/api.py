from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, query, schemas
from .config import Settings, settings
from .database import create_session
from .pagination import Pagination


router = APIRouter()


# Dependency
def get_settings():
    yield settings


def get_db(settings: Settings = Depends(get_settings)):
    with create_session() as db:
        yield db


# database summary
@router.get(
    "/summary",
    response_model=schemas.DatabaseSummary,
    tags=["summary"],
    response_model_exclude_unset=True,
)
async def get_database_summary(db: Session = Depends(get_db)):
    return crud.get_database_summary(db)


# biosample
@router.post(
    "/biosample", response_model=schemas.Biosample, tags=["biosample"],
)
async def create_biosample(
    biosample: schemas.BiosampleCreate,
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(),
):
    if crud.get_project(db, biosample.project_id) is None:
        raise HTTPException(status_code=400, detail="Project does not exist")

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


@router.get(
    "/biosample/{biosample_id}", response_model=schemas.Biosample, tags=["biosample"],
)
async def get_biosample(biosample_id: str, db: Session = Depends(get_db)):
    db_biosample = crud.get_biosample(db, biosample_id)
    if db_biosample is None:
        raise HTTPException(status_code=404, detail="Biosample not found")
    return db_biosample


@router.delete(
    "/biosample/{biosample_id}", status_code=204, tags=["biosample"],
)
async def delete_biosample(biosample_id: str, db: Session = Depends(get_db)):
    db_biosample = crud.get_biosample(db, biosample_id)
    if db_biosample is None:
        raise HTTPException(status_code=404, detail="Biosample not found")
    crud.delete_biosample(db, db_biosample)


# study
@router.post(
    "/study", response_model=schemas.Study, tags=["study"],
)
async def create_study(study: schemas.StudyCreate, db: Session = Depends(get_db)):
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


@router.get(
    "/study/{study_id}", response_model=schemas.Study, tags=["study"],
)
async def get_study(study_id: str, db: Session = Depends(get_db)):
    db_study = crud.get_study(db, study_id)
    if db_study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return db_study


@router.delete(
    "/study/{study_id}", status_code=204, tags=["study"],
)
async def delete_study(study_id: str, db: Session = Depends(get_db)):
    db_study = crud.get_study(db, study_id)
    if db_study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    crud.delete_study(db, db_study)


# project
@router.post(
    "/project", response_model=schemas.Project, tags=["project"],
)
async def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
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


@router.get(
    "/project/{project_id}", response_model=schemas.Project, tags=["project"],
)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.delete(
    "/project/{project_id}", status_code=204, tags=["project"],
)
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    crud.delete_project(db, db_project)


# data object
@router.post(
    "/data_object", response_model=schemas.DataObject, tags=["data object"],
)
async def create_data_object(data_object: schemas.DataObjectCreate, db: Session = Depends(get_db)):
    return crud.create_data_object(db, data_object)


@router.get(
    "/data_object/{data_object_id}", response_model=schemas.DataObject, tags=["data object"],
)
async def get_data_object(data_object_id: str, db: Session = Depends(get_db)):
    db_data_object = crud.get_data_object(db, data_object_id)
    if db_data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    return db_data_object


@router.delete(
    "/data_object/{data_object_id}", status_code=204, tags=["data object"],
)
async def delete_data_object(data_object_id: str, db: Session = Depends(get_db)):
    db_data_object = crud.get_data_object(db, data_object_id)
    if db_data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    crud.delete_data_object(db, db_data_object)


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


@router.get(
    "/reads_qc/{reads_qc_id}", response_model=schemas.ReadsQC, tags=["reads_qc"],
)
async def get_reads_qc(reads_qc_id: str, db: Session = Depends(get_db)):
    db_reads_qc = crud.get_reads_qc(db, reads_qc_id)
    if db_reads_qc is None:
        raise HTTPException(status_code=404, detail="ReadsQC not found")
    return db_reads_qc


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


@router.post(
    "/metaproteomic_analysis/facet",
    response_model=query.FacetResponse,
    tags=["metaproteomic_analysis"],
    name="Get all values of an attribute",
)
async def facet_metaproteomic_analysis(query: query.FacetQuery, db: Session = Depends(get_db)):
    return crud.facet_metaproteomic_analysis(db, query.attribute, query.conditions)


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
