from sqlalchemy.orm import Session

from nmdc_server import crud, models
from tests import fakes


def test_bulk_archive_path_lookup_uses_scalar_association_rows(db: Session):
    data_generation = fakes.OmicsProcessingFactory(
        id="nmdc:dgns-1",
        poolable_replicates_manifest_id="nmdc:manifest-1",
    )
    second_data_generation = fakes.OmicsProcessingFactory(
        id="nmdc:dgns-2",
        poolable_replicates_manifest_id="nmdc:manifest-1",
    )
    raw_data_object = fakes.DataObjectFactory(
        id="nmdc:dobj-raw",
        name="reads.fastq.gz",
        omics_processing=data_generation,
    )
    workflow_data_object = fakes.DataObjectFactory(
        id="nmdc:dobj-1",
        name="assembly.fna",
        omics_processing=None,
    )
    data_generation.outputs.extend([raw_data_object, workflow_data_object])
    second_data_generation.outputs.append(workflow_data_object)
    fakes.MetagenomeAssemblyFactory(
        id="nmdc:wfmgas-1",
        outputs=[workflow_data_object],
        was_informed_by=[data_generation],
    )
    db.flush()

    lookup = crud.get_bulk_archive_path_lookup(db, [raw_data_object, workflow_data_object])

    assert lookup.paths_by_data_object_id == {
        "nmdc:dobj-raw": "nmdc_manifest-1/reads.fastq.gz",
        "nmdc:dobj-1": "nmdc_manifest-1/nmdc_wfmgas-1/assembly.fna",
    }
    # The broad output association to dgns-2 must not be mistaken for either a
    # direct source or a workflow's informing DataGeneration.
    assert lookup.data_generation_ids == ["nmdc:dgns-1"]
    assert lookup.workflow_ids_by_data_generation_id == {"nmdc:dgns-1": ["nmdc:wfmgas-1"]}
