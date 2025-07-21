from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, computed_field, field_validator

from nmdc_server import schemas
from nmdc_server.models import SubmissionEditorRole
from nmdc_server.storage import BucketName, storage


class Contributor(BaseModel):
    name: str
    orcid: str
    roles: List[str]
    permissionLevel: Optional[str] = None


class Doi(BaseModel):
    value: str
    provider: str


class StudyFormCreate(BaseModel):
    studyName: str
    piName: str
    piEmail: str
    piOrcid: str
    fundingSources: Optional[List[str]] = None
    dataDois: Optional[List[Doi]] = None
    linkOutWebpage: List[str]
    studyDate: Optional[str] = None
    description: str
    notes: str
    contributors: List[Contributor]
    # These are optional here to allow temporary Field Notes compatibility
    alternativeNames: Optional[List[str]] = None
    GOLDStudyId: Optional[str] = None
    NCBIBioProjectId: Optional[str] = None


class StudyForm(StudyFormCreate):
    alternativeNames: List[str]
    GOLDStudyId: str
    NCBIBioProjectId: str


class MultiOmicsForm(BaseModel):
    award: Optional[str] = None
    awardDois: Optional[List[Doi]] = None
    dataGenerated: Optional[bool] = None
    doe: Optional[bool] = None
    facilities: Optional[List[str]] = None
    facilityGenerated: Optional[bool] = None
    JGIStudyId: str
    mgCompatible: Optional[bool] = None
    mgInterleaved: Optional[bool] = None
    mtCompatible: Optional[bool] = None
    mtInterleaved: Optional[bool] = None
    omicsProcessingTypes: List[str]
    otherAward: Optional[str] = None
    ship: Optional[bool] = None
    studyNumber: str
    unknownDoi: Optional[bool] = None

    # This allows Field Notes to continue to send alternativeNames, GOLDStudyId, and
    # NCBIBioProjectId in this form until it catches up with the new data model in its next release
    model_config = ConfigDict(extra="allow")


class NmcdAddress(BaseModel):
    name: str
    email: str
    phone: str
    line1: str
    line2: str
    city: str
    state: str
    postalCode: str
    country: str


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


class MetadataSubmissionRecordCreate(BaseModel):
    packageName: List[str]
    addressForm: AddressForm
    templates: List[str]
    studyForm: StudyFormCreate
    multiOmicsForm: MultiOmicsForm
    sampleData: Dict[str, List[Any]]


class MetadataSubmissionRecord(MetadataSubmissionRecordCreate):
    studyForm: StudyForm


class PartialMetadataSubmissionRecord(BaseModel):
    packageName: Optional[List[str]] = None
    addressForm: Optional[AddressForm] = None
    templates: Optional[List[str]] = None
    studyForm: Optional[StudyForm] = None
    multiOmicsForm: Optional[MultiOmicsForm] = None
    sampleData: Optional[Dict[str, List[Any]]] = None


class SubmissionMetadataSchemaCreate(BaseModel):
    metadata_submission: MetadataSubmissionRecordCreate
    status: Optional[str] = None
    source_client: Optional[str] = None
    is_test_submission: bool = False


class SubmissionMetadataSchemaPatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata_submission: PartialMetadataSubmissionRecord
    status: Optional[str] = None
    # Map of ORCID iD to permission level
    permissions: Optional[Dict[str, str]] = None
    field_notes_metadata: Optional[Dict[str, Any]] = None


class SubmissionMetadataSchemaListItem(BaseModel):
    id: UUID
    author: schemas.User
    study_name: Optional[str] = None
    templates: List[str]
    status: str
    date_last_modified: datetime
    created: datetime
    is_test_submission: bool = False


class SubmissionImagesObject(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    size: int
    content_type: str


class SubmissionMetadataSchema(SubmissionMetadataSchemaListItem, SubmissionMetadataSchemaCreate):
    model_config = ConfigDict(from_attributes=True)

    author_orcid: str
    field_notes_metadata: Optional[Dict[str, Any]] = None
    metadata_submission: MetadataSubmissionRecord

    lock_updated: Optional[datetime] = None
    locked_by: Optional[schemas.User] = None

    permission_level: Optional[str] = None

    # These fields are excluded from the model's JSON representation because they need to be
    # translated into signed URLs before being returned to the client. This is done via the
    # @computed_field-decorated properties below.
    pi_image_name: Optional[str] = Field(exclude=True, default=None)
    primary_study_image_name: Optional[str] = Field(exclude=True, default=None)
    study_images_objects: list[SubmissionImagesObject] = Field(
        exclude=True, default_factory=list, alias="study_images"
    )

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

    # Mypy doesn't understand the combined use of `@computed_field` and `@property`
    # https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.computed_field
    @computed_field  # type: ignore
    @property
    def pi_image(self) -> Optional[str]:
        """Returns the signed URL for the PI's image if available."""
        if self.pi_image_name:
            return storage.get_signed_download_url(
                BucketName.SUBMISSION_IMAGES, self.pi_image_name
            ).url
        return None

    @computed_field  # type: ignore
    @property
    def primary_study_image(self) -> Optional[str]:
        """Returns the signed URL for the primary study image if available."""
        if self.primary_study_image_name:
            return storage.get_signed_download_url(
                BucketName.SUBMISSION_IMAGES, self.primary_study_image_name
            ).url
        return None

    @computed_field  # type: ignore
    @property
    def study_images(self) -> List[str]:
        """Returns a list of signed URLs for all study images."""
        if not self.study_images_objects:
            return []
        return [
            storage.get_signed_download_url(BucketName.SUBMISSION_IMAGES, img.name).url
            for img in self.study_images_objects
        ]


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
    current_value: Optional[str] = None
