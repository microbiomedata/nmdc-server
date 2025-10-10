import importlib.resources
import shutil
from pathlib import Path

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import json_dumper

static_path = Path("static")


def initialize_static_directory(*, remove_existing=False) -> Path:
    if remove_existing:
        # Delete existing contents of the static directory,
        # but keep the directory itself, since it may already
        # be mounted by the FastAPI app.
        try:
            for child in static_path.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        except FileNotFoundError:
            pass
    static_path.mkdir(parents=True, exist_ok=True)
    return static_path


def generate_submission_schema_files(directory: Path) -> None:
    """Copy artifacts from nmdc_submission_schema package to the static directory."""
    submission_schema_files = importlib.resources.files("nmdc_submission_schema")

    out_dir = directory / "submission_schema"
    out_dir.mkdir(exist_ok=True)

    # The schema itself in JSON format
    schema_path = submission_schema_files / "project/json/nmdc_submission_schema.json"
    shutil.copyfile(str(schema_path), out_dir / "submission_schema.json")

    # The GOLD ecosystem tree that the submission schema re-exports
    gold_tree_path = submission_schema_files / "project/thirdparty/GoldEcosystemTree.json"
    shutil.copyfile(str(gold_tree_path), out_dir / "GoldEcosystemTree.json")
