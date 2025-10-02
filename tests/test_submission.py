import json
from csv import DictReader
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi.encoders import jsonable_encoder
from nmdc_schema.nmdc import SubmissionStatusEnum
from sqlalchemy.orm.session import Session
from starlette.testclient import TestClient

from nmdc_server import fakes
from nmdc_server.models import SubmissionEditorRole, SubmissionImagesObject, SubmissionRole
from nmdc_server.schemas_submission import SubmissionMetadataSchema, SubmissionMetadataSchemaPatch
from nmdc_server.storage import BucketName


@pytest.fixture
def suggest_payload():
    return [
        {"row": 1, "data": {"foo": "bar", "lat_lon": "44.058648, -123.095277"}},
        {"row": 3, "data": {"elev": "0", "lat_lon": "44.046389 -123.051910"}},
        {"row": 4, "data": {"foo": "bar"}},
        {"row": 5, "data": {"lat_lon": "garbage foo bar"}},
    ]


def test_list_submissions(db: Session, client: TestClient, logged_in_user):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    response = client.request(method="GET", url="/api/metadata_submission")
    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == str(submission.id)


def test_get_metadata_submissions_mixs_as_non_admin(
    db: Session, client: TestClient, logged_in_user
):
    response = client.request(method="GET", url="/api/metadata_submission/mixs_report")
    assert response.status_code == 403


def test_get_metadata_submissions_mixs_as_admin(
    db: Session, client: TestClient, logged_in_admin_user
):
    now = datetime.now(tz=UTC)

    # Create logged in user
    logged_in_user = logged_in_admin_user  # allows us to reuse some code snippets

    # Create test submission
    # submission1 has "Submitted- Pending Review" as the status (this is the one we want)
    submission1 = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        created=now,
        status=SubmissionStatusEnum.SubmittedPendingReview.text,
        metadata_submission={
            "sampleData": {
                "built_env_data": [
                    {
                        "samp_name": "Sample A",
                        "env_medium": "Medium A",
                        "env_broad_scale": "Broad Scale A",
                        "env_local_scale": "Local Scale A",
                    },
                    {
                        "samp_name": "Sample B",
                        "env_medium": "Medium B",
                        "env_broad_scale": "Broad Scale B",
                        "env_local_scale": "Local Scale B",
                    },
                ]
            },
            "packageName": "Env Pkg 1",
        },
    )
    db.commit()
    response = client.request(method="get", url="/api/metadata_submission/mixs_report")
    assert response.status_code == 200

    # Check that the reponse payload is a TSV and that the result has the correct
    # number of rows and information populated. The result should have 3 rows
    # including a header.
    # Reference: https://docs.python.org/3/library/csv.html#csv.DictReader

    fieldnames = [
        "Submission ID",
        "Status",
        "Sample Name",
        "Environmental Package/Extension",
        "Environmental Broad Scale",
        "Environmental Local Scale",
        "Environmental Medium",
        "Package T/F",
        "Broad Scale T/F",
        "Local Scale T/F",
        "Medium T/F",
    ]
    reader = DictReader(response.text.splitlines(), fieldnames=fieldnames, delimiter="\t")
    rows = [row for row in reader]
    assert len(rows) == 3  # including the header row

    header_row = rows[0]  # get the header row
    assert len(list(header_row.keys())) == len(fieldnames)

    data_row = rows[1]  # first data row (data about Sample A in submission1)
    assert data_row["Submission ID"] == str(submission1.id)
    assert data_row["Status"] == SubmissionStatusEnum.SubmittedPendingReview.text
    assert data_row["Sample Name"] == "Sample A"
    assert data_row["Environmental Package/Extension"] == "Env Pkg 1"
    assert data_row["Environmental Broad Scale"] == "Broad Scale A"
    assert data_row["Environmental Local Scale"] == "Local Scale A"
    assert data_row["Environmental Medium"] == "Medium A"
    assert data_row["Package T/F"] == "False"
    assert data_row["Broad Scale T/F"] == "False"
    assert data_row["Local Scale T/F"] == "False"
    assert data_row["Medium T/F"] == "False"

    data_row = rows[2]  # second data row (data about Sample B in submission1)
    assert data_row["Submission ID"] == str(submission1.id)
    assert data_row["Status"] == SubmissionStatusEnum.SubmittedPendingReview.text
    assert data_row["Sample Name"] == "Sample B"
    assert data_row["Environmental Package/Extension"] == "Env Pkg 1"
    assert data_row["Environmental Broad Scale"] == "Broad Scale B"
    assert data_row["Environmental Local Scale"] == "Local Scale B"
    assert data_row["Environmental Medium"] == "Medium B"
    assert data_row["Package T/F"] == "False"
    assert data_row["Broad Scale T/F"] == "False"
    assert data_row["Local Scale T/F"] == "False"
    assert data_row["Medium T/F"] == "False"


