from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from nmdc_server import schemas
from nmdc_server.models import SubmissionEditorRole


class Contributor(BaseModel):
    name: str
    orcid: str
    roles: List[str]
    permissionLevel: Optional[str] = None


class StudyForm(BaseModel):
    studyName: str
    piName: str
    piEmail: str
    piOrcid: str
    fundingSources: Optional[List[str]] = None
    linkOutWebpage: List[str]
    studyDate: Optional[str] = None
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
    expectedShippingDate: Optional[datetime] = None
    shippingConditions: str
    sample: str
    description: str
    experimentalGoals: str
    randomization: str
    usdaRegulated: Optional[bool] = None
    permitNumber: str
    biosafetyLevel: str
    irbOrHipaa: Optional[bool] = None
    comments: str


class ContextForm(BaseModel):
    awardDois: Optional[List[str]] = None
    dataGenerated: Optional[bool] = None
    facilityGenerated: Optional[bool] = None
    facilities: List[str]
    award: Optional[str] = None
    otherAward: str
    unknownDoi: Optional[bool] = None


class MetadataSubmissionRecord(BaseModel):
    packageName: str
    contextForm: ContextForm
    addressForm: AddressForm
    templates: List[str]
    studyForm: StudyForm
    multiOmicsForm: MultiOmicsForm
    sampleData: Dict[str, List[Any]]


class PartialMetadataSubmissionRecord(BaseModel):
    packageName: Optional[str] = None
    contextForm: Optional[ContextForm] = None
    addressForm: Optional[AddressForm] = None
    templates: Optional[List[str]] = None
    studyForm: Optional[StudyForm] = None
    multiOmicsForm: Optional[MultiOmicsForm] = None
    sampleData: Optional[Dict[str, List[Any]]] = None


class SubmissionMetadataSchemaCreate(BaseModel):
    metadata_submission: MetadataSubmissionRecord
    status: Optional[str] = None
    source_client: Optional[str] = None


class SubmissionMetadataSchemaPatch(BaseModel):
    metadata_submission: PartialMetadataSubmissionRecord
    status: Optional[str] = None
    # Map of ORCID iD to permission level
    permissions: Optional[Dict[str, str]] = None
    field_notes_metadata: Optional[Dict[str, Any]] = None


class SubmissionMetadataSchema(SubmissionMetadataSchemaCreate):
    id: UUID
    author_orcid: str
    created: datetime
    status: str
    author: schemas.User
    templates: List[str]
    study_name: Optional[str] = None
    field_notes_metadata: Optional[Dict[str, Any]] = None
    isTestSubmission: bool = False

    lock_updated: Optional[datetime] = None
    locked_by: Optional[schemas.User] = None

    permission_level: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("metadata_submission", mode="before")
    def populate_roles(cls, metadata_submission, info: ValidationInfo):
        owners = set(info.data.get("owners", []))
        editors = set(info.data.get("editors", []))
        viewers = set(info.data.get("viewers", []))
        metadata_contributors = set(info.data.get("metadata_contributors", []))

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


SubmissionMetadataSchema.model_rebuild()


class MetadataSuggestionRequest(BaseModel):
    row: int
    data: Dict[str, str]


class MetadataSuggestionType(str, Enum):
    ADD = "add"
    REPLACE = "replace"


class MetadataSuggestion(BaseModel):
    type: MetadataSuggestionType
    row: int
    slot: str
    value: str
