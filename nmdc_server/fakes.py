from collections import OrderedDict
from datetime import UTC, datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from factory import Faker, SubFactory, lazy_attribute, post_generation
from factory.alchemy import SQLAlchemyModelFactory
from faker.providers import BaseProvider, date_time, geo, internet, lorem, misc, person, python
from sqlalchemy.orm.scoping import scoped_session

from nmdc_server import models
from nmdc_server.database import SessionLocal
from nmdc_server.schemas import AnnotationValue


class DoiProvider(BaseProvider):
    def doi(self):
        num = self.random_int(min=1000, max=999999999)
        post_size = self.random_int(min=1, max=10)
        post = self.bothify("?" * post_size).lower()
        return f"10.{num}/{post}"

    def uuid(self):
        return uuid4()


class EnumProvider(BaseProvider):
    def enum_value(self, enum_class):
        enum_values = list(enum_class)
        return self.random_element(enum_values)


db = scoped_session(SessionLocal)
Faker.add_provider(DoiProvider)
Faker.add_provider(date_time)
Faker.add_provider(geo)
Faker.add_provider(internet)
Faker.add_provider(lorem)
Faker.add_provider(misc)
Faker.add_provider(person)
Faker.add_provider(python)
Faker.add_provider(EnumProvider)


class DOIInfoFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.DOIInfo
        sqlalchemy_session = db

    id = Faker("doi")
    info = Faker("pydict", value_types=["str"])
    doi_type = Faker("enum_value", enum_class=models.DOIType)


class AnnotatedFactory(SQLAlchemyModelFactory):
    id: str = Faker("pystr")
    name: str = Faker("word")
    description: str = Faker("sentence")

    alternate_identifiers = Faker("pylist", nb_elements=2, value_types=[str])
    annotations: Dict[str, AnnotationValue] = Faker(
        "pydict", value_types=["int", "float", "date_time", "str"]
    )


class WebsiteFactory(SQLAlchemyModelFactory):
    id = Faker("uuid")
    url = Faker("uri")

    class Meta:
        model = models.Website
        sqlalchemy_session = db


class EnvoTermFactory(SQLAlchemyModelFactory):
    id = Faker("pystr")
    label = Faker("word")
    data = Faker("pydict", value_types=["str"])

    class Meta:
        model = models.EnvoTerm
        sqlalchemy_session = db

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        term = models.EnvoTerm(*args, **kwargs)
        db.add(models.EnvoAncestor(term=term, ancestor=term, direct=False))
        return term


class EnvoAncestorFactory(SQLAlchemyModelFactory):
    term = SubFactory(EnvoTermFactory)
    ancestor = SubFactory(EnvoTermFactory)
    direct = Faker("random_element", elements=OrderedDict([(True, 0.1), (False, 0.9)]))

    class Meta:
        model = models.EnvoAncestor
        sqlalchemy_session = db


class PrincipalInvestigator(SQLAlchemyModelFactory):
    id = Faker("uuid")
    name = Faker("name")
    image = Faker("binary", length=64)

    class Meta:
        model = models.PrincipalInvestigator
        sqlalchemy_session = db