def test_get_metadata_submissions_report_as_non_admin(
    db: Session, client: TestClient, logged_in_user
):
    response = client.request(method="GET", url="/api/metadata_submission/report")
    assert response.status_code == 403


def test_get_metadata_submissions_report_as_admin(
    db: Session, client: TestClient, logged_in_admin_user
):
    now = datetime.now(tz=UTC)

    # Create two submissions, only one of which is owned by the logged-in user.
    logged_in_user = logged_in_admin_user  # allows us to reuse some code snippets
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        created=now,
        is_test_submission=False,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    other_user = fakes.UserFactory()
    other_submission = fakes.MetadataSubmissionFactory(
        author=other_user,
        author_orcid=other_user.orcid,
        created=now + timedelta(seconds=1),
        # TODO: Omit some optional fields in order to simplify the test data.
        # See: `class MetadataSubmissionRecordCreate` in `schema_submission.py`
        # See: https://microbiomedata.github.io/submission-schema/SampleData/
        metadata_submission={
            "sampleData": {
                "soil_data": [
                    {
                        "ph": "\n4\n",
                        "depth": ".10-.20 meters",
                        "ph_meth": (
                            "Zhang, Hailin, and Kendal Henderson. Procedures used by OSU Soil, "
                            "Water and Forage Analytical Laboratory. "
                            "Oklahoma Cooperative Extension "
                            "Service, 2016."
                        ),
                        "ecosystem": "Environmental",
                        "fao_class": "Histosols",
                        "samp_name": "June2016WEW_Plot6_D2",
                        "samp_size": "+10 grams",
                        "env_medium": "peat soil [ENVO:00005774]",
                        "store_cond": "frozen",
                        "annual_temp": "5.0 C",
                        "cur_land_use": "conifers",
                        "geo_loc_name": "USA: Minnesota, Marcel Experimental Forest",
                        "growth_facil": "field",
                        "analysis_type": ["metagenomics"],
                        "annual_precpt": "804 mm/year",
                        "water_content": "84 %",
                        "ecosystem_type": "Soil",
                        "collection_date": "08/23/2016",
                        "env_broad_scale": "__temperate woodland biome [ENVO:01000221]",
                        "env_local_scale": "peatland [ENVO:00000044]",
                        "samp_store_temp": "-80",
                        "ecosystem_subtype": "Peat",
                        "ecosystem_category": "Terrestrial",
                        "samp_collec_device": "russian corer",
                        "specific_ecosystem": "Bog",
                        "gaseous_environment": "ambient",
                        "water_cont_soil_meth": (
                            'Gardner, Walter H. "Water content." Methods of Soil Analysis: '
                            "Part 1 Physical and Mineralogical Methods 5 (1986): 493-544."
                        ),
                    },
                    {
                        "ph": "\n4\n",
                        "depth": "\n.40-.50\n",
                        "lat_lon": "47.506961 -93.455715",
                        "ph_meth": (
                            "Zhang, Hailin, and Kendal Henderson. Procedures used by OSU Soil, "
                            "Water and Forage Analytical Laboratory. "
                            "Oklahoma Cooperative Extension "
                            "Service, 2016."
                        ),
                        "ecosystem": "Environmental",
                        "fao_class": "Histosols",
                        "samp_name": "Aug2016WEW_Plot6_D5",
                        "samp_size": "+10 grams",
                        "env_medium": "peat soil [ENVO:00005774]",
                        "annual_temp": "5.0 C",
                        "cur_land_use": "conifers (e.g. pine,spruce,fir,cypress)",
                        "geo_loc_name": "USA: Minnesota, Marcel Experimental Forest",
                        "analysis_type": ["metagenomics"],
                        "annual_precpt": "804 mm/year",
                        "water_content": "\n84%\n",
                        "ecosystem_type": "Soil",
                        "collection_date": "08/23/2016",
                        "env_broad_scale": "__temperate woodland biome [ENVO:01000221]",
                        "env_local_scale": "peatland [ENVO:00000044]",
                        "samp_store_temp": "-80",
                        "ecosystem_subtype": "Peat",
                        "ecosystem_category": "Terrestrial",
                        "samp_collec_device": "russian corer",
                        "specific_ecosystem": "Bog",
                        "gaseous_environment": "ambient",
                        "water_cont_soil_meth": (
                            'Gardner, Walter H. "Water content." Methods of Soil Analysis: '
                            "Part 1 Physical and Mineralogical Methods 5 (1986): 493-544."
                        ),
                    },
                ],
                "jgi_mg_data": [
                    {"samp_name": "June2016WEW_Plot6_D2", "analysis_type": ["metagenomics"]},
                    {"samp_name": "Aug2016WEW_Plot6_D5", "analysis_type": ["metagenomics"]},
                ],
            },
            "multiOmicsForm": {
                "studyNumber": "",
                "JGIStudyId": "",
                "omicsProcessingTypes": [],
                "facilities": [],
                "otherAward": "",
                "doe": None,
                "dataGenerated": None,
                "facilityGenerated": None,
                "award": None,
                "awardDois": [],
                "mgCompatible": None,
            },
            "studyForm": {
                "studyName": "My study name",
                "piName": "My PI name",
                "piEmail": "My PI email",
                "piOrcid": "",
                "linkOutWebpage": [],
                "fundingSources": [],
                "description": "",
                "notes": "",
                "contributors": [],
                "alternativeNames": [],
                "GOLDStudyId": "",
                "NCBIBioProjectId": "",
            },
            "templates": [],
            "addressForm": {
                "shipper": {
                    "name": "",
                    "email": "",
                    "phone": "",
                    "line1": "",
                    "line2": "",
                    "city": "",
                    "state": "",
                    "postalCode": "",
                    "country": "",
                },
                "shippingConditions": "",
                "sample": "",
                "description": "",
                "experimentalGoals": "",
                "randomization": "",
                "permitNumber": "",
                "biosafetyLevel": "",
                "comments": "",
            },
            "packageName": [],
        },
        is_test_submission=True,
        status=SubmissionStatusEnum.InProgress.text,
        source_client="field_notes",
    )
    db.commit()

    response = client.request(method="GET", url="/api/metadata_submission/report")
    assert response.status_code == 200

    # Confirm the response payload is a TSV file having the fields and values we expect;
    # i.e. below its header row, it has two data rows, each representing a submission,
    # ordered from most recently-created to least recently-created.
    # Reference: https://docs.python.org/3/library/csv.html#csv.DictReader
    fieldnames = [
        "Submission ID",
        "Author ORCID",
        "Author Name",
        "Study Name",
        "PI Name",
        "PI Email",
        "Source Client",
        "Status",
        "Is Test Submission",
        "Date Last Modified",
        "Date Created",
        "Number of Samples",
    ]
    reader = DictReader(response.text.splitlines(), fieldnames=fieldnames, delimiter="\t")
    rows = [row for row in reader]
    assert len(rows) == 3  # includes the header row

    header_row = rows[0]  # gets the header row
    assert len(list(header_row.keys())) == len(fieldnames)

    data_row = rows[1]  # gets the first data row (the most recently-created submission)
    assert data_row["Submission ID"] == str(other_submission.id)
    assert data_row["Author ORCID"] == other_user.orcid
    assert data_row["Author Name"] == other_user.name
    assert data_row["Study Name"] == "My study name"
    assert data_row["PI Name"] == "My PI name"
    assert data_row["PI Email"] == "My PI email"
    assert data_row["Source Client"] == "field_notes"
    assert data_row["Status"] == SubmissionStatusEnum.InProgress.text
    assert data_row["Is Test Submission"] == "True"
    assert data_row["Number of Samples"] == "4"
    assert isinstance(data_row["Date Last Modified"], str)
    assert isinstance(data_row["Date Created"], str)

    data_row = rows[2]  # gets the second data row
    assert data_row["Submission ID"] == str(submission.id)
    assert data_row["Author ORCID"] == logged_in_user.orcid
    assert data_row["Author Name"] == logged_in_user.name
    assert data_row["Study Name"] == ""
    assert data_row["PI Name"] == ""
    assert data_row["PI Email"] == ""
    assert data_row["Source Client"] == ""  # upstream faker lacks `source_client` attribute
    assert (
        data_row["Status"] == SubmissionStatusEnum.InProgress.text
    )  # matches value in upstream faker
    assert data_row["Is Test Submission"] == "False"
    assert data_row["Number of Samples"] == "0"
    assert isinstance(data_row["Date Last Modified"], str)
    assert isinstance(data_row["Date Created"], str)


