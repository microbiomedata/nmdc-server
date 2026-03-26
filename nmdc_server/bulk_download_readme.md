# NMDC Data Products

Thank you for downloading data products from the NMDC Data Portal!

The following document explains the structure of the archive you have downloaded.

## Data Product Files

Each file you have downloaded is nested inside of a series of folders that organize the files by their associated counterparts. The hierarchy uses the following structure:

- `Study`
  - `Biosample`
    - `DataGeneration`
      - Data Product File

The name of each folder is a sanitized version of the object's ID (`:` replaced by `_`). For example:

- `nmdc_sty-11-8ws97026`
  - `nmdc_bsm-11-127y7152`
    - `nmdc_dgms-11-5fd4qm69`
      - `nmdc_dobj-11-dhdvdf46_kaiko_QC_metrics.tsv`

## Metadata

At the top level of the download is a folder called `metadata`. This includes two JSON files that are intended to help you understand more about how each data product file was generated and how to relate them back to `Biosample`s.

### `data_objects.json`

This file includes a list of JSON objects where each object represents a `DataObject`. In NMDC terms, a `DataObject` is defined as:

> An object that primarily consists of symbols that represent information. Files, records, and omics data are examples of data objects.

Each data product file included in your download has an associated `DataObject` ID (e.g. `nmdc:dobj-11-zvr19844`). You can tell which file the ID relates to by looking at the `name` field. The `name` value is equal to the name of the data product file (e.g. `nmdc_dobj-11-xmvv4977_nmdc_dobj-11-f6nr5w60_QC_metrics.tsv`).

### `related_biosamples.json`

This file includes a single object whose keys are each of the `DataObject` IDs included in your download. For each `DataObject` ID, there is a list of `Biosample` IDs that are associated with that `DataObject`. This can help you relate your data products back to concrete `Biosample`s.