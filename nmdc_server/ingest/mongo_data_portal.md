# MongoDB-based Data Portal

There are now API endpoints and UI changes to support retrieving data directly from MongoDB, eliminating the need to ingest into Postgres.
This new experimental mode requires additional denormalized collections in MongoDB for efficient search.
Note that this does not alleviate the dependency on Postgres, which is still used for the following:
* User login
* Download counts
* Submission portal submissions

This is implemented as a feature flag that can be changed at runtime to compare Postgres-based and MongoDB-based search and UI.

The following are still required for feature parity with the existing data portal:
- [x] Study detail page
- [ ] Biosample detail page
  - [x] Initial page
  - [ ] Add Depth
  - [ ] Add Lat/long
  - [ ] Add Envo terms
  - [ ] Add study ID
  - [ ] Add collection date
  - [ ] Add open in Gold
  - [ ] Add more alternate identifiers
  - [ ] Remove type
  - [ ] Remove community
  - [ ] Remove habitat
  - [ ] Remove NCBI taxonomy
  - [ ] Remove sample collection site
  - [ ] Remove samp name
  - [ ] Remove location
  - [ ] Remove multiomics count
- [x] Sankey
- [ ] Dynamic ENVO term trees in field flyout
- [ ] Make `envo.py` not rely on postgres Biosample table
- [ ] Autocomplete search
- [ ] Associating omics processing through analytic samples (borrow ingest code)
- [ ] Associating `M` and `MAP` terms in KEGG search
- [ ] Robust performance comparison
- [ ] Show studies with no samples
- [ ] Fix names in UI to not include `has_raw_value`
- [ ] Fix permalink serialization
- [ ] Upgrade to latest data
- [ ] Merge in recent changes
- [ ] Cache Mongo connection

# Denormalized MongoDB

To run denormalization, execute:

```
python denormalize.py
```

This will create the following new Mongo collections to support faceted search in the data portal:

## `study_tranformed`
This collection is required to efficiently summarize a study. Its documents are available in the `biosample_denormalized` and `omics_processing_denormalized` collections, and it is used in the following endpoints:
* `/mongo_study/{study_id}` (used on study details page)

This collection is identical to the `study_set` collection with the following additional fields:
* `omics_processing_counts`: An array of objects with `type` and `count` fields for each omics processing associated with samples in the study, e.g. `[{"type": "Metabolomics", "count": 50}, {"type": "Metagenome", "count": 100}, ...]`
* `sample_count`: The number of biosamples associated with the study

## `biosample_tranformed`
This collection is required to efficiently query biosamples. Its documents are available in the `biosample_denormalized` and `omics_processing_denormalized` collections.

This collection is identical to the `biosample_set` collection with the following additional fields:
* `collection_date.has_date_value`: The value of the collection date converted to a `Date` object for binning and search
* `multiomics`: An array of strings containing the types of `omics_processing` objects associated with the biosample (e.g. `["Metagenomics", "Proteomics"]`)
* `multiomics_count`: The length of the `multiomics` field, so that biosamples can be sorted in "more-omics-types-first" order

## `biosample_denormalized`

This collection is required to efficiently lookup sample object and counts without costly mongodb joins (i.e. `$lookup` aggregations). It is used in the following endpoints:
* `/environment/mongo_geospatial`
* `/biosample/mongo_search`
* `/biosample/mongo_facet`
* `/biosample/mongo_binned_facet`
* `/study/mongo_search`
* `/study/mongo_facet`
* `/data_object/mongo_workflow_summary`

This collection is identical to the `biosample_transformed` collection with the following additional fields:
* `study`: The study records from `study_set` whose `id` matches the biosample `part_of`
* `omics_processing`: An array of omics processing records from `omics_processing_set` whose `has_input` matches the biosample `id`
* `analysis`: An array of analysis records from the following collections whose `was_informed_by` field matches the `id`  of one of the `omics_processing` records associated with this biosample
  * `mags_activity_set`
  * `metabolomics_analysis_activity_set`
  * `metagenome_annotation_activity_set`
  * `metagenome_assembly_set`
  * `metaproteomics_analysis_activity_set`
  * `metatranscriptome_activity_set`
  * `nom_analysis_activity_set`
* `data_object`: An array of data object records whose `id` matches the `has_output` field of one of the `analysis` records associated with this biosample
* `gene_function`: An array of gene function records from `functional_annotation_agg` or `metap_gene_function_aggregation` whose `metagenome_annotation_id` or `metaproteomic_analysis_id` field matches the `id` of one of the `analysis` records associated with this biosample

## `omics_processing_denormalized`

This collection is required to efficiently lookup omics processing counts without costly mongodb joins (i.e. `$lookup` aggregations). It is used in the following endpoints:
* `/omics_processing/mongo_facet`

This collection is identical to the `omics_processing_set` collection with the following additional fields:
* `biosample`: The biosample records from `biosample_transformed` whose `id` matches the `has_input` field of this omics processing
* `study`: The study records from `study_set` whose `id` matches the `part_of` field of the `biosample` record associated with this omics processing
* `analysis`: An array of analysis records from the analysis collections (see `biosample_denormalized` above) whose `was_informed_by` field matches the `id` of this omics processing
* `data_object`: Derived similarly to `biosample_denormalized` above
* `gene_function`: Derived similarly to `biosample_denormalized` above