def test_obtain_submission_lock(db: Session, client: TestClient, logged_in_user):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Should be able to successfully GET this submission and the lock should not be set
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body.get("locked_by") is None

    # Attempt to acquire the lock
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/lock")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["locked_by"]["id"] == str(logged_in_user.id)

    # Verify that the lock is set
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["locked_by"]["id"] == str(logged_in_user.id)


def test_cannot_acquire_lock_on_locked_submission(db: Session, client: TestClient, logged_in_user):
    locking_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=locking_user,
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Attempt to acquire the lock, verify that it fails and reports the current lock holder
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/lock")
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["locked_by"]["id"] == str(locking_user.id)


def test_release_submission_lock(db: Session, client: TestClient, logged_in_user):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=logged_in_user,
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Verify that the lock is set
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["locked_by"]["id"] == str(logged_in_user.id)

    # Release the lock
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/unlock")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    # Verify that the lock is released
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["locked_by"] is None


def test_cannot_release_other_users_submission_lock(
    db: Session, client: TestClient, logged_in_user
):
    locking_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=locking_user,
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Attempt to release the lock, verify that it fails
    response = client.request(method="put", url=f"/api/metadata_submission/{submission.id}/unlock")
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["locked_by"]["id"] == str(locking_user.id)


def test_try_edit_locked_submission(db: Session, client: TestClient, logged_in_user):
    # Locked by a random user at utcnow by default
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=fakes.UserFactory(),
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = SubmissionMetadataSchema.model_validate(submission)
    db.commit()

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload, exclude_unset=True),
    )
    assert response.status_code == 400


