from nmdc_server import crud, models


def test_construct_zip_file_path_uses_data_generation_and_workflow_names():
    data_generation = models.OmicsProcessing(
        id="nmdc:dgns-1",
        name="Data/Generation",
    )
    data_object = models.DataObject(
        id="nmdc:dobj-1",
        name="reads.fastq.gz",
    )
    workflow_activity = models.ReadsQC(
        id="nmdc:wfrqc-1",
        name="Reads:QC",
    )
    data_generation.outputs.append(data_object)
    data_generation.reads_qc.append(workflow_activity)
    workflow_activity.outputs.append(data_object)

    assert crud.construct_zip_file_path(data_object) == "Data_Generation/Reads_QC/reads.fastq.gz"
