import importlib.resources
import json
import shutil
from importlib.metadata import version
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

    out_dir = directory / "submission_schema"
    submission_schema_json_path = out_dir / "submission_schema.json"

    if submission_schema_json_path.exists():
        # If the submission schema JSON file already exists, check its version and see
        # if it needs to be updated.
        with open(submission_schema_json_path, "r") as f:
            existing_schema = json.load(f)
        if existing_schema.get("version") == version("nmdc-submission-schema"):
            return

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

    # The entire submission schema in JSON format
    out_dir.mkdir(exist_ok=True)
    json_dumper.dump(sv.schema, submission_schema_json_path)

    # The GOLD ecosystem tree that the submission schema re-exports
    gold_tree_path = submission_schema_files / "project/thirdparty/GoldEcosystemTree.json"
    shutil.copyfile(str(gold_tree_path), out_dir / "GoldEcosystemTree.json")