def test_try_edit_expired_locked_submission(db: Session, client: TestClient, logged_in_user):
    # initialize test submission with expired lock
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=fakes.UserFactory(),
        lock_updated=datetime.now(tz=UTC) - timedelta(hours=1),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = SubmissionMetadataSchema.model_validate(submission)
    db.commit()

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload, exclude_unset=True),
    )
    assert response.status_code == 200


def test_try_edit_locked_by_current_user_submission(
    db: Session, client: TestClient, logged_in_user
):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=logged_in_user,
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = SubmissionMetadataSchema.model_validate(submission)
    db.commit()

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload, exclude_unset=True),
    )
    assert response.status_code == 200


def test_submission_list_with_roles(db: Session, client: TestClient, logged_in_user):
    user_a = fakes.UserFactory()
    submission_a = fakes.MetadataSubmissionFactory(author=user_a, author_orcid=user_a.orcid)
    fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
    )
    fakes.MetadataSubmissionFactory(author=user_a, author_orcid=user_a.orcid)
    db.commit()
    fakes.SubmissionRoleFactory(
        submission=submission_a,
        submission_id=submission_a.id,
        user_orcid=logged_in_user.orcid,
    )
    db.commit()
    response = client.request(method="get", url="/api/metadata_submission")
    assert response.status_code == 200

    results = response.json()["results"]
    allowed_submission_ids = [result["id"] for result in results]
    expected_ids = [str(submission_a.id)]
    assert all([submission_id in expected_ids for submission_id in allowed_submission_ids])
    assert len(results) == 1


@pytest.mark.parametrize("role,code", [(SubmissionEditorRole.owner, 200), (None, 403)])
def test_get_submission_with_roles(db: Session, client: TestClient, logged_in_user, role, code):
    if role == SubmissionEditorRole.owner:
        submission = fakes.MetadataSubmissionFactory()
        db.commit()
        role = fakes.SubmissionRoleFactory(
            submission=submission, submission_id=submission.id, user_orcid=logged_in_user.orcid
        )
    else:
        submission = fakes.MetadataSubmissionFactory()
    db.commit()
    response = client.request(method="get", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == code


@pytest.mark.parametrize("role,code", [(SubmissionEditorRole.owner, 200), (None, 403)])
def test_edit_submission_with_roles(db: Session, client: TestClient, logged_in_user, role, code):
    if role == SubmissionEditorRole.owner:
        submission = fakes.MetadataSubmissionFactory()
        payload = SubmissionMetadataSchema.model_validate(submission)
        db.commit()
        role = fakes.SubmissionRoleFactory(
            submission=submission,
            submission_id=submission.id,
            user_orcid=logged_in_user.orcid,
        )
    else:
        submission = fakes.MetadataSubmissionFactory()
        payload = SubmissionMetadataSchema.model_validate(submission)
    db.commit()
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload),
    )
    assert response.status_code == code


def test_create_role_on_patch(db: Session, client: TestClient, logged_in_user):
    pi_orcid = fakes.Faker("pystr")
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission, submission_id=submission.id, user_orcid=logged_in_user.orcid
    )
    payload = SubmissionMetadataSchemaPatch(**submission.__dict__)
    db.commit()

    payload.permissions = {str(pi_orcid): SubmissionEditorRole.owner.value}
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload),
    )
    assert response.status_code == 200

    roles = db.query(SubmissionRole)
    assert roles.count() == 2

    role = roles.filter(SubmissionRole.user_orcid == str(pi_orcid)).first()
    assert role is not None
    assert role.user_orcid == str(pi_orcid)
    assert role.submission_id == submission.id
    assert SubmissionEditorRole(role.role) == SubmissionEditorRole.owner


