from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, validator

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
    datasetDoi: str
    dataGenerated: Optional[bool] = None
    facilityGenerated: Optional[bool] = None
    facilities: List[str]
    award: Optional[str] = None
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


class SubmissionMetadataSchema(SubmissionMetadataSchemaCreate):
    id: UUID
    author_orcid: str
    created: datetime
    status: str
    author: schemas.User
    templates: List[str]
    study_name: Optional[str] = None

    lock_updated: Optional[datetime] = None
    locked_by: Optional[schemas.User] = None

    permission_level: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator`
    # manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
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


class MetadataSuggestionType(str, Enum):
    ADD = "add"
    REPLACE = "replace"


class MetadataSuggestion(BaseModel):
    type: MetadataSuggestionType
    row: int
    slot: str
    value: str
