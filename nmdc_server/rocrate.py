import json
from datetime import datetime

# Base RO-Crate structure with placeholders for dynamic content
# This gets included in bulk downloads as ro-crate-metadata.json
# See https://www.researchobject.org/ro-crate/specification/1.2/introduction.html
ROCRATE_BULK_DOWNLOAD_BASE = {
    "@context": "https://w3id.org/ro/crate/1.2/context",
    "@graph": [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
            "about": {"@id": "./"}
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": "NMDC Bulk Download Data Bundle",
            "datePublished": datetime.now().isoformat(),
            "hasPart": [
                {"@id": "README.md"},
                {"@id": "metadata/"},
                {"@id": "metadata/related_biosamples.json"},
                {"@id": "metadata/data_objects.json"},
                {"@id": "data/"}
            ]
        },
        {
            "@id": "README.md",
            "@type": "File",
            "description": "Human-readable summary of the bulk download."
        },
        {
            "@id": "metadata/",
            "@type": "Dataset",
            "name": "Metadata Directory",
            "description": "Mapping and relationship files for the bulk download.",
            "hasPart": [
                {"@id": "metadata/related_biosamples.json"},
                {"@id": "metadata/data_objects.json"}
            ]
        },
        {
            "@id": "metadata/related_biosamples.json",
            "@type": "File",
            "name": "Related Entities Mapping",
            "description": "JSON file linking bulk files to external research entities."
        },
        {
            "@id": "metadata/data_objects.json",
            "@type": "File",
            "name": "Object Definitions",
            "description": "Schema definitions for the objects contained in the dataset."
        },
        {
            "@id": "data/",
            "@type": "Dataset",
            "name": "Data Directory",
            "description": "...",
        },
    ]
}


def generate_rocrate_for_bulk_download(bulk_download):
    """Generates an RO-Crate metadata object for a given bulk download record."""
    rocrate_object = json.loads(json.dumps(ROCRATE_BULK_DOWNLOAD_BASE))
    root = next((item for item in rocrate_object["@graph"] if item["@id"] == "./"), None)
    root["name"] = bulk_download.title
    root["description"] = bulk_download.description

    return rocrate_object