@pytest.mark.parametrize("samples_only,code", [(True, 200), (False, 403)])
def test_piecewise_patch_metadata_contributor(
    db: Session, client: TestClient, logged_in_user, samples_only, code
):
    user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=user, author_orcid=user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.metadata_contributor,
    )
    full_payload = SubmissionMetadataSchemaPatch.model_validate(submission)
    db.commit()

    if samples_only:
        request_dict = {
            "metadata_submission": {"sampleData": full_payload.metadata_submission.sampleData}
        }
        request_payload = jsonable_encoder(
            SubmissionMetadataSchemaPatch.model_validate(request_dict), exclude_unset=True
        )
    else:
        request_payload = jsonable_encoder(full_payload)

    # Logged in user should not be able to submit full payload because it contains non-sample data
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=request_payload,
    )
    assert response.status_code == code


def test_delete_role_on_patch(db: Session, client: TestClient, logged_in_user):
    user_orcid = fakes.Faker("pystr")
    pi_orcid = fakes.Faker("pystr")
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=pi_orcid,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user_orcid,
        role=SubmissionEditorRole.viewer,
    )
    payload = SubmissionMetadataSchemaPatch.model_validate(submission)
    db.commit()

    payload.permissions = {}

    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload),
    )
    assert response.status_code == 200
    roles = db.query(SubmissionRole)
    # logged_in_user's, pi's owner roles should still exist
    assert roles.count() == 2
    assert all([role.role == SubmissionEditorRole.owner for role in roles.all()])


def test_update_role_on_patch(db: Session, client: TestClient, logged_in_user):
    user_orcid = fakes.Faker("pystr")
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user_orcid,
        role=SubmissionEditorRole.viewer,
    )
    payload = SubmissionMetadataSchemaPatch.model_validate(submission)
    db.commit()

    payload.permissions = {str(user_orcid): SubmissionEditorRole.editor.value}
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload),
    )
    assert response.status_code == 200
    roles = db.query(SubmissionRole).filter(SubmissionRole.user_orcid == str(user_orcid))
    assert roles.count() == 1
    role = roles.first()
    assert role and role.role == SubmissionEditorRole.editor


