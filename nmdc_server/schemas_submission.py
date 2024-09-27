from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, validator

from nmdc_server import schemas
from nmdc_server.models import SubmissionEditorRole


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
    fundingSources: Optional[List[str]]
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


class PartialMetadataSubmissionRecord(BaseModel):
    packageName: Optional[str]
    contextForm: Optional[ContextForm]
    addressForm: Optional[AddressForm]
    templates: Optional[List[str]]
    studyForm: Optional[StudyForm]
    multiOmicsForm: Optional[MultiOmicsForm]
    sampleData: Optional[Dict[str, List[Any]]]


class SubmissionMetadataSchemaCreate(BaseModel):
    metadata_submission: MetadataSubmissionRecord
    status: Optional[str]
    source_client: Optional[str]


class SubmissionMetadataSchemaPatch(BaseModel):
    metadata_submission: PartialMetadataSubmissionRecord
    status: Optional[str]
    # Map of ORCID iD to permission level
    permissions: Optional[Dict[str, str]]


class SubmissionMetadataSchema(SubmissionMetadataSchemaCreate):
    id: UUID
    author_orcid: str
    created: datetime
    status: str
    author: schemas.User
    templates: List[str]
    study_name: Optional[str]

    lock_updated: Optional[datetime]
    locked_by: Optional[schemas.User]

    permission_level: Optional[str]

    class Config:
        orm_mode = True

    @validator("metadata_submission", pre=True, always=True)
    def populate_roles(cls, metadata_submission, values):
        owners = set(values.get("owners", []))
        editors = set(values.get("editors", []))
        viewers = set(values.get("viewers", []))
        metadata_contributors = set(values.get("metadata_contributors", []))

        for contributor in metadata_submission.get("studyForm", {}).get("contributors", []):
            orcid = contributor.get("orcid", None)
            if orcid:
                if orcid in owners:
                    contributor["role"] = SubmissionEditorRole.owner.value
                elif orcid in editors:
                    contributor["role"] = SubmissionEditorRole.editor.value
                elif orcid in metadata_contributors:
                    contributor["role"] = SubmissionEditorRole.metadata_contributor.value
                elif orcid in viewers:
                    contributor["role"] = SubmissionEditorRole.viewer.value
        return metadata_submission


SubmissionMetadataSchema.update_forward_refs()


class MetadataSuggestionRequest(BaseModel):
    row: int
    data: Dict[str, str]


class MetadataSuggestion(BaseModel):
    op: Literal["add", "remove", "replace"]
    row: int
    slot: str
    value: str
