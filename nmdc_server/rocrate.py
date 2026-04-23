from datetime import datetime


def get_rocrate_base_bulk_download():
    """
    Base RO-Crate structure with placeholders for dynamic content.
    This gets included in bulk downloads as ro-crate-metadata.json.
    See https://www.researchobject.org/ro-crate/specification/1.2/introduction.html
    """
    return {
        "@context": "https://w3id.org/ro/crate/1.2/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "NMDC Data Portal Bulk Download",
                "description": "autogenerate-me",
                "datePublished": "2026",
                "additionalProperty": [
                    {
                        "@type": "PropertyValue",
                        "name": "query_conditions",
                        "value": ["autogenerate-me"],
                    },
                    {
                        "@type": "PropertyValue",
                        "name": "selected_file_types",
                        "value": ["autogenerate-me"],
                    },
                ],
                "hasPart": [
                    {"@id": "README.md"},
                    {"@id": "metadata/"},
                    {"@id": "metadata/related_biosamples.json"},
                    {"@id": "metadata/data_objects.json"},
                    {"@id": "data/"},
                ],
            },
            {
                "@id": "README.md",
                "@type": "File",
                "description": "Human-readable summary of how to navigate this bulk download.",
            },
            {
                "@id": "metadata/",
                "@type": "Dataset",
                "name": "Metadata Directory",
                "description": "Metadata files that associate the data files in this bulk download with other NMDC research entities.",
                "hasPart": [
                    {"@id": "metadata/related_biosamples.json"},
                    {"@id": "metadata/data_objects.json"},
                ],
            },
            {
                "@id": "metadata/related_biosamples.json",
                "@type": "File",
                "name": "Related Biosamples Mapping",
                "description": "A single JSON object whose keys are each of the `DataObject` IDs included in your download. For each `DataObject` ID, there is a list of `Biosample` IDs that are associated with that `DataObject`.",
            },
            {
                "@id": "metadata/data_objects.json",
                "@type": "File",
                "name": "Data Object Metadata",
                "description": "A JSON array where each element represents the metadata for a single `DataObject` included in your download. Each file name in your data directory is prefixed with its corresponding `DataObject` ID which correlates to the IDs in this file.",
            },
            {
                "@id": "data/",
                "@type": "Dataset",
                "name": "Data Directory",
                "description": "autogenerate-me",
            },
        ],
    }


def get_root_data_entity(rocrate_dict):
    """Helper function to extract the root data entity from the RO-Crate dictionary."""
    return next((item for item in rocrate_dict["@graph"] if item["@id"] == "./"), None)


def generate_rocrate_for_bulk_download(bulk_download):
    """Generates an RO-Crate metadata object for a given bulk download record."""
    rocrate_dict = get_rocrate_base_bulk_download()
    root_data_entity = get_root_data_entity(rocrate_dict)
    if not root_data_entity:
        raise ValueError("RO-Crate structure is missing the root data entity with @id './'")
    root_data_entity["description"] = (
        f"Bulk download of data files from the NMDC Data Portal, generated on {datetime.now().strftime("%Y-%m-%d")} at {datetime.now().strftime("%H:%M")}. The files included in the data directory are determined by the `query_conditions` and `selected_file_types` specified for this bulk download."
    )
    query_conditions_property = next(
        (
            prop
            for prop in root_data_entity["additionalProperty"]
            if prop["name"] == "query_conditions"
        ),
        None,
    )
    if not query_conditions_property:
        raise ValueError("RO-Crate structure is missing the 'query_conditions' additional property")
    query_conditions_property["value"] = bulk_download.conditions
    selected_file_types_property = next(
        (
            prop
            for prop in root_data_entity["additionalProperty"]
            if prop["name"] == "selected_file_types"
        ),
        None,
    )
    if not selected_file_types_property:
        raise ValueError(
            "RO-Crate structure is missing the 'selected_file_types' additional property"
        )
    selected_file_types_property["value"] = bulk_download.filter
    data_directory_entity = next(
        (item for item in rocrate_dict["@graph"] if item["@id"] == "data/"), None
    )
    data_directory_entity["description"] = (
        f"Directory containing the {len(bulk_download.files)} data files for this bulk download. The file names are generated using the file's corresponding `DataObject` ID and `DataObject` name, where ':' (colons) in the IDs are replaced with '_' (underscore) for file system safety. Each file is prefixed by its sanitized `DataObject` ID, followed by '__' (double underscore), followed by its sanitized `DataObject` name."
    )
    return rocrate_dict