class StudyFactory(AnnotatedFactory):
    add_date = Faker("date_time")
    mod_date = Faker("date_time")
    gold_name = Faker("word")
    gold_description = Faker("sentence")
    scientific_objective = Faker("sentence")
    principal_investigator = SubFactory(PrincipalInvestigator)
    image = Faker("binary", length=64)
    dois: List[models.DOIInfo] = []

    class Meta:
        model = models.Study
        sqlalchemy_session = db

    @post_generation
    def principal_investigator_websites(self, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            extracted = [StudyWebsiteFactory(), StudyWebsiteFactory()]

        for website in extracted:
            self.principal_investigator_websites.append(website)


class StudyWebsiteFactory(SQLAlchemyModelFactory):
    website = SubFactory(WebsiteFactory)

    class Meta:
        model = models.StudyWebsite
        sqlalchemy_session = db


class BiosampleFactory(AnnotatedFactory):
    class Meta:
        model = models.Biosample
        sqlalchemy_session = db

    add_date = Faker("date_time")
    mod_date = Faker("date_time")
    collection_date = Faker("date_time")
    depth = Faker("random_number", digits=3)
    env_broad_scale = SubFactory(EnvoTermFactory)
    env_local_scale = SubFactory(EnvoTermFactory)
    env_medium = SubFactory(EnvoTermFactory)
    latitude = Faker("latitude")
    longitude = Faker("longitude")
    study = SubFactory(StudyFactory)
    ecosystem = Faker("word")
    ecosystem_category = Faker("word")
    ecosystem_type = Faker("word")
    ecosystem_subtype = Faker("word")
    specific_ecosystem = Faker("word")


class OmicsProcessingFactory(AnnotatedFactory):
    class Meta:
        model = models.OmicsProcessing
        sqlalchemy_session = db

    add_date = Faker("date_time")
    mod_date = Faker("date_time")
    biosample_inputs: List[models.Biosample] = []

    @lazy_attribute
    def study(self):
        if not self.biosample_inputs:
            return None
        return self.biosample_inputs[0].study


class DataObjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.DataObject
        sqlalchemy_session = db

    id: str = Faker("pystr")
    name: str = Faker("word")
    description: str = Faker("sentence")
    file_type: str = Faker("word")
    file_size_bytes = Faker("pyint")
    md5_checksum = Faker("md5", raw_output=False)
    omics_processing = SubFactory(OmicsProcessingFactory)
    workflow_type: Optional[str] = None


class PipelineStepBase(SQLAlchemyModelFactory):
    id: str = Faker("pystr")
    name: str = Faker("word")
    type: str = Faker("word")
    git_url: str = Faker("uri")
    started_at_time: datetime = Faker("date_time")
    ended_at_time: datetime = Faker("date_time")
    execution_resource: str = Faker("word")
    omics_processing: models.OmicsProcessing = SubFactory(OmicsProcessingFactory)


class ReadsQCFactory(PipelineStepBase):
    class Meta:
        model = models.ReadsQC
        sqlalchemy_session = db

    input_read_count: int = Faker("pyint")
    input_read_bases: int = Faker("pyint")
    output_read_count: int = Faker("pyint")
    output_read_bases: int = Faker("pyint")


class MetagenomeAssemblyFactory(PipelineStepBase):
    class Meta:
        model = models.MetagenomeAssembly
        sqlalchemy_session = db

    scaffolds: float = Faker("pyfloat")
    contigs: float = Faker("pyfloat")
    scaf_bp: float = Faker("pyfloat")
    contig_bp: float = Faker("pyfloat")
    scaf_n50: float = Faker("pyfloat")
    scaf_l50: float = Faker("pyfloat")
    ctg_n50: float = Faker("pyfloat")
    ctg_l50: float = Faker("pyfloat")
    scaf_n90: float = Faker("pyfloat")
    scaf_l90: float = Faker("pyfloat")
    ctg_n90: float = Faker("pyfloat")
    ctg_l90: float = Faker("pyfloat")
    scaf_max: float = Faker("pyfloat")
    ctg_max: float = Faker("pyfloat")
    scaf_n_gt50k: float = Faker("pyfloat")
    scaf_l_gt50k: float = Faker("pyfloat")
    scaf_pct_gt50k: float = Faker("pyfloat")
    num_input_reads: float = Faker("pyfloat")
    num_aligned_reads: float = Faker("pyfloat")
    scaf_logsum: float = Faker("pyfloat")
    scaf_powsum: float = Faker("pyfloat")
    ctg_logsum: float = Faker("pyfloat")
    ctg_powsum: float = Faker("pyfloat")
    asm_score: float = Faker("pyfloat")
    gap_pct: float = Faker("pyfloat")
    gc_avg: float = Faker("pyfloat")
    gc_std: float = Faker("pyfloat")


class MetagenomeAnnotationFactory(PipelineStepBase):
    class Meta:
        model = models.MetagenomeAnnotation
        sqlalchemy_session = db


class MetaproteomicAnalysisFactory(PipelineStepBase):
    class Meta:
        model = models.MetaproteomicAnalysis
        sqlalchemy_session = db


class MAGsAnalysisFactory(PipelineStepBase):
    class Meta:
        model = models.MAGsAnalysis
        sqlalchemy_session = db

    input_contig_num: int = Faker("pyint")
    too_short_contig_num: int = Faker("pyint")
    low_depth_contig_num: int = Faker("pyint")
    unbinned_contig_num: int = Faker("pyint")
    binned_contig_num: int = Faker("pyint")


class MAGFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.MAG
        sqlalchemy_session = db

    bin_name: str = Faker("word")
    number_of_contig: int = Faker("pyint")
    completeness: float = Faker("pyfloat")
    contamination: float = Faker("pyfloat")
    gene_count: int = Faker("pyint")
    bin_quality: str = Faker("word")
    num_16s: int = Faker("pyint")
    num_5s: int = Faker("pyint")
    num_23s: int = Faker("pyint")
    num_t_rna: int = Faker("pyint")

    mags_analysis = SubFactory(MAGsAnalysisFactory)


class NOMAnalysisFactory(PipelineStepBase):
    class Meta:
        model = models.NOMAnalysis
        sqlalchemy_session = db


class ReadBasedAnalysisFactory(PipelineStepBase):
    class Meta:
        model = models.ReadBasedAnalysis
        sqlalchemy_session = db


class MetabolomicsAnalysisFactory(PipelineStepBase):
    class Meta:
        model = models.MetabolomicsAnalysis
        sqlalchemy_session = db


class GeneFunction(SQLAlchemyModelFactory):
    class Meta:
        model = models.GeneFunction
        sqlalchemy_session = db

    id: str = Faker("pystr")


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.User
        sqlalchemy_session = db

    id: UUID = Faker("uuid")
    name: str = Faker("name")
    orcid: str = Faker("pystr")
    is_admin: bool = False


class MetadataSubmissionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.SubmissionMetadata
        sqlalchemy_session = db

    id: UUID = Faker("uuid")
    author = SubFactory(UserFactory)
    author_orcid = Faker("pystr")
    status = "In Progress"
    study_name = Faker("word")
    templates = Faker("pylist", nb_elements=2, value_types=[str])
    created = datetime.now(tz=UTC)
    date_last_modified = created
    # TODO specify all fields!
    metadata_submission = {
        "sampleData": {},
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
            "studyName": "",
            "piName": "",
            "piEmail": "",
            "piOrcid": "",
            "linkOutWebpage": [],
            "fundingSources": [],
            "dataDois": [],
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
    }
    locked_by = None
    lock_updated = None
    is_test_submission = False


class SubmissionRoleFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.SubmissionRole
        sqlalchemy_session = db

    submission_id: UUID = Faker("uuid")
    user_orcid: str = Faker("pystr")
    role: models.SubmissionEditorRole = models.SubmissionEditorRole.owner
    submission = SubFactory(MetadataSubmissionFactory)
