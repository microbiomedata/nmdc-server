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


@router.post(
    "/biosample/search",
    response_model=query.BiosampleSearchResponse,
    tags=["biosample"],
    name="Search for biosamples",
    description="Faceted search of biosample data.",
)
async def search(query: query.BiosampleSearchQuery, db: Session = Depends(get_db)):
    return {"results": list(crud.search_biosample(db, query.conditions))}


@router.get("/study/{study_id}", response_model=schemas.Study)
async def get_study(study_id: str, db: Session = Depends(get_db)):
    db_study = crud.get_study(db, study_id)
    if db_study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return db_study


@router.get("/project/{project_id}", response_model=schemas.Project)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.get("/biosample/{biosample_id}", response_model=schemas.Biosample)
async def get_biosample(biosample_id: str, db: Session = Depends(get_db)):
    db_biosample = crud.get_biosample(db, biosample_id)
    if db_biosample is None:
        raise HTTPException(status_code=404, detail="Biosample not found")
    return db_biosample


@router.delete("/biosample/{biosample_id}", status_code=204)
async def delete_biosample(biosample_id: str, db: Session = Depends(get_db)):
    db_biosample = crud.get_biosample(db, biosample_id)
    if db_biosample is None:
        raise HTTPException(status_code=404, detail="Biosample not found")
    crud.delete_biosample(db, db_biosample)


@router.post("/biosample", response_model=schemas.Biosample)
async def create_biosample(biosample: schemas.BiosampleCreate, db: Session = Depends(get_db)):
    if crud.get_project(db, biosample.project_id) is None:
        raise HTTPException(status_code=400, detail="Project does not exist")

    return crud.create_biosample(db, biosample)


@router.get("/data_object/{data_object_id}", response_model=schemas.DataObject)
async def get_data_object(data_object_id: str, db: Session = Depends(get_db)):
    db_data_object = crud.get_data_object(db, data_object_id)
    if db_data_object is None:
        raise HTTPException(status_code=404, detail="DataObject not found")
    return db_data_object
