# NMDC Data Products

Thank you for downloading data products from the NMDC Data Portal!

The following document explains the structure of the archive you have downloaded.

## Data Product Files

The data files can be found in the `data/` folder after unzipping your archive. Each data product file is considered a `DataObject`, as defined in the [NMDC Schema Documentation](https://microbiomedata.github.io/nmdc-schema/DataObject/). The files themselves are split up and nested by `DataGeneration` and `WorkflowExecution`. The `DataGeneration` and `WorkflowExecution` folders are named using a sanitized version of their respective ID, where colons (`:`) are replaced with underscores (`_`). For example, the path to one of the downloaded files in this archive might be:

```
data/nmdc_omprc-11-uniqueid/nmdc_wfmag-11-uniqueid.1/data-product-file.csv
```

In rare cases a `DataIbject` file was generated directly by a `DataGeneration` and does not have a corresponding `WorkflowExecution`. In these cases, the file is nested directly in the `DataGeneration` folder:

```
data/nmdc_dgms-11-uniqueid/raw-data.csv
```

Note that some `DataObject` file names include references to other related NMDC identifiers, but this is not an enforced standard.

## RO-Crate Metadata Document

Included at the top level of every download is a file called `ro-crate-metadata.json`. This is a machine-readable document that describes the contents of this archive as well its relevant relationships as it relates to the data's provenance. To learn more about RO-Crate, check out the [RO-Crate specification docs](https://www.researchobject.org/ro-crate/specification/1.2/introduction.html).

The RO-Crate `@graph` array contains nodes for every folder in the zip, every metadata file, and every associated NMDC `Biosample`, `Study`, `DataGeneration`, and `WorkflowExecution`. The RO-Crate intentionally only contains nodes down to the `WorkflowExecution` level to minimize the size of the JSON file. The full `DataObject` metadata is included in `metadata/data_objects.json` (explained in the next section).

## Metadata Folder

At the top level of the download is a folder called `metadata/`. It contains `data_objects.json`, which helps you understand how each data product file was generated and how to relate it back to `Biosample`s.

### `data_objects.json`

This file includes a list of JSON objects where each object represents a `DataObject`. In NMDC terms, a `DataObject` is defined as:

> An object that primarily consists of symbols that represent information. Files, records, and omics data are examples of data objects.

Each data product file included in your download has an associated `DataObject` ID (e.g. `nmdc:dobj-11-zvr19844`). The `_bulk_download_path` field contains its complete path from the root of this archive, including the `data/` folder. The `_related_biosample_ids` field lists the IDs of the `Biosample`s associated with that data object. The `_globus_path` field contains the complete path to the `DataObject` file in the NMDC [Globus](https://www.globus.org/) collection.
