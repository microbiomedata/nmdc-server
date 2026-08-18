# NMDC Data Products

Thank you for downloading data products from the NMDC Data Portal!

The following document explains the structure of the archive you have downloaded.

## Data Product Files

The data files can be found in the `data/` folder after unzipping your archive. Each data product file is considered a `DataObject`, as defined in the [NMDC Schema Documentation](https://microbiomedata.github.io/nmdc-schema/DataObject/). The file names are generated using the file's corresponding `DataObject` ID and `DataObject` name, where ':' (colons) in the IDs are replaced with '_' (underscore) for file system safety. Each file is prefixed by its sanitized `DataObject` ID, followed by '__' (double underscore), followed by its sanitized `DataObject` name.

For example: `nmdc_dobj-11-wyam2520__nmdc_wfrqc-11-k1c92g17.1_filterStats.txt`

Note that some `DataObject` names include references to other related NMDC identifiers, but this is not an enforced standard.

## RO-Crate Metadata Document

Included at the top level of every download is a file called `ro-crate-metadata.json`. This is a machine-readable document that describes the contents of this archive. To learn more about RO-Crate, check out the [RO-Crate specification docs](https://www.researchobject.org/ro-crate/specification/1.2/introduction.html).

## Metadata Folder

At the top level of the download is a folder called `metadata/`. It contains `data_objects.json`, which helps you understand how each data product file was generated and how to relate it back to `Biosample`s.

### `data_objects.json`

This file includes a list of JSON objects where each object represents a `DataObject`. In NMDC terms, a `DataObject` is defined as:

> An object that primarily consists of symbols that represent information. Files, records, and omics data are examples of data objects.

Each data product file included in your download has an associated `DataObject` ID (e.g. `nmdc:dobj-11-zvr19844`). The `_bulk_download_path` field contains its complete path from the root of this archive, including the `data/` directory. The `_related_biosample_ids` field lists the IDs of the `Biosample`s associated with that data object.
