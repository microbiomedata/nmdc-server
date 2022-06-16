from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel


class Contributor(BaseModel):
    name: str
    orcid: str
    roles: List[str]


class StudyForm(BaseModel):
    studyName: str
    piName: str
    piEmail: str
    piOrcid: str
    linkOutWebpage: List[str]
    studyDate: Optional[str]
    description: str
    notes: str
    contributors: List[Contributor]


class MultiOmicsForm(BaseModel):
    datasetDoi: str
    alternativeNames: List[str]
    studyNumber: str
    GOLDStudyId: str
    JGIStudyId: str
    NCBIBioProjectName: str
    NCBIBioProjectId: str
    omicsProcessingTypes: List[str]


class MetadataSubmissionRecord(BaseModel):
    packageName: str
    template: str
    studyForm: StudyForm
    multiOmicsForm: MultiOmicsForm
    sampleData: List[List[Any]]


class SubmissionMetadataSchemaCreate(BaseModel):
    metadata_submission: MetadataSubmissionRecord
    status: Optional[str]


class SubmissionMetadataSchema(SubmissionMetadataSchemaCreate):
    id: UUID
    author_orcid: str
    created: datetime
    status: str

    class Config:
        orm_mode = True


SubmissionMetadataSchema.update_forward_refs()
