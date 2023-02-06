import json
from contextlib import contextmanager
import requests

@contextmanager
def print_status(message):
    print(f"{message}... ", end="")
    try:
        yield
    except Exception as e:
        print("FAILED")
        raise e
    else:
        print("done")

REPO = "microbiomedata/sheets_and_friends"
REVISION_ID = "4c83c3696d686cf5878db40a71e296faed1a4b2c"
REMOTE_PATH = "artifacts/nmdc_submission_schema.json"

LOCAL_PATH = "web/src/views/SubmissionPortal/schema.json"

url = f"https://raw.githubusercontent.com/{REPO}/{REVISION_ID}/{REMOTE_PATH}"

with print_status("Fetching schema from GitHub"):
    response = requests.get(url)
    response.raise_for_status()
    body = response.json()

with print_status("Removing unnecessary schema elements"):
    for class_def in body["classes"].values():
        # slot_usage is not needed since all class-induced slots should
        # already be materialized as attributes
        if "slot_usage" in class_def:
            del class_def["slot_usage"]

        for attr_def in class_def.get("attributes", {}).values():
            # domain_of is not used and because of an upstream bug can
            # contain a long list with lots of duplication
            del attr_def["domain_of"]

with print_status(f"Writing schema to {LOCAL_PATH}"):
    with open(LOCAL_PATH, "w") as out_file:
        json.dump(body, out_file, indent=2)
