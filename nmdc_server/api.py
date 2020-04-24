from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, query, schemas
from .config import Settings
from .database import create_session


router = APIRouter()


# Dependency
def get_settings():
    yield Settings()


def get_db(settings: Settings = Depends(get_settings)):
    with create_session() as db:
        yield db


# biosample
@router.post(
    "/biosample", response_model=schemas.Biosample, tags=["biosample"],
)
async def create_biosample(biosample: schemas.BiosampleCreate, db: Session = Depends(get_db)):
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
async def search_biosample(query: query.SearchQuery, db: Session = Depends(get_db)):
    return {"results": list(crud.search_biosample(db, query.conditions))}


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
async def search_study(query: query.SearchQuery, db: Session = Depends(get_db)):
    return {"results": list(crud.search_study(db, query.conditions))}


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
async def search_project(query: query.SearchQuery, db: Session = Depends(get_db)):
    return {"results": list(crud.search_project(db, query.conditions))}


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


@router.post(
    "/data_object/search",
    response_model=query.DataObjectSearchResponse,
    tags=["data object"],
    name="Search for studies",
    description="Faceted search of data object data.",
)
async def search_data_object(query: query.SearchQuery, db: Session = Depends(get_db)):
    return {"results": list(crud.search_data_object(db, query.conditions))}


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