def test_delete_submission_by_owner(db: Session, client: TestClient, logged_in_user):
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Verify that the DELETE request goes through
    response = client.request(method="DELETE", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 204

    # Verify that it's really gone
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 404


def test_delete_submission_by_non_owner(db: Session, client: TestClient, logged_in_user):
    user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=user, author_orcid=user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.metadata_contributor,
    )
    db.commit()

    # Verify that a contributor cannot delete it
    response = client.request(method="DELETE", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 403

    # Verify that it is still there
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200


def test_delete_submission_while_locked(db: Session, client: TestClient, logged_in_user):
    user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=user,
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=user.orcid,
        role=SubmissionEditorRole.metadata_contributor,
    )
    db.commit()

    # Verify that a owner cannot delete while submission is locked
    response = client.request(method="DELETE", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 400

    # Verify that it is still there
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200


def test_sync_submission_templates(db: Session, client: TestClient, logged_in_user):
    template = "foo"
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=logged_in_user,
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = jsonable_encoder(
        SubmissionMetadataSchemaPatch.model_validate(submission), exclude_unset=True
    )
    payload["metadata_submission"]["templates"] = [template]
    db.commit()

    _ = client.request(
        method="PATCH", url=f"/api/metadata_submission/{submission.id}", json=payload
    )
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    assert len(response.json()["templates"]) == 1
    assert response.json()["templates"][0] == template


def test_sync_submission_study_name(db: Session, client: TestClient, logged_in_user):
    expected_val = "my study"
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        locked_by=logged_in_user,
        lock_updated=datetime.now(tz=UTC),
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = jsonable_encoder(
        SubmissionMetadataSchemaPatch.model_validate(submission), exclude_unset=True
    )
    payload["metadata_submission"]["studyForm"]["studyName"] = expected_val
    db.commit()

    _ = client.request(
        method="PATCH", url=f"/api/metadata_submission/{submission.id}", json=payload
    )
    response = client.request(method="GET", url=f"/api/metadata_submission/{submission.id}")
    assert response.status_code == 200
    assert response.json()["study_name"] == expected_val


def test_metadata_suggest(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST", url="/api/metadata_submission/suggest", json=suggest_payload
    )
    assert response.status_code == 200
    assert response.json() == [
        {"type": "add", "row": 1, "slot": "elev", "value": "16", "current_value": None},
        {"type": "replace", "row": 3, "slot": "elev", "value": "16", "current_value": "0"},
    ]


def test_metadata_suggest_single_type(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST",
        url="/api/metadata_submission/suggest?types=add",
        json=suggest_payload,
    )
    assert response.status_code == 200
    assert response.json() == [
        {"type": "add", "row": 1, "slot": "elev", "value": "16", "current_value": None},
    ]


def test_metadata_suggest_multiple_types(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST",
        url="/api/metadata_submission/suggest?types=add&types=replace",
        json=suggest_payload,
    )
    assert response.status_code == 200
    assert response.json() == [
        {"type": "add", "row": 1, "slot": "elev", "value": "16", "current_value": None},
        {"type": "replace", "row": 3, "slot": "elev", "value": "16", "current_value": "0"},
    ]


def test_metadata_suggest_invalid_type(client: TestClient, suggest_payload, logged_in_user):
    response = client.request(
        method="POST",
        url="/api/metadata_submission/suggest?types=whatever",
        json=suggest_payload,
    )
    assert response.status_code == 422


def test_set_submission_pi_image_success(db: Session, client: TestClient, logged_in_user):
    """Test successfully setting a PI image for a submission."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    upload_data = {
        "object_name": "test-pi-image.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/pi_image", json=upload_data
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("pi_image_url") is not None

    # Verify the image was set in the database
    db.refresh(submission)
    assert submission.pi_image is not None
    assert submission.pi_image.name == "test-pi-image.jpg"
    assert submission.pi_image.size == 1000000
    assert submission.pi_image.content_type == "image/jpeg"


def test_set_submission_primary_study_image_success(
    db: Session, client: TestClient, logged_in_user
):
    """Test successfully setting a primary study image for a submission."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    upload_data = {
        "object_name": "test-primary-study-image.png",
        "file_size": 2000000,
        "content_type": "image/png",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/primary_study_image", json=upload_data
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("primary_study_image_url") is not None

    # Verify the image was set in the database
    db.refresh(submission)
    assert submission.primary_study_image is not None
    assert submission.primary_study_image.name == "test-primary-study-image.png"
    assert submission.primary_study_image.size == 2000000
    assert submission.primary_study_image.content_type == "image/png"


def test_set_submission_study_images_success(db: Session, client: TestClient, logged_in_user):
    """Test successfully adding images to the study_images collection."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Add first image to study_images
    upload_data_1 = {
        "object_name": "study-image-1.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/study_images", json=upload_data_1
    )

    assert response.status_code == 200
    body = response.json()
    study_image_urls = body.get("study_image_urls")
    assert study_image_urls is not None
    assert len(study_image_urls) == 1

    db.refresh(submission)
    assert len(submission.study_images) == 1
    assert submission.study_images[0].name == "study-image-1.jpg"

    # Add second image to study_images
    upload_data_2 = {
        "object_name": "study-image-2.png",
        "file_size": 2048000,
        "content_type": "image/png",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/study_images", json=upload_data_2
    )

    assert response.status_code == 200
    body = response.json()
    study_image_urls = body.get("study_image_urls")
    assert study_image_urls is not None
    assert len(study_image_urls) == 2

    db.refresh(submission)
    assert len(submission.study_images) == 2

    # Verify both images are in the collection
    image_names = [img.name for img in submission.study_images]
    assert "study-image-1.jpg" in image_names
    assert "study-image-2.png" in image_names


def test_set_submission_image_replaces_existing_single_image(
    db: Session, client: TestClient, logged_in_user, temp_storage_object
):
    """Test that setting a single image type replaces the existing image."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )

    # Add initial PI image
    original_image = SubmissionImagesObject(
        name="original-pi-image.jpg", size=500000, content_type="image/jpeg"
    )
    submission.pi_image = original_image
    db.commit()
    original_blob = temp_storage_object(BucketName.SUBMISSION_IMAGES, original_image.name)
    assert original_blob.exists() is True

    # Set new PI image - should replace the original
    upload_data = {
        "object_name": "new-pi-image.png",
        "file_size": 1000000,
        "content_type": "image/png",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/pi_image", json=upload_data
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("pi_image_url") is not None

    # Verify the new image replaced the old one in the database
    db.refresh(submission)
    assert submission.pi_image.name == "new-pi-image.png"
    assert submission.pi_image.size == 1000000
    assert submission.pi_image.content_type == "image/png"

    # Verify the original image was deleted from storage
    assert original_blob.exists() is False


def test_set_submission_image_unauthorized_user(db: Session, client: TestClient, logged_in_user):
    """Test that unauthorized users cannot set submission images."""
    # Create submission owned by a different user
    other_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=other_user, author_orcid=other_user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=other_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    upload_data = {
        "object_name": "unauthorized-image.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/pi_image", json=upload_data
    )

    assert response.status_code == 403


def test_set_submission_image_viewer_role_unauthorized(
    db: Session, client: TestClient, logged_in_user
):
    """Test that users with viewer role cannot set submission images."""
    other_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=other_user, author_orcid=other_user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=other_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    # Give logged in user viewer access
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.viewer,
    )
    db.commit()

    upload_data = {
        "object_name": "viewer-image.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/pi_image", json=upload_data
    )

    assert response.status_code == 403


def test_set_submission_image_editor_role_authorized(
    db: Session, client: TestClient, logged_in_user
):
    """Test that users with editor role can set submission images."""
    other_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=other_user, author_orcid=other_user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=other_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    # Give logged in user editor access
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.editor,
    )
    db.commit()

    upload_data = {
        "object_name": "editor-image.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/pi_image", json=upload_data
    )

    assert response.status_code == 200


