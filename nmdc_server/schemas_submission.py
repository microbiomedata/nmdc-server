from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from nmdc_server import schemas


class Contributor(BaseModel):
    name: str
    orcid: str
    roles: List[str]
    permissionLevel: Optional[str]


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
    alternativeNames: List[str]
    studyNumber: str
    GOLDStudyId: str
    JGIStudyId: str
    NCBIBioProjectId: str
    omicsProcessingTypes: List[str]


class NmcdAddress(BaseModel):
    name: str
    email: str
    phone: str
    line1: str
    line2: str
    city: str
    state: str
    postalCode: str


class AddressForm(BaseModel):
    shipper: NmcdAddress
    expectedShippingDate: Optional[datetime]
    shippingConditions: str
    sample: str
    description: str
    experimentalGoals: str
    randomization: str
    usdaRegulated: Optional[bool]
    permitNumber: str
    biosafetyLevel: str
    irbOrHipaa: Optional[bool]
    comments: str


class ContextForm(BaseModel):
    datasetDoi: str
    dataGenerated: Optional[bool]
    facilityGenerated: Optional[bool]
    facilities: List[str]
    award: Optional[str]
    otherAward: str


class MetadataSubmissionRecord(BaseModel):
    packageName: str
    contextForm: ContextForm
    addressForm: AddressForm
    templates: List[str]
    studyForm: StudyForm
    multiOmicsForm: MultiOmicsForm
    sampleData: Dict[str, List[Any]]


class SubmissionMetadataSchemaCreate(BaseModel):
    metadata_submission: MetadataSubmissionRecord
    status: Optional[str]


class SubmissionMetadataSchema(SubmissionMetadataSchemaCreate):
    id: UUID
    author_orcid: str
    created: datetime
    status: str
    author: schemas.User

    lock_updated: Optional[datetime]
    locked_by: Optional[schemas.User]

    class Config:
        orm_mode = True


SubmissionMetadataSchema.update_forward_refs()
