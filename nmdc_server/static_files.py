import importlib.resources
import shutil
from pathlib import Path

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import json_dumper


def initialize_static_directory(*, remove_existing=False) -> Path:
    static_path = Path("static")
    if remove_existing:
        try:
            shutil.rmtree(static_path)
        except FileNotFoundError:
            pass
    static_path.mkdir(parents=True, exist_ok=True)
    return static_path


def generate_submission_schema_files(directory: Path) -> None:
    submission_schema_files = importlib.resources.files("nmdc_submission_schema")

    # Load each class in the submission schema, ensure that each slot of the class
    # is fully materialized into attributes, and then drop the slot usage definitions
    # to save some bytes.
    schema_path = submission_schema_files / "schema/nmdc_submission_schema.yaml"
    sv = SchemaView(str(schema_path))
    for class_name, class_definition in sv.all_classes().items():
        for slot_definition in sv.class_induced_slots(class_name):
            class_definition.attributes[slot_definition.name] = slot_definition
    sv.materialize_patterns()
    for class_definition in sv.all_classes().values():
        class_definition.slot_usage = None

    out_dir = directory / "submission_schema"
    out_dir.mkdir(exist_ok=True)

    # The entire submission schema in JSON format
    json_dumper.dump(sv.schema, out_dir / "submission_schema.json")

    # The GOLD ecosystem tree that the submission schema re-exports
    gold_tree_path = submission_schema_files / "project/thirdparty/GoldEcosystemTree.json"
    shutil.copyfile(str(gold_tree_path), out_dir / "GoldEcosystemTree.json")