def test_set_submission_image_admin_role_authorized(
    db: Session, client: TestClient, logged_in_admin_user
):
    """Test that users with admin role can set submission images."""
    other_user = fakes.UserFactory()
    submission = fakes.MetadataSubmissionFactory(author=other_user, author_orcid=other_user.orcid)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=other_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    upload_data = {
        "object_name": "admin-image.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/pi_image", json=upload_data
    )

    assert response.status_code == 200


def test_set_submission_image_nonexistent_submission(
    db: Session, client: TestClient, logged_in_user
):
    """Test setting image for a nonexistent submission returns 404."""
    upload_data = {
        "object_name": "test-image.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    # This is a random UUID that does not correspond to any submission
    response = client.post(
        "/api/metadata_submission/cdfc2184-d389-433e-b1ac-f709f8364557/image/pi_image",
        json=upload_data,
    )

    assert response.status_code == 404


def test_set_submission_image_invalid_image_type(db: Session, client: TestClient, logged_in_user):
    """Test setting image with invalid image type returns 422."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    upload_data = {
        "object_name": "test-image.jpg",
        "file_size": 1000000,
        "content_type": "image/jpeg",
    }

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/invalid_type", json=upload_data
    )

    assert response.status_code == 422


def test_set_submission_image_missing_required_fields(
    db: Session, client: TestClient, logged_in_user
):
    """Test setting image with missing required fields returns 422."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Missing object_name field
    incomplete_data = {"file_size": 1000000, "content_type": "image/jpeg"}

    response = client.post(
        f"/api/metadata_submission/{submission.id}/image/pi_image", json=incomplete_data
    )

    assert response.status_code == 422


def test_delete_submission_pi_image_success(
    db: Session, client: TestClient, logged_in_user, temp_storage_object
):
    """Test successfully deleting a PI image from a submission."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Add a PI image to delete
    pi_image = SubmissionImagesObject(
        name="pi-image-to-delete.jpg", size=500000, content_type="image/jpeg"
    )
    submission.pi_image = pi_image
    db.commit()

    # Verify the image exists in storage
    blob = temp_storage_object(BucketName.SUBMISSION_IMAGES, pi_image.name)
    assert blob.exists() is True

    # Delete the PI image
    response = client.delete(f"/api/metadata_submission/{submission.id}/image/pi_image")
    assert response.status_code == 204

    # Verify the image was deleted from the database
    db.refresh(submission)
    assert submission.pi_image is None

    # Verify the image was deleted from storage
    assert blob.exists() is False  # type: ignore


def test_delete_submission_primary_study_image_success(
    db: Session, client: TestClient, logged_in_user, temp_storage_object
):
    """Test successfully deleting a primary study image from a submission."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Add a primary study image to delete
    primary_study_image = SubmissionImagesObject(
        name="primary-study-image-to-delete.png", size=600000, content_type="image/png"
    )
    submission.primary_study_image = primary_study_image
    db.commit()

    # Verify the image exists in storage
    blob = temp_storage_object(BucketName.SUBMISSION_IMAGES, primary_study_image.name)
    assert blob.exists() is True

    # Delete the primary study image
    response = client.delete(f"/api/metadata_submission/{submission.id}/image/primary_study_image")
    assert response.status_code == 204

    # Verify the image was deleted from the database
    db.refresh(submission)
    assert submission.primary_study_image is None

    # Verify the image was deleted from storage
    assert blob.exists() is False  # type: ignore


def test_delete_submission_study_images_success(
    db: Session, client: TestClient, logged_in_user, temp_storage_object
):
    """Test successfully deleting a study image from a submission."""
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user, author_orcid=logged_in_user.orcid
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Add a study image to delete
    image_to_delete = SubmissionImagesObject(
        name="study-image-to-delete.jpg", size=700000, content_type="image/jpeg"
    )
    submission.study_images.append(image_to_delete)
    other_image = SubmissionImagesObject(
        name="other-study-image.jpg", size=800000, content_type="image/jpeg"
    )
    submission.study_images.append(other_image)
    db.commit()

    # Verify the image exists in storage
    blob_to_delete = temp_storage_object(BucketName.SUBMISSION_IMAGES, image_to_delete.name)
    other_blob = temp_storage_object(BucketName.SUBMISSION_IMAGES, other_image.name)
    assert blob_to_delete.exists() is True
    assert other_blob.exists() is True

    # Delete the study image
    response = client.delete(
        f"/api/metadata_submission/{submission.id}/image/study_images"
        f"?image_name={image_to_delete.name}"
    )
    assert response.status_code == 204

    # Verify the image was deleted from the database
    db.refresh(submission)
    assert len(submission.study_images) == 1

    # Verify the image was deleted from storage
    assert blob_to_delete.exists() is False
    assert other_blob.exists() is True


@pytest.mark.parametrize(
    "test_status,code",
    [
        (SubmissionStatusEnum.InProgress.text, 200),
        (SubmissionStatusEnum.SubmittedPendingReview.text, 403),
    ],
)
def test_edit_submission_status_uneditable(
    db: Session, client: TestClient, logged_in_user, test_status, code
):
    """Test that a submission with an uneditable status (anything other than InProgress or UpdatesRequired) errors"""
    submission = fakes.MetadataSubmissionFactory(status=test_status)
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    payload = SubmissionMetadataSchema.model_validate(submission)
    db.commit()
    response = client.request(
        method="patch",
        url=f"/api/metadata_submission/{submission.id}",
        json=jsonable_encoder(payload),
    )
    assert response.status_code == code


def test_github_issue_resubmission_creates_comment_only(
    db: Session, client: TestClient, logged_in_user
):
    """
    Confirm that when a submission status becomes 'SubmittedPendingReview',
    the Github API searches for an existing issue with the same ID and either
    creates one if it doesn't exist or adds a comment if it does
    """

    # Create a submission
    submission = fakes.MetadataSubmissionFactory(
        author=logged_in_user,
        author_orcid=logged_in_user.orcid,
        status=SubmissionStatusEnum.InProgress.text,
        is_test_submission=False,
    )
    fakes.SubmissionRoleFactory(
        submission=submission,
        submission_id=submission.id,
        user_orcid=logged_in_user.orcid,
        role=SubmissionEditorRole.owner,
    )
    db.commit()

    # Mock the existing GitHub issue that would be found
    existing_issue = {
        "number": 123,
        "url": "https://api.github.com/repos/owner/repo/issues/123",
        "html_url": "https://github.com/owner/repo/issues/123",
        "title": f"NMDC Submission: {submission.id}",
        "state": "open",
    }

    # Fake response from github API call searching for the existing issue
    search_response = Mock()
    search_response.status_code = 200
    search_response.json.return_value = [existing_issue]

    # Fake response from github API call making a comment on existing issue
    comment_response = Mock()
    comment_response.status_code = 201
    comment_response.json.return_value = {"id": 456, "body": "comment content"}

    # Patch the normal API settings as well as
    # search(requests.get) and comment (requests.post) API calls
    # with their mock versions defined below
    with patch("nmdc_server.api.requests.get") as mock_get, patch(
        "nmdc_server.api.requests.post"
    ) as mock_post, patch("nmdc_server.api.settings") as mock_settings:

        # Configure fake github settings
        mock_settings.github_issue_url = "https://api.github.com/repos/owner/repo/issues"
        mock_settings.github_authentication_token = "fake_token"
        mock_settings.github_issue_assignee = "assignee"
        mock_settings.host = "test-host"

        # Set fake responses for search and comment API calls
        mock_get.return_value = search_response
        mock_post.return_value = comment_response

        # Update submission status to trigger GitHub issue creation/update
        payload = {
            "status": SubmissionStatusEnum.SubmittedPendingReview.text,
            "metadata_submission": {},
        }
        response = client.request(
            method="PATCH",
            url=f"/api/metadata_submission/{submission.id}",
            json=payload,
        )
        assert response.status_code == 200

        # Verify that the mock version of requests.get was used to search existing issues once
        assert mock_get.call_count == 1
        get_call = mock_get.call_args
        assert "https://api.github.com/repos/owner/repo/issues" in get_call[0][0]

        # Verify that the mock version of request.post was used to create a comment once (not a new issue)
        assert mock_post.call_count == 1
        post_call = mock_post.call_args
        assert post_call[0][0] == "https://api.github.com/repos/owner/repo/issues/123/comments"

        # Verify the mocked comment includes resubmission information
        comment_data = json.loads(post_call[1]["data"])
        assert "Submission Resubmitted" in comment_data["body"]
        assert logged_in_user.name in comment_data["body"]
        assert logged_in_user.orcid in comment_data["body"]
        assert SubmissionStatusEnum.SubmittedPendingReview.text in comment_data["body"]
